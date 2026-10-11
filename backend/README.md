# Home Services AI Platform - Backend (Week 1: Lead Capture Agent)

**Status:** Week 1 MVP - Ready to Run  
**Location:** `/media/Dman/Hermes/Hermes/backend/`  
**Tech Stack:** FastAPI + LangChain + Twilio  

---

## What This Does

**Lead Capture Agent** answers phone calls and extracts job details:

```
Customer calls 250-555-PLUMB
         ↓
Twilio routes to your server
         ↓
Agent hears: "I have an emergency. Toilet is overflowing at 123 Main Street."
         ↓
Agent extracts:
  - Service: plumbing
  - Urgency: emergency
  - Address: 123 Main Street
  - Phone: (from Twilio)
         ↓
Job saved to database
         ↓
Contractor sees it on dashboard
```

---

## Quick Start (5 Minutes)

### 1. Get Your API Keys

**OpenAI (for LLM/Agent):**
```bash
# Go to https://platform.openai.com/api-keys
# Create a new API key
# Copy it
```

**Twilio (for phone):**
```bash
# Go to https://www.twilio.com/console
# Note your Account SID and Auth Token
# Buy a phone number (e.g., 250-555-PLUMB)
```

### 2. Set Up Environment

```bash
cd /media/Dman/Hermes/Hermes/backend

# Copy example env and add your keys
cp .env.example .env
nano .env  # Add your OpenAI API key + Twilio credentials
```

### 3. Activate Virtual Environment & Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Server

```bash
python main.py
```

**Expected output:**
```
INFO:     Application startup complete [uvicorn]
INFO:     Uvicorn running on http://0.0.0.0:8000 [production]
```

### 5. Test It

**In another terminal:**

```bash
# Health check
curl http://localhost:8000/health

# Test the agent with a sample transcript
curl -X POST http://localhost:8000/api/test/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "I have an emergency. My toilet is overflowing at 123 Main Street.", "phone": "+1-250-555-1234"}'
```

**Expected response:**
```json
{
  "success": true,
  "transcript": "I have an emergency. My toilet is overflowing at 123 Main Street.",
  "extracted": {
    "service_type": "plumbing",
    "urgency": "emergency",
    "address": "123 Main Street",
    "customer_phone": "+1-250-555-1234"
  },
  "confidence": 0.85,
  "next_question": "What's your address?"
}
```

---

## Project Structure

```
backend/
├── main.py                    # FastAPI app + Lead Capture Agent
├── requirements.txt           # Python dependencies
├── .env                       # Your secrets (OpenAI, Twilio keys)
├── .env.example              # Template for .env
├── venv/                      # Virtual environment
└── (coming Week 2)
    ├── database.py           # PostgreSQL connection
    ├── models.py             # SQLAlchemy models (Job, Contact, etc)
    ├── agents/
    │   ├── lead_capture.py   # Refactored agent
    │   ├── quote_generator.py
    │   ├── scheduler.py
    │   └── billing.py
    └── api/
        ├── routes.py         # API endpoints
        └── webhooks.py       # Twilio webhooks
```

---

## How It Works (Architecture)

### 1. Phone Call Flow

```
Customer calls
  ↓
Twilio intercepts (doesn't answer directly)
  ↓
Twilio sends HTTP POST to /api/calls/incoming
  ↓
Your server responds with TwiML (XML instructions)
  ↓
Twilio plays: "Hi! What service do you need?"
  ↓
Customer speaks: "I have an emergency. Toilet is overflowing."
  ↓
Twilio records (up to 120 seconds)
  ↓
Twilio sends recording + transcription to /api/calls/recording
  ↓
Your agent processes the transcript
  ↓
Agent extracts: service, urgency, address, phone
  ↓
Saved to database
  ↓
Contractor's dashboard updates in real-time (WebSocket)
```

### 2. Agent Brain (LangChain)

The agent has "tools" it can call:

```python
@tool
def classify_service_type(transcript: str) -> str:
    """Determine if it's plumbing, HVAC, electrical, etc."""

@tool
def assess_urgency(transcript: str) -> str:
    """Is this emergency, routine, or scheduling?"""

@tool
def extract_contact_info(transcript: str, phone: str) -> dict:
    """Get customer name, address, phone."""

@tool
def save_lead_to_database(job_details: dict) -> dict:
    """Store the extracted job in PostgreSQL."""
```

The agent receives the transcript and decides which tools to call. LangChain handles the orchestration.

### 3. API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (is server running?) |
| `/api/calls/incoming` | POST | Twilio webhook: customer calls |
| `/api/calls/recording` | POST | Twilio webhook: recording ready |
| `/api/test/transcript` | POST | Test endpoint: send transcript, get extraction |
| `/api/jobs` | GET | List all jobs (empty for now) |

---

## Testing Locally (Without Twilio)

Use the test endpoint to simulate what Twilio sends:

```bash
# Terminal 1: Start the server
python main.py

# Terminal 2: Send test transcripts
curl -X POST http://localhost:8000/api/test/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hi, I need emergency plumbing. Theres water everywhere in the kitchen at 456 Oak Road.",
    "phone": "+1-250-555-9876"
  }'
```

**Test cases to try:**

1. **Emergency plumbing:**
   ```json
   {"transcript": "Emergency! Toilet overflowing at 123 Main St", "phone": "+1-250-555-1111"}
   ```

