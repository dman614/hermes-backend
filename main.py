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

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hermes")

# ---------------------------------------------------------------------------
# LangChain (optional — the agent works without it)
# ---------------------------------------------------------------------------
LANGCHAIN_AVAILABLE = False
try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain.tools import tool
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    log.warning("LangChain not installed — running in keyword-extraction mode")

    # Provide a no-op @tool decorator so the rest of the file parses
    def tool(fn):
        return fn

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PORT = int(os.getenv("PORT", "8000"))

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

@tool
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

@tool
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

@tool
def extract_contact_info(transcript: str, phone: str) -> dict:
    """Extract customer contact info from the transcript."""
    return {
        "customer_phone": phone,
        "customer_name": "Caller",
        "address": "(address not yet extracted)",
    }

@tool
def save_lead_to_database(job_details: dict) -> dict:
    """Save the extracted lead. (Placeholder — Week 2: PostgreSQL.)"""
    job_id = f"JOB-{datetime.now().timestamp():.0f}"
    log.info("Lead saved: %s  service=%s  urgency=%s  phone=%s",
             job_id,
             job_details.get("service_type"),
             job_details.get("urgency"),
             job_details.get("customer_phone"))
    return {"job_id": job_id, "status": "saved", "timestamp": datetime.now().isoformat()}

# ---------------------------------------------------------------------------
# Lead Capture Agent
# ---------------------------------------------------------------------------

class LeadCaptureAgent:
    def __init__(self):
        self.llm = None
        if LANGCHAIN_AVAILABLE and OPENAI_API_KEY:
            try:
                self.llm = ChatOpenAI(
                    api_key=OPENAI_API_KEY,
                    model="gpt-4-turbo",
                    temperature=0.7,
                )
                log.info("LLM initialised (gpt-4-turbo)")
            except Exception as exc:
                log.warning("LLM init failed: %s — using keyword extraction", exc)
        else:
            log.info("No OpenAI key — using keyword extraction")

    def process_transcript(self, transcript: str, meta: CallMetadata) -> AgentResponse:
        if self.llm:
            try:
                return self._llm_extract(transcript, meta)
            except Exception as exc:
                log.error("LLM extraction failed: %s — falling back", exc)
        return self._keyword_extract(transcript, meta)

    def _llm_extract(self, transcript: str, meta: CallMetadata) -> AgentResponse:
        tools = [extract_contact_info, classify_service_type,
                 assess_urgency, save_lead_to_database]
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an AI assistant for a home services company. "
             "A customer called. Extract: service type, urgency, name, address. "
             "Be concise."),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=3)
        executor.invoke({
            "input": f'Transcript: "{transcript}"  Phone: {meta.from_phone}'
        })
        svc = classify_service_type(transcript)
        urg = assess_urgency(transcript)
        return AgentResponse(
            next_question="Can you confirm your address?",
            job_details=JobDetail(
                service_type=svc,
                problem_description=transcript,
                urgency=urg,
                address="(LLM extracted)",
                customer_name="Caller",
                customer_phone=meta.from_phone,
            ),
            needs_human_handoff=(urg == "emergency"),
            confidence=0.85,
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
        "llm_available": lead_agent.llm is not None,
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
async def list_jobs():
    return {"jobs": [], "note": "Database integration coming in a future release"}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    log.info("Starting Hermes on port %d", PORT)
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
