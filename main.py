"""
Hermes - Home Services Lead Capture Agent
FastAPI + LangChain + Twilio

Answers incoming calls, records the caller's message,
extracts service type / urgency / contact info, and logs the lead.
Falls back to keyword-based extraction when no OpenAI key is set.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

from db import db
from quote_agent import generate_quote, set_quote_status

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hermes")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PORT = int(os.getenv("PORT", "8000"))

# ---------------------------------------------------------------------------
# LLM (optional — the agent works without it; Anthropic or OpenAI)
# ---------------------------------------------------------------------------
LLM_AVAILABLE = False
client = None

if ANTHROPIC_API_KEY:
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        LLM_AVAILABLE = True
        log.info("LLM: Anthropic client ready")
    except ImportError:
        log.warning("anthropic SDK not installed — checking OpenAI")
    except Exception as exc:
        log.warning("Anthropic init failed: %s — checking OpenAI", exc)

if not LLM_AVAILABLE and OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        LLM_AVAILABLE = True
        log.info("LLM: OpenAI client ready")
    except ImportError:
        log.warning("OpenAI SDK not installed — running in keyword mode")
    except Exception as exc:
        log.warning("OpenAI init failed: %s — running in keyword mode", exc)

if not LLM_AVAILABLE:
    log.info("No LLM key — running in keyword-extraction mode")

# Base URL for this server (used in TwiML action URLs)
BASE_URL = os.getenv("BASE_URL", "")  # e.g. https://hermes-backend-8j16.onrender.com

app = FastAPI(
    title="Hermes Lead Capture Agent",
    description="AI agent that answers phone calls and captures job details",
    version="0.2.0",
)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class CallMetadata(BaseModel):
    call_sid: str
    from_phone: str
    to_phone: str
    call_status: str
    timestamp: str = ""

class JobDetail(BaseModel):
    service_type: str
    problem_description: str
    urgency: str
    address: str
    customer_name: Optional[str] = None
    customer_phone: str

class AgentResponse(BaseModel):
    next_question: str
    job_details: JobDetail
    needs_human_handoff: bool
    confidence: float

# ---------------------------------------------------------------------------
# Extraction helpers (used by both LLM and keyword paths)
# ---------------------------------------------------------------------------

def classify_service_type(transcript: str) -> str:
    """Classify the service needed from the caller's words."""
    t = transcript.lower()
    if any(w in t for w in ("leak", "toilet", "pipe", "plumb", "drain", "water", "faucet")):
        return "plumbing"
    if any(w in t for w in ("heat", "air", "furnace", "hvac", "cool", "ac ", "a/c")):
        return "hvac"
    if any(w in t for w in ("wire", "electr", "outlet", "breaker", "panel", "light")):
        return "electrical"
    return "unknown"

def assess_urgency(transcript: str) -> str:
    """Assess if this is an emergency, routine, or scheduling request."""
    t = transcript.lower()
    if any(w in t for w in ("emergency", "urgent", "right now", "immediately",
                             "overflowing", "flooding", "broken", "down", "no heat",
                             "no water", "gas smell", "sparking")):
        return "emergency"
    if any(w in t for w in ("schedule", "appointment", "next week", "available")):
        return "scheduling"
    return "routine"

def extract_contact_info(transcript: str, phone: str) -> dict:
    """Extract customer contact info from the transcript."""
    return {
        "customer_phone": phone,
        "customer_name": "Caller",
        "address": "(address not yet extracted)",
    }

def save_lead_to_database(job_details: dict) -> dict:
    """Save the extracted lead to PostgreSQL (the central jobs table)."""
    job = db.create_job({
        "job_ref": f"JOB-{int(datetime.now().timestamp())}",
        "customer_name": job_details.get("customer_name"),
        "customer_phone": job_details.get("customer_phone"),
        "customer_address": job_details.get("address"),
        "service_type": job_details.get("service_type"),
        "urgency": job_details.get("urgency"),
        "problem_description": job_details.get("problem_description"),
        "status": "incoming",
        "source": "phone",
    })
    return {"job_id": job.get("id"), "job_ref": job.get("job_ref"),
            "status": job.get("status", "saved"),
            "timestamp": datetime.now().isoformat()}

# ---------------------------------------------------------------------------
# Lead Capture Agent
# ---------------------------------------------------------------------------

