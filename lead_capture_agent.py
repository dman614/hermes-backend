"""
Home Services Lead Capture Agent - Week 1 MVP
FastAPI + LangChain + Twilio

This is the SKELETON. We'll build it together.
"""

from fastapi import FastAPI, Request
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import httpx
from sqlalchemy import create_engine, Column, String, DateTime, Float
from sqlalchemy.orm import declarative_base, Session
import os
from datetime import datetime
from twilio.rest import Client

# ============================================================================
# SETUP
# ============================================================================

app = FastAPI()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/home_services")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# LLM
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.3)

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Job(Base):
    """A job/lead from a customer call."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    contractor_id = Column(String)  # Which contractor's job is this
    customer_name = Column(String)
    customer_phone = Column(String)
    customer_address = Column(String)
    service_type = Column(String)  # "plumbing", "hvac", "electrical"
    urgency = Column(String)  # "emergency", "routine", "scheduled"
    problem_description = Column(String)
    status = Column(String)  # "incoming", "quote_pending", "quote_sent", "scheduled", "completed"
    created_at = Column(DateTime, default=datetime.utcnow)
    estimated_cost = Column(Float, nullable=True)

Base.metadata.create_all(bind=engine)

# ============================================================================
# TOOLS (Functions the Agent Can Call)
# ============================================================================

@tool
def analyze_caller_intent(transcript: str) -> dict:
    """
    AI listens to what the caller said and understands what they need.
    
    INPUT: Recording transcript (what the AI heard on the call)
    OUTPUT: Structured data about the job
    """
    # In real life, you'd get this from the Twilio recording
    # For now, we'll use an LLM to parse it
    
    prompt = f"""
    A customer called a plumber. Here's what they said:
    "{transcript}"
    
    Extract:
    1. service_type: "plumbing", "hvac", or "electrical"
    2. urgency: "emergency", "routine", or "scheduled"
    3. problem_description: what's actually broken (e.g., "toilet overflowing")
    
    Return JSON only.
    """
    
    response = llm.invoke(prompt)
    # Parse response into JSON (we'll do this properly later)
    return {
        "service_type": "plumbing",
        "urgency": "emergency",
        "problem_description": "Toilet overflowing in master bathroom"
    }

@tool
def extract_contact_info(transcript: str) -> dict:
    """
    Extract name, phone, and address from the call transcript.
    
    INPUT: What was said on the call
    OUTPUT: Customer contact details
    """
    prompt = f"""
    From this call transcript, extract:
    1. name: Customer's name
    2. phone: Their phone number (format: 250-XXX-XXXX)
    3. address: Their street address
    
    Transcript: "{transcript}"
    
    Return JSON only.
    """
    
    response = llm.invoke(prompt)
    return {
        "name": "John Smith",
        "phone": "250-555-1234",
        "address": "123 Main St, Campbell River, BC V9W 2B1"
    }

@tool
def store_lead_in_database(
    contractor_id: str,
    contact_info: dict,
    job_details: dict
) -> str:
    """
    Save the job to the database.
    
    INPUT: Contractor ID, customer info, job details
    OUTPUT: Job ID (so we can refer to it later)
    """
    from uuid import uuid4
    
    job_id = str(uuid4())
    
    # Create job record
    job = Job(
        id=job_id,
        contractor_id=contractor_id,
        customer_name=contact_info["name"],
        customer_phone=contact_info["phone"],
        customer_address=contact_info["address"],
        service_type=job_details["service_type"],
        urgency=job_details["urgency"],
        problem_description=job_details["problem_description"],
        status="incoming"
    )
    
    # Save to database
    db = Session(engine)
    db.add(job)
    db.commit()
    db.close()
    
    return job_id

@tool
def notify_contractor_dashboard(contractor_id: str, job_id: str, job_details: dict) -> dict:
    """
    Send a notification to the contractor's dashboard.
    
    INPUT: Job ID and details
    OUTPUT: Confirmation that notification was sent
    """
    # In real life, this would:
    # - Send a WebSocket message to the contractor's dashboard
    # - Show: "New lead! [Customer Name] called about [Problem]"
    
    print(f"DASHBOARD NOTIFICATION: New job {job_id} for {contractor_id}")
    print(f"  Customer: {job_details}")
    
    return {
        "notification_sent": True,
        "message": "Contractor notified on dashboard"
    }

# ============================================================================
# THE AGENT
# ============================================================================

def create_lead_capture_agent():
    """Create the Lead Capture Agent."""
    
    tools = [
        analyze_caller_intent,
        extract_contact_info,
        store_lead_in_database,
        notify_contractor_dashboard
    ]
    
    # This is the agent's personality/instructions
    system_prompt = """
    You are the Lead Capture Agent for a home services company.
    
    Your job:
    1. The customer has just called and we have a transcript of what they said
    2. You must understand what service they need (plumbing, HVAC, electrical)
    3. Extract their contact information
    4. Save it to the database
    5. Notify the contractor
    
    Use the tools in order:
    1. First, analyze what they said (analyze_caller_intent)
    2. Then extract their contact info (extract_contact_info)
    3. Then save to database (store_lead_in_database)
    4. Finally, notify the contractor (notify_contractor_dashboard)
    
    Be thorough. If something is unclear, note it.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create the agent (LangChain handles the thinking loop)
    agent = create_tool_calling_agent(llm, tools, prompt_template)
    
    # Wrap it in an executor (this makes it run the loop)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # Print every step (great for learning)
        max_iterations=10
    )
    
    return executor

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/api/calls/incoming")
async def handle_incoming_call(request: Request):
    """
    Twilio webhook: incoming call.
    
    Twilio calls this URL when someone calls your plumbing business.
    """
    
    form_data = await request.form()
    
    # For now, we'll simulate. In production, you'd:
    # 1. Record the call
    # 2. Transcribe it (Twilio + Deepgram or AssemblyAI)
    # 3. Pass transcript to agent
    
    # SIMULATED CALL
    transcript = """
    Customer: Hi, I have an emergency. My toilet is overflowing in the master bathroom.
    Operator: I'm sorry to hear that. What's your name?
    Customer: John Smith.
    Operator: Can I get your phone number?
    Customer: 250-555-1234
    Operator: And your address?
    Customer: 123 Main St, Campbell River, BC V9W 2B1
    """
    
    contractor_id = "contractor_123"  # In real life, look this up from call routing
    
    # Run the agent
    agent = create_lead_capture_agent()
    
    result = agent.invoke({
        "input": f"""
        A customer just called. Here's what was said:
        
        {transcript}
        
        Extract the information and save the lead to our database.
        Our contractor_id is: {contractor_id}
        """
    })
    
    # Agent completed! Return success
    return {
        "status": "success",
        "message": "Lead captured and contractor notified",
        "agent_output": result["output"]
    }

