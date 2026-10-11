# 🚀 Week 1: Quick Start Guide

**Goal:** Get the Lead Capture Agent running and test it.

**Time:** 15 minutes

---

## Step 1: Navigate to Backend Directory

```bash
cd /media/Dman/Hermes/Hermes/backend
```

**Verify you see:**
```
.env
.env.example
main.py
README.md
requirements.txt
run.sh
venv/
```

---

## Step 2: Add Your API Keys

### Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create New Secret Key"
3. Copy the key (starts with `sk-proj-`)

### Get Twilio Credentials (Optional for Week 1)

1. Go to https://www.twilio.com/console
2. Note your Account SID and Auth Token
3. Optionally buy a phone number (e.g., 250-555-PLUMB)

### Set Up .env File

```bash
# Open the .env file
nano .env
```

Update these lines:
```env
OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1250555XXXX
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

---

## Step 3: Start the Server

### Option A: Using the Script (Easiest)

```bash
bash run.sh
```

### Option B: Manual Start

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python main.py
```

**Expected output:**
```
╔════════════════════════════════════════════════════════════════╗
║   Home Services Lead Capture Agent - Week 1 MVP                ║
║   Starting server on http://localhost:8000                    ║
╚════════════════════════════════════════════════════════════════╝

INFO:     Application startup complete [uvicorn]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 4: Test It (Open New Terminal)

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "ok",
  "service": "Home Services Lead Capture Agent",
  "timestamp": "2026-09-05T19:10:30.123456"
}
```

### Test 2: Send a Test Transcript

```bash
curl -X POST http://localhost:8000/api/test/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hi, I have an emergency. My toilet is overflowing at 123 Main Street.",
    "phone": "+1-250-555-1234"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "transcript": "Hi, I have an emergency. My toilet is overflowing at 123 Main Street.",
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

### Test 3: Try Different Scenarios

**Scenario A: HVAC Issue (Routine)**
```bash
curl -X POST http://localhost:8000/api/test/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "My air conditioning stopped working. Can I schedule a service visit?", "phone": "+1-250-555-2222"}'
```

**Scenario B: Electrical Issue (Emergency)**
```bash
curl -X POST http://localhost:8000/api/test/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Emergency! I see sparks coming from the outlet in my basement at 789 Pine Avenue.", "phone": "+1-250-555-3333"}'
```

**Scenario C: Scheduling (Routine)**
```bash
curl -X POST http://localhost:8000/api/test/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "I need to schedule an electrician for next week. I want to update my kitchen wiring at 456 Oak Road.", "phone": "+1-250-555-4444"}'
```

---

## Step 5: What's Happening?

### Flow:

```
Your curl request
    ↓
FastAPI receives it
    ↓
LeadCaptureAgent.process_transcript() is called
    ↓
Agent runs LangChain with tools:
  - classify_service_type() → plumbing/hvac/electrical
  - assess_urgency() → emergency/routine/scheduling
  - extract_contact_info() → name/address/phone
  - save_lead_to_database() → mock save (real DB Week 2)
    ↓
Extracted data returned as JSON
    ↓
Your terminal shows the response
```

### Agent Brain:

The agent doesn't just pattern-match. It:

1. **Reads the transcript** from the customer
2. **Calls tools** to extract information
3. **Makes decisions** (is this emergency? what service?)
4. **Returns structured data** (service, urgency, address, phone)

This is what real calls will do too (via Twilio → your server).

---

## Step 6: View the Code

Open `main.py` to see:

- **LeadCaptureAgent class** (line ~200) — The AI brain
- **Tools** (line ~100) — What the agent can do
- **Endpoints** (line ~300) — API routes
- **Pydantic models** (line ~50) — Data structures

Key functions to understand:

```python
@tool
def classify_service_type(transcript: str) -> str:
    """Figure out if it's plumbing, HVAC, or electrical"""

@tool
def assess_urgency(transcript: str) -> str:
    """Is this emergency or routine?"""

@tool
def extract_contact_info(transcript: str, phone: str) -> dict:
    """Get customer name and address"""
```

---

## Troubleshooting

### "Command not found: python"
```bash
# Use python3 instead
python3 main.py
```

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Activate virtual environment first
source venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused"
The server isn't running. Start it first:
```bash
bash run.sh
```

### "OPENAI_API_KEY not set"
Your `.env` file doesn't have the key. Check:
```bash
cat .env | grep OPENAI
```

Should show: `OPENAI_API_KEY=sk-proj-...`

If blank, add your key and restart the server.

---

## What Just Happened?

You've built and tested:

✅ **FastAPI backend** — Receives requests, responds with JSON  
✅ **LangChain agent** — Understands customer intent, extracts data  
✅ **Tools** — classify, assess urgency, extract contact, save  
✅ **Endpoints** — Health check, test transcript, real Twilio webhooks  

This is the core of the system. Week 2 you'll:

- Connect real PostgreSQL database
- Hook up real Twilio webhooks
- Build the dashboard
- Add transcription service

But the AI brain? **Done.** 🧠

---

## Next Steps

### Option A: Deep Dive
Read through `main.py` and understand:
1. How FastAPI works
2. How LangChain agents work
3. How the tools get called

### Option B: Connect to Twilio (Optional for Week 1)
1. Get your Twilio credentials
2. Deploy the server somewhere public (Heroku/Railway/Fly.io)
3. Point Twilio webhook to your server URL
4. Make a test call

### Option C: Move to Week 2
Start building:
1. PostgreSQL database schema
2. Quote Generation Agent
3. Contractor dashboard (Next.js)

---

## Commands to Remember

```bash
# Start server
cd /media/Dman/Hermes/Hermes/backend && bash run.sh

# Test health
curl http://localhost:8000/health

# Test agent
curl -X POST http://localhost:8000/api/test/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "I need emergency plumbing at 123 Main St.", "phone": "+1-250-555-1234"}'

# Stop server (in server terminal)
Ctrl+C

# Check requirements
cat requirements.txt

# Check .env
cat .env | grep OPENAI
```

---

## You're Ready!

The backend is running. The agent is working. The foundation is solid.

Next: **Week 2 — Database + Dashboard** 🚀

Questions? Check the README.md in this directory.
