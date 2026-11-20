"""
Hermes - Live voice bridge (Twilio MediaStreams <-> ElevenLabs Conversational AI).

Call flow:
  caller -> Twilio opens WS to /ws/live-call
  bridge opens WS to ElevenLabs (ulaw 8kHz both directions)
  caller audio (base64 ulaw)  -> ElevenLabs
  ElevenLabs audio (base64)   -> Twilio, played to caller
  on conversation end: fetch transcript from ElevenLabs, parse the JSON
  'conversation result' payload, and return it to the HTTP layer so the
  lead can be persisted via the existing Claude extraction pipeline.
"""

import asyncio
import base64
import json
import logging
import os

import websockets

log = logging.getLogger("hermes.bridge")

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVEN_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "")

ELEVEN_WS_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ELEVEN_AGENT_ID}"

# Called with the conversation result dict when a call ends.
on_conversation_end = None


def register_end_callback(fn):
    """HTTP layer registers a callback: fn(conversation_result: dict)."""
    global on_conversation_end
    on_conversation_end = fn


async def handle_twilio_stream(ws_twilio):
    """One Twilio media-stream connection. Returns the conversation result."""
    stream_sid = None
    conversation_id = None
    ws_eleven = None
    transcript_parts = []
    eleven_results = {}
    stop = asyncio.Event()

    async def eleven_to_twilio():
        """Forward ElevenLabs audio + transcript messages back into the call."""
        nonlocal conversation_id
        try:
            async for raw in ws_eleven:
                msg = json.loads(raw)
                mtype = msg.get("type")
                if mtype == "conversation_initiation_metadata":
                    conversation_id = msg.get("conversation_id")
                    log.info("ElevenLabs conversation started: %s", conversation_id)
                elif mtype == "audio":
                    payload = msg.get("audio", {}).get("chunk")
                    if payload and stream_sid:
                        frame = json.dumps({
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": payload},
                        })
                        await ws_twilio.send(frame)
                elif mtype in ("user_transcript", "agent_response"):
                    text = msg.get("text", "")
                    if text:
                        transcript_parts.append(f"{'Caller' if mtype == 'user_transcript' else 'Eric'}: {text}")
                elif mtype == "client_tool_call":
                    # ElevenLabs asks us to run a tool (none defined yet) - clear it.
                    await ws_eleven.send(json.dumps({
                        "type": "client_tool_call_result",
                        "request_id": msg.get("request_id"),
                        "result": json.dumps({"status": "ok", "data": None}),
                        "is_error": False,
                    }))
                elif mtype == "conversation_initiation_completed":
                    # ready to receive audio
                    pass
                elif mtype == "ping":
                    await ws_eleven.send(json.dumps({"type": "pong", "ping": msg.get("ping")}))
                elif mtype == "interruption":
                    # caller talked over Eric - forward silence/hangup semantics no-op
                    pass
                elif mtype == "final_response":
                    log.info("Final response from ElevenLabs")
                elif mtype == "conversation_completed" or mtype == "close":
                    # capture any trailing metadata
                    for key in ("transcript", "status", "ended_reason", "metadata"):
                        if key in msg:
                            eleven_results[key] = msg[key]
                    break
                elif mtype == "error":
                    log.error("ElevenLabs error: %s", msg)
                    break
        except Exception as exc:
            log.warning("Eleven->Twilio leg ended: %s", exc)
        finally:
            stop.set()

    # Open the ElevenLabs conversation
    try:
        ws_eleven = await websockets.connect(
            ELEVEN_WS_URL,
            additional_headers={"xi-api-key": ELEVEN_API_KEY},
            max_size=10 * 1024 * 1024,
        )
    except Exception as exc:
        log.error("Cannot open ElevenLabs WS: %s", exc)
        await ws_twilio.close()
        return {}

    if ws_eleven is None:
        await ws_twilio.close()
        return {}

    eleven_task = asyncio.create_task(eleven_to_twilio())

    try:
        async for raw in ws_twilio:
            data = json.loads(raw)
            ev = data.get("event")
            if ev == "connected":
                continue
            elif ev == "start":
                stream_sid = data.get("streamSid")
                log.info("Twilio stream started: %s", stream_sid)
                # send an audio_input to prime the agent
                await ws_eleven.send(json.dumps({
                    "type": "audio_input",
                    "audio": {"data": base64.b64encode(b"\x7f" * 640).decode()},
                }))
            elif ev == "media":
                payload = data.get("media", {}).get("payload", "")
                if payload and not stop.is_set():
                    await ws_eleven.send(json.dumps({
                        "type": "audio_input",
                        "audio": {"data": payload},
                    }))
            elif ev == "stop":
                log.info("Twilio stream stopped (call over)")
                break
    except Exception as exc:
        log.warning("Twilio->Eleven leg ended: %s", exc)
    finally:
        stop.set()

    # Wrap up the ElevenLabs side
    try:
        if ws_eleven:
            try:
                await ws_eleven.send(json.dumps({
                    "type": "client_tool_call_result",
                    "request_id": "end",
                    "result": json.dumps({"status": "end_conversation"}),
                    "is_error": False,
                }))
            except Exception:
                pass
            try:
                await asyncio.wait_for(ws_eleven.close(), timeout=3)
            except Exception:
                pass
    except Exception:
        pass
    await asyncio.wait_for(eleven_task, timeout=5)

    # Fetch the full conversation (transcript) from ElevenLabs API
    result = {}
    if conversation_id:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}",
                headers={"xi-api-key": ELEVEN_API_KEY, "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
        except Exception as exc:
            log.error("Failed fetching conversation %s: %s", conversation_id, exc)

    result.setdefault("transcript_text", "\n".join(transcript_parts))
    result.setdefault("_stream_transcript", transcript_parts)

    if on_conversation_end:
        try:
            on_conversation_end(result)
        except Exception as exc:
            log.error("End callback failed: %s", exc)
    return result
