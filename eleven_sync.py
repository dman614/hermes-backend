"""
Hermes - ElevenLabs conversation sync.

After a call handled by ElevenLabs' Twilio integration, the transcript lives
only on their servers. This module fetches completed conversations, runs the
Claude extraction pipeline to build a job, saves it to the central DB, and
notifies the owner by SMS - deduplicated via unique job_ref (conv_<id>).
"""

import json
import logging
import os
import urllib.request
from datetime import datetime

from db import db
from sms import send_sms

log = logging.getLogger("hermes.sync")

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVEN_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "")
OWNER_PHONE = os.getenv("OWNER_PHONE", "+12507921488")  # Dale's mobile


def _convai_get(path: str) -> dict:
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/convai/{path}",
        headers={"xi-api-key": ELEVEN_API_KEY, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def list_done_conversations(limit: int = 10) -> list:
    """Most recent conversations for the agent."""
    try:
        data = _convai_get(f"conversations?agent_id={ELEVEN_AGENT_ID}&limit={limit}")
        return data.get("conversations", [])
    except Exception as exc:
        log.error("list conversations failed: %s", exc)
        return []


def fetch_transcript(conversation_id: str) -> dict:
    """Full conversation: transcript lines + metadata."""
    try:
        return _convai_get(f"conversations/{conversation_id}")
    except Exception as exc:
        log.error("fetch conversation %s failed: %s", conversation_id, exc)
        return {}


def transcript_to_text(data: dict) -> str:
    """Build a clean transcript string for the extraction pipeline."""
    lines = []
    for t in data.get("transcript", []):
        role = t.get("role", "")
        msg = t.get("message", "") or ""
        if msg:
            speaker = "Caller" if role == "user" else "Eric"
            lines.append(f"{speaker}: {msg}")
    return "\n".join(lines)


def sync_new_conversations() -> dict:
    """Fetch done conversations and convert unseen ones into jobs.

    Returns counts for reporting. Safe to run repeatedly - job_ref is the
    conversation id, unique in the jobs table, so reruns are no-ops.
    """
    imported = 0
    skipped = 0
    errors = 0
    notified = []

    for conv in list_done_conversations(limit=10):
        conv_id = conv.get("conversation_id")
        if not conv_id:
            continue
        status = conv.get("status", "")
        if status not in ("done", "completed"):
            continue

        # dedupe: already imported?
        job_ref = conv_id if conv_id.startswith("conv_") else f"conv_{conv_id}"
        existing = db.list_jobs(limit=500)
        if any(j.get("job_ref") == job_ref for j in existing):
            skipped += 1
            continue

        # skip abandoned / test calls with no real caller speech
        if (conv.get("user_message_count") or 0) < 1:
            skipped += 1
            continue

        data = fetch_transcript(conv_id)
        text = transcript_to_text(data)
        if not text:
            skipped += 1
            continue

        try:
            from main import CallMetadata, lead_agent
            meta = CallMetadata(
                call_sid=conv_id,
                from_phone=conv.get("metadata", {}).get("caller_number") or "phone",
                to_phone="+17789094293",
                call_status="completed",
                timestamp=datetime.now().isoformat(),
            )
            resp = lead_agent.process_transcript(text, meta)

            job = db.create_job({
                "job_ref": job_ref,
                "customer_name": resp.job_details.customer_name,
                "customer_phone": resp.job_details.customer_phone,
                "customer_address": resp.job_details.address,
                "service_type": resp.job_details.service_type,
                "urgency": resp.job_details.urgency,
                "problem_description": resp.job_details.problem_description,
                "status": "incoming",
                "source": "elevenlabs_voice",
            })
            imported += 1

            # Owner SMS: new lead notification
            sms = send_sms(OWNER_PHONE, (
                f"New lead ({resp.job_details.service_type}) from "
                f"{resp.job_details.customer_name}: {resp.job_details.problem_description[:80]}"
                f" - {resp.job_details.address} [{resp.job_details.urgency}]"))
            notified.append({"job_id": job.get("id"), "sms": sms})

        except Exception as exc:
            log.error("import conversation %s failed: %s", conv_id, exc)
            errors += 1

    return {"imported": imported, "skipped": skipped, "errors": errors,
            "notified": notified}