def _parse_json_response(raw: str) -> dict:
    """Parse an LLM JSON response, tolerating markdown fences, prose, and
    leading/trailing junk that some models emit around the JSON block."""
    if not raw:
        return {}
    text = raw.strip()
    # Strip ```json ... ``` fences
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # Find the first { ... } block if surrounding prose exists
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        log.warning("LLM returned non-JSON response: %r", raw[:200])
        return {}

class LeadCaptureAgent:
    def __init__(self):
        self.client = client  # shared: Anthropic or OpenAI, or None
        if self.client:
            log.info("LLM extraction enabled")

    def process_transcript(self, transcript: str, meta: CallMetadata) -> AgentResponse:
        if self.client:
            try:
                return self._llm_extract(transcript, meta)
            except Exception as exc:
                log.error("LLM extraction failed: %s — falling back", exc)
        return self._keyword_extract(transcript, meta)

    def _llm_extract(self, transcript: str, meta: CallMetadata) -> AgentResponse:
        system_prompt = (
            "You extract job details from a home-services customer call transcript. "
            "Return ONLY JSON with keys: service_type (plumbing|hvac|electrical|unknown), "
            "urgency (emergency|routine|scheduling), customer_name (string or null), "
            "address (string or null), problem_description (short summary). "
            'Example: {"service_type": "plumbing", "urgency": "emergency", '
            '"customer_name": "Sarah Chen", "address": "482 Maple Ave", '
            '"problem_description": "Kitchen sink leaking, water on floor"}'
        )
        user_content = f'Transcript: "{transcript}"'

        if ANTHROPIC_API_KEY:
            resp = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=300,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            raw = (resp.content[0].text
                   if resp.content and getattr(resp.content[0], "text", None)
                   else "{}")
        else:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=300,
            )
            raw = resp.choices[0].message.content or "{}"
        data = _parse_json_response(raw)

        svc = data.get("service_type") or classify_service_type(transcript)
        urg = data.get("urgency") or assess_urgency(transcript)
        if svc not in ("plumbing", "hvac", "electrical", "unknown"):
            svc = classify_service_type(transcript)
        if urg not in ("emergency", "routine", "scheduling"):
            urg = assess_urgency(transcript)
        name = data.get("customer_name") or "Caller"
        addr = data.get("address") or "(ask caller to confirm)"
        problem = data.get("problem_description") or transcript

        save_lead_to_database({
            "service_type": svc,
            "urgency": urg,
            "customer_phone": meta.from_phone,
            "customer_name": name,
            "address": addr,
            "problem_description": problem,
        })
        return AgentResponse(
            next_question="Can you confirm your address?",
            job_details=JobDetail(
                service_type=svc,
                problem_description=problem,
                urgency=urg,
                address=addr,
                customer_name=name,
                customer_phone=meta.from_phone,
            ),
            needs_human_handoff=(urg == "emergency"),
            confidence=0.92,
        )

    def _keyword_extract(self, transcript: str, meta: CallMetadata) -> AgentResponse:
        svc = classify_service_type(transcript)
        urg = assess_urgency(transcript)
        save_lead_to_database({
            "service_type": svc,
            "urgency": urg,
            "customer_phone": meta.from_phone,
        })
        return AgentResponse(
            next_question="Can you confirm your address?",
            job_details=JobDetail(
                service_type=svc,
                problem_description=transcript,
                urgency=urg,
                address="(ask caller to confirm)",
                customer_name="Caller",
                customer_phone=meta.from_phone,
            ),
            needs_human_handoff=(urg == "emergency"),
            confidence=0.70,
        )

lead_agent = LeadCaptureAgent()

# Initialise the database schema at startup (no-op if DATABASE_URL unset)
db.init_schema()

# ---------------------------------------------------------------------------
# Twilio webhook endpoints
# ---------------------------------------------------------------------------

def _recording_action_url() -> str:
    """Absolute URL for the <Record action=...> callback."""
    if BASE_URL:
        return f"{BASE_URL.rstrip('/')}/webhook/call/recording"
    return "/webhook/call/recording"


@app.post("/webhook/call")
@app.post("/api/calls/incoming")
async def handle_incoming_call(request: Request):
    """
    Twilio webhook: a customer is calling.
    Respond with TwiML that greets and records.
    """
    try:
        form_data = await request.form()
        from_phone = form_data.get("From", "unknown")
        to_phone = form_data.get("To", "unknown")
        log.info("Incoming call: %s -> %s", from_phone, to_phone)
    except Exception:
        pass

    action = _recording_action_url()
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hi! Thanks for calling Comox Valley Home Services.
         Please tell us what you need — plumbing, H-V-A-C, or electrical —
         and describe the problem after the beep.</Say>
    <Record maxLength="120" action="{action}" method="POST"
            transcribe="true" transcribeCallback="{action}" />
    <Say voice="alice">We did not receive a recording. Goodbye.</Say>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.post("/webhook/call/recording")
