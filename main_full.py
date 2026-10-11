"""
Home Services Lead Capture Agent - Week 1 MVP
FastAPI + LangChain + Twilio

This is the PRODUCTION skeleton you'll run and iterate on.
"""

import os
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

# AI/LLM
try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain.tools import tool
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
except ImportError:
    print("⚠️ LangChain not installed yet. Run: pip install langchain langchain-openai")

# Database (we'll add this in Week 2)
# from sqlalchemy import create_engine
# from database import SessionLocal, Job

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Home Services Lead Capture Agent",
    description="AI agent that answers phone calls and captures job details",
    version="0.1.0"
)

# ============================================================================
# CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-test-placeholder")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC-test-placeholder")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "test-placeholder")

# Database URL (we'll use this in Week 2)
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/hermes")

# ============================================================================
# PYDANTIC MODELS (Data Structures)
# ============================================================================

class CallMetadata(BaseModel):
    """Metadata from Twilio webhook"""
    call_sid: str
    from_phone: str
    to_phone: str
    call_status: str
    timestamp: str = ""

class JobDetail(BaseModel):
    """Job information extracted by agent"""
    service_type: str  # "plumbing", "hvac", "electrical"
    problem_description: str
    urgency: str  # "emergency", "routine", "scheduling"
    address: str
    customer_name: Optional[str] = None
    customer_phone: str

class AgentResponse(BaseModel):
    """Agent's response to transcription"""
    next_question: str
    job_details: JobDetail
    needs_human_handoff: bool
    confidence: float

# ============================================================================
# LANGCHAIN TOOLS (What the agent can do)
# ============================================================================

@tool
def extract_contact_info(transcript: str, phone: str) -> dict:
    """
    Extract customer contact info from transcript.
    
    Args:
        transcript: What the customer said
        phone: Customer's phone number (from Twilio)
    
    Returns:
        Extracted info: name, address, phone
    """
    # In Week 1, we'll simulate. In production, use LLM.
    return {
        "customer_phone": phone,
        "customer_name": "John (extracted)",  # Would be LLM extracted
        "address": "123 Main St (extracted)"
    }

@tool
def classify_service_type(transcript: str) -> str:
    """
    Classify the service needed (plumbing, HVAC, electrical, etc).
    
    Args:
        transcript: What the customer said
    
    Returns:
        Service type: "plumbing" | "hvac" | "electrical" | "unknown"
    """
    # Simulate classification
    if "leak" in transcript.lower() or "toilet" in transcript.lower():
        return "plumbing"
    elif "heat" in transcript.lower() or "air" in transcript.lower():
        return "hvac"
    elif "wire" in transcript.lower() or "electric" in transcript.lower():
        return "electrical"
    return "unknown"

@tool
def assess_urgency(transcript: str) -> str:
    """
    Assess if this is emergency, routine, or scheduling.
    
    Args:
        transcript: What the customer said
    
    Returns:
        Urgency level: "emergency" | "routine" | "scheduling"
    """
    # Simulate urgency detection
    emergency_keywords = ["emergency", "urgent", "right now", "immediately", "overflowing", "broken", "down"]
    
    if any(keyword in transcript.lower() for keyword in emergency_keywords):
        return "emergency"
    elif "schedule" in transcript.lower() or "appointment" in transcript.lower():
        return "scheduling"
    return "routine"