@app.get("/api/jobs")
def get_jobs(contractor_id: str):
    """
    Get all jobs for a contractor.
    
    Called by the frontend dashboard.
    """
    db = Session(engine)
    jobs = db.query(Job).filter(Job.contractor_id == contractor_id).all()
    db.close()
    
    return [{
        "id": job.id,
        "customer_name": job.customer_name,
        "customer_phone": job.customer_phone,
        "customer_address": job.customer_address,
        "service_type": job.service_type,
        "urgency": job.urgency,
        "problem": job.problem_description,
        "status": job.status,
        "created_at": job.created_at
    } for job in jobs]

@app.get("/health")
def health_check():
    """Sanity check endpoint."""
    return {"status": "ok"}

# ============================================================================
# TO RUN THIS
# ============================================================================

"""
1. Install dependencies:
   pip install fastapi uvicorn langchain langchain-openai sqlalchemy psycopg2 twilio

2. Set environment variables:
   export OPENAI_API_KEY="sk-..."
   export DATABASE_URL="postgresql://user:password@localhost/home_services"
   export TWILIO_ACCOUNT_SID="ACxxx"
   export TWILIO_AUTH_TOKEN="xxxxx"
   export TWILIO_PHONE="+1234567890"

3. Start the server:
   uvicorn this_file:app --reload

4. Test the agent:
   curl -X POST http://localhost:8000/api/calls/incoming

5. View jobs:
   curl http://localhost:8000/api/jobs?contractor_id=contractor_123
"""