@app.post("/api/calls/recording")
async def handle_recording(request: Request):
    """
    Twilio callback after the caller's recording finishes.
    Process the transcript and respond.
    """
    try:
        form_data = await request.form()
        call_sid = str(form_data.get("CallSid", ""))
        from_phone = str(form_data.get("From", "unknown"))
        to_phone = str(form_data.get("To", "unknown"))

        # Twilio sends TranscriptionText when transcription is ready,
        # or we fall back to a placeholder until real STT is wired.
        transcript = str(form_data.get("TranscriptionText")
                         or form_data.get("SpeechResult")
                         or "(no transcript received)")

        log.info("Recording from %s — transcript: %s", from_phone, transcript)

        meta = CallMetadata(
            call_sid=call_sid,
            from_phone=from_phone,
            to_phone=to_phone,
            call_status="recording_received",
            timestamp=datetime.now().isoformat(),
        )
        result = lead_agent.process_transcript(transcript, meta)

        log.info("Extracted: service=%s  urgency=%s  confidence=%.2f",
                 result.job_details.service_type,
                 result.job_details.urgency,
                 result.confidence)

        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thanks for that information!
         A technician will call you back within 30 minutes. Goodbye!</Say>
    <Hangup />
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    except Exception as exc:
        log.error("Error processing recording: %s", exc)
        return Response(
            content="""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, there was an error. Please try again later.</Say>
    <Hangup />
</Response>""",
            media_type="application/xml",
        )

# ---------------------------------------------------------------------------
# Health / test / utility endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Hermes is running!", "version": "0.2.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "Hermes Lead Capture Agent",
        "llm_available": lead_agent.client is not None,
        "timestamp": datetime.now().isoformat(),
    }

@app.post("/api/test/transcript")
async def test_transcript(request: Request):
    """
    Test the extraction pipeline without Twilio.

    curl -X POST .../api/test/transcript \\
         -H "Content-Type: application/json" \\
         -d '{"transcript": "Emergency plumbing at 123 Main St", "phone": "+1-250-555-1234"}'
    """
    body = await request.json()
    transcript = body.get("transcript", "")
    phone = body.get("phone", "+1-250-555-0000")

    meta = CallMetadata(
        call_sid="TEST",
        from_phone=phone,
        to_phone="+1-250-555-PLUMB",
        call_status="test",
        timestamp=datetime.now().isoformat(),
    )
    resp = lead_agent.process_transcript(transcript, meta)
    return {
        "success": True,
        "transcript": transcript,
        "extracted": {
            "service_type": resp.job_details.service_type,
            "urgency": resp.job_details.urgency,
            "address": resp.job_details.address,
            "customer_phone": resp.job_details.customer_phone,
        },
        "confidence": resp.confidence,
        "needs_human_handoff": resp.needs_human_handoff,
        "next_question": resp.next_question,
    }

@app.get("/api/jobs")
async def list_jobs(status: str = "", limit: int = 50):
    """List captured leads/jobs from PostgreSQL."""
    jobs = db.list_jobs(limit=limit, status=status)
    return {"jobs": jobs, "count": len(jobs), "database": db.available}

@app.post("/api/jobs/{job_id}/quotes")
async def create_quote(job_id: int, parts_cost: float = 0):
    """Quote Generation Agent: build a quote for a captured job."""
    try:
        quote = generate_quote(job_id, parts_cost=parts_cost)
        return {"success": True, "quote": quote}
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

@app.get("/api/jobs/{job_id}/quotes")
async def get_quotes(job_id: int):
    """List quotes for a job."""
    quotes = db.get_quotes_for_job(job_id)
    return {"job_id": job_id, "quotes": quotes, "count": len(quotes)}

@app.post("/api/quotes/{quote_id}/status")
async def update_quote(quote_id: int, status: str):
    """Owner approval: set draft -> approved -> sent, or rejected."""
    try:
        result = set_quote_status(quote_id, status)
        return {"success": True, **result}
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    log.info("Starting Hermes on port %d", PORT)
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