@tool
def save_lead_to_database(job_details: dict) -> dict:
    """
    Save extracted job details to database.
    
    Args:
        job_details: Dict with customer_name, phone, address, service_type, urgency
    
    Returns:
        Saved job record with job_id
    """
    # Week 2: Connect to PostgreSQL
    # For now, simulate
    job_id = f"JOB-{datetime.now().timestamp()}"
    return {
        "job_id": job_id,
        "status": "saved",
        "customer_phone": job_details.get("customer_phone"),
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# LEAD CAPTURE AGENT (The AI Brain)
# ============================================================================

class LeadCaptureAgent:
    """
    AI agent that:
    1. Receives transcript from phone call
    2. Understands what the customer needs
    3. Asks clarifying questions
    4. Extracts structured data
    5. Saves to database
    """
    
    def __init__(self):
        """Initialize the agent with LangChain"""
        try:
            self.llm = ChatOpenAI(
                api_key=OPENAI_API_KEY,
                model="gpt-4-turbo",
                temperature=0.7
            )
        except Exception as e:
            print(f"⚠️ LLM initialization failed: {e}")
            self.llm = None
    
    def create_agent(self):
        """Build the LangChain agent with tools"""
        if not self.llm:
            return None
        
        # Define what tools the agent can use
        tools = [
            extract_contact_info,
            classify_service_type,
            assess_urgency,
            save_lead_to_database,
        ]
        
        # Create the prompt template for the agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant for a home services company (HVAC, plumbing, electrical).
A customer has called with a service request. Your job is to:
1. Understand what service they need
2. Assess urgency
3. Extract their contact info
4. Ask clarifying questions if needed
5. Save the job to the database

Be friendly, professional, and concise. Focus on getting the essential info.
If the customer is in an emergency, acknowledge urgency immediately.
"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=3)
        
        return agent_executor
    
    def process_transcript(self, transcript: str, call_metadata: CallMetadata) -> AgentResponse:
        """
        Process a customer transcript and extract job details.
        
        Args:
            transcript: What the customer said (speech-to-text)
            call_metadata: Phone call metadata from Twilio
        
        Returns:
            Agent response with extracted details and next action
        """
        
        if not self.llm:
            # Fallback: simulate without LLM
            return self._simulate_response(transcript, call_metadata)
        
        try:
            agent = self.create_agent()
            
            # Run the agent
            result = agent.invoke({
                "input": f"""Customer transcript: "{transcript}"
Phone: {call_metadata.from_phone}
Extract: name, address, service type, urgency. Ask for missing info if needed."""
            })
            
            # Parse result and return
            return AgentResponse(
                next_question="What's your address?",  # Would be LLM generated
                job_details=JobDetail(
                    service_type=classify_service_type(transcript),
                    problem_description=transcript,
                    urgency=assess_urgency(transcript),
                    address="123 Main St",  # Would be extracted
                    customer_name="John",
                    customer_phone=call_metadata.from_phone
                ),
                needs_human_handoff=False,
                confidence=0.85
            )
        
        except Exception as e:
            print(f"Agent error: {e}")
            return self._simulate_response(transcript, call_metadata)
    
    def _simulate_response(self, transcript: str, call_metadata: CallMetadata) -> AgentResponse:
        """Fallback simulation when LLM unavailable"""
        return AgentResponse(
            next_question="What's your address?",
            job_details=JobDetail(
                service_type=classify_service_type(transcript),
                problem_description=transcript,
                urgency=assess_urgency(transcript),
                address="123 Main Street (ask to confirm)",
                customer_name="Caller",
                customer_phone=call_metadata.from_phone
            ),
            needs_human_handoff="emergency" in assess_urgency(transcript).lower(),
            confidence=0.70
        )

# Initialize the agent
lead_agent = LeadCaptureAgent()

# ============================================================================
# TWILIO WEBHOOK ENDPOINTS
# ============================================================================

@app.post("/api/calls/incoming")
async def handle_incoming_call(request: Request):
    """
    Twilio webhook: when a customer calls.
    
    Twilio sends call metadata here.
    We respond with TwiML (XML instructions for what to say/do).
    """
    try:
        form_data = await request.form()
        
        # Extract call metadata from Twilio
        call_metadata = CallMetadata(
            call_sid=form_data.get("CallSid", ""),
            from_phone=form_data.get("From", ""),
            to_phone=form_data.get("To", ""),
            call_status=form_data.get("CallStatus", ""),
            timestamp=datetime.now().isoformat()
        )
        
        print(f"📞 Incoming call: {call_metadata.from_phone} → {call_metadata.to_phone}")
        
        # Respond with TwiML (Twilio Markup Language)
        # This tells Twilio what to do next
        twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hi! Thanks for calling Comox Valley Home Services. 
         What service do you need today? Plumbing, HVAC, or electrical?</Say>
    <Record maxLength="120" />
</Response>"""
        
        return Response(content=twiml_response, media_type="application/xml")
    
    except Exception as e:
        print(f"❌ Error handling incoming call: {e}")
        return Response(
            content="""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, there was an error. Please try again.</Say>
</Response>""",
            media_type="application/xml"
        )

@app.post("/api/calls/recording")
async def handle_recording(request: Request):
    """
    Twilio webhook: when recording is ready.
    
    Twilio sends the recording URL and transcription here.
    We process it with the agent.
    """
    try:
        form_data = await request.form()
        
        call_metadata = CallMetadata(
            call_sid=form_data.get("CallSid", ""),
            from_phone=form_data.get("From", ""),
            to_phone=form_data.get("To", ""),
            call_status="recording_received",
            timestamp=datetime.now().isoformat()
        )
        
        # In production, you'd:
        # 1. Download the recording from form_data["RecordingUrl"]
        # 2. Transcribe it with Deepgram or Twilio API
        # 3. Run the agent on the transcript
        
        # For Week 1, simulate
        transcript = "I have an emergency. My toilet is overflowing at 123 Main Street."
        
        print(f"🎙️ Processing recording from {call_metadata.from_phone}")
        print(f"   Transcript: {transcript}")
        
        # Run agent
        agent_response = lead_agent.process_transcript(transcript, call_metadata)
        
        print(f"✅ Agent extracted:")
        print(f"   Service: {agent_response.job_details.service_type}")
        print(f"   Urgency: {agent_response.job_details.urgency}")
        print(f"   Address: {agent_response.job_details.address}")
        
        # Save to database (Week 2)
        # job = save_job_to_db(agent_response.job_details)
        
        # Tell Twilio what to say next
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thanks for that information! 
         A technician will call you back within 30 minutes. Goodbye!</Say>
    <Hangup />
</Response>"""
        
        return Response(content=twiml_response, media_type="application/xml")
    
    except Exception as e:
        print(f"❌ Error processing recording: {e}")
        return {"error": str(e)}, 500

# ============================================================================
# HEALTH CHECK & TEST ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Home Services Lead Capture Agent",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/test/transcript")
async def test_transcript(transcript: str, phone: str = "+1-250-555-1234"):
    """
    Test endpoint: process a transcript without Twilio.
    
    Usage:
    curl -X POST http://localhost:8000/api/test/transcript \
         -H "Content-Type: application/json" \
         -d '{"transcript": "I have an emergency. Toilet is overflowing at 123 Main Street.", "phone": "+1-250-555-1234"}'
    """
    call_metadata = CallMetadata(
        call_sid="TEST-123",
        from_phone=phone,
        to_phone="+1-250-555-PLUMB",
        call_status="test",
        timestamp=datetime.now().isoformat()
    )
    
    response = lead_agent.process_transcript(transcript, call_metadata)
    
    return {
        "success": True,
        "transcript": transcript,
        "extracted": {
            "service_type": response.job_details.service_type,
            "urgency": response.job_details.urgency,
            "address": response.job_details.address,
            "customer_phone": response.job_details.customer_phone,
        },
        "confidence": response.confidence,
        "next_question": response.next_question,
    }

@app.get("/api/jobs")
async def list_jobs():
    """
    List all jobs (Week 2: from database).
    For now, return empty list.
    """
    return {
        "jobs": [],
        "note": "Database integration coming Week 2"
    }

# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║   Home Services Lead Capture Agent - Week 1 MVP                ║
    ║   Starting server on http://localhost:8000                    ║
    ╚════════════════════════════════════════════════════════════════╝
    
    📍 Health check:
       curl http://localhost:8000/health
    
    🧪 Test the agent:
       curl -X POST http://localhost:8000/api/test/transcript \\
            -H "Content-Type: application/json" \\
            -d '{"transcript": "I have an emergency. Toilet is overflowing."}'
    
    📞 Twilio webhooks:
       POST /api/calls/incoming — When customer calls
       POST /api/calls/recording — When recording is ready
    
    Next: Get your OPENAI_API_KEY and test!
    """)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