2. **Routine HVAC:**
   ```json
   {"transcript": "My AC isn't working. Can you schedule a checkup?", "phone": "+1-250-555-2222"}
   ```

3. **Electrical issue:**
   ```json
   {"transcript": "I have sparking wires in my basement at 789 Pine Ave", "phone": "+1-250-555-3333"}
   ```

---

## Environment Setup Details

### Python Version
```bash
python3 --version
# Python 3.13.5 (or newer)
```

### Virtual Environment

```bash
# Create (one-time)
python3 -m venv venv

# Activate (every session)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Check it's activated (should show venv prefix)
which python  # /path/to/venv/bin/python
```

### Dependencies

**Core:**
- `fastapi` — Web framework
- `uvicorn` — ASGI server (runs FastAPI)
- `langchain` — AI agent orchestration
- `langchain-openai` — LLM integration

**External Services:**
- `twilio` — Phone calls & SMS
- `openai` — LLM (via LangChain)

**Database (Week 2):**
- `psycopg` — PostgreSQL driver
- `sqlalchemy` — ORM

**Utils:**
- `python-dotenv` — Load .env files
- `pydantic` — Data validation

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"

You forgot to activate the virtual environment:
```bash
source venv/bin/activate
```

Or you didn't install dependencies:
```bash
pip install -r requirements.txt
```

### "OPENAI_API_KEY not set"

Your `.env` file is missing or doesn't have the key. Check:
```bash
cat .env
# Should show: OPENAI_API_KEY=sk-proj-...
```

If it's empty or missing, create it:
```bash
cp .env.example .env
nano .env
# Paste your real OpenAI API key
```

### "Connection refused" (port 8000)

Another app is using port 8000. Change it in `main.py`:
```python
uvicorn.run("main:app", host="0.0.0.0", port=8001)  # Use 8001 instead
```

Or kill the other process:
```bash
lsof -i :8000
kill -9 <PID>
```

### Agent Isn't Extracting Info Correctly

The LLM might not be working. Check:
1. `OPENAI_API_KEY` is valid (test on openai.com)
2. API key has `gpt-4-turbo` access (not just gpt-3.5)
3. Account has sufficient credits

For now, the code falls back to simple keyword matching. Week 2, we'll add better prompting.

---

## What Happens in Week 2

- ✅ Database integration (PostgreSQL + SQLAlchemy)
- ✅ Real Twilio webhook routing (not just simulation)
- ✅ Contractor dashboard (Next.js frontend)
- ✅ WebSocket real-time notifications
- ✅ Quote generation (Agent #2)
- ✅ Transcription service (Deepgram or OpenAI Whisper)

---

## Key Files to Understand

### `main.py` (The Core)

**Classes:**
- `LeadCaptureAgent` — The AI brain (calls LangChain)
- `CallMetadata` — Data from Twilio
- `JobDetail` — Extracted job info
- `AgentResponse` — What the agent returns

**Endpoints:**
- `POST /api/calls/incoming` — Incoming call
- `POST /api/calls/recording` — Recording ready
- `POST /api/test/transcript` — Manual test

**Tools:**
- `classify_service_type()` — What service?
- `assess_urgency()` — Emergency or routine?
- `extract_contact_info()` — Who and where?
- `save_lead_to_database()` — Store it

### `.env` (Your Secrets)

**Never commit this to git!**

Contains:
- OpenAI API key
- Twilio credentials
- Database password

### `requirements.txt` (Dependencies)

Lists all Python packages. Run:
```bash
pip install -r requirements.txt
```

---

## Next Steps

### For Week 1:
1. ✅ Set up environment
2. ✅ Run the server
3. ✅ Test with `/api/test/transcript`
4. **TODO:** Connect to real Twilio (optional for MVP)

### For Week 2:
1. Add PostgreSQL database
2. Connect Twilio webhooks
3. Build contractor dashboard (Next.js)
4. Add real transcription service
5. Build Quote Generation Agent

### For Week 3:
1. Add Scheduling Agent
2. Calendar integration
3. SMS notifications

### For Week 4:
1. Add Billing Agent
2. Stripe integration
3. Invoice generation

---

## Running Tests

```bash
# Test health check
curl http://localhost:8000/health

# Test agent with transcript
curl -X POST http://localhost:8000/api/test/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "I have an emergency. Toilet overflowing at 123 Main."}'

# List jobs
curl http://localhost:8000/api/jobs
```

---

## Debugging

**Verbose logging:**
```bash
# Edit main.py and change:
# uvicorn.run("main:app", log_level="info")
# To:
uvicorn.run("main:app", log_level="debug")
```

**Check what the agent is thinking:**
Look at the console output when you send a test request. LangChain will show its thought process.

---

## Deployment (Later)

When ready for production:

1. Deploy to Heroku, Railway, or Fly.io
2. Set real environment variables on the platform
3. Point Twilio webhooks to your production URL
4. Connect to production PostgreSQL database

More details in Week 2.

---

## Questions?

Check:
1. `/media/Dman/Hermes/Hermes/home-services-agents-explained.md` — Concept guide
2. `/media/Dman/Hermes/Hermes/HOW_AGENTS_ACCESS_CALLS.md` — Phone flow
3. `/media/Dman/Hermes/Hermes/VISUAL_WALKTHROUGH.md` — Step-by-step example

---

**Status:** ✅ Ready to Run  
**Timeline:** Week 1 of 4  
**Next:** Test it! Then connect to Twilio  

Let's build. 🚀
