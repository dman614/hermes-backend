# How Agents Access Cell Phone Calls (Complete Explanation)

## The Short Answer

**The agent doesn't directly access a cell phone call.** Here's the flow:

```
Contractor's Phone (receives call)
           ↓
Twilio (cloud service catches the call)
           ↓
Twilio sends call to YOUR SERVER
           ↓
Your FastAPI server handles it
           ↓
Agent processes the audio/transcript
           ↓
Agent decides what to do
```

---

## How It Actually Works (Step by Step)

### Step 1: Contractor Gets a Business Phone Number (Twilio)

**What the contractor does:**
1. Sign up for Twilio.com (costs ~$1–2/month)
2. Buy a phone number (e.g., 250-555-1234)
3. In Twilio settings, point that number to YOUR SERVER

**What happens:**
- Contractor tells customers to call 250-555-1234
- When someone calls that number, Twilio receives it
- Twilio doesn't answer directly — instead it FORWARDS the call to YOUR SERVER

### Step 2: Twilio Sends the Call to Your Server

**Twilio has a "webhook" feature:**
- A webhook = "Call this URL when something happens"
- In Twilio settings: "When a call comes in, send it to https://yourserver.com/api/calls/incoming"

**The call flows like this:**

```
Customer calls: 250-555-1234
         ↓
Twilio receives it (doesn't answer)
         ↓
Twilio makes HTTP request to YOUR SERVER:
  POST https://yourserver.com/api/calls/incoming
  Body: {
    "from": "+1 250 555 9876",  # Customer's phone
    "to": "+1 250 555 1234",    # Your business number
    "call_id": "abc123xyz"
  }
         ↓
Your FastAPI server receives the request
```

### Step 3: Your Server Handles It (Interactive Call)

**Option A: Live Voice AI (Recommended)**

Your server responds with instructions for Twilio:
```
"Play this message to the customer"
"Listen for their response"
"When they speak, transcribe it"
```

**This is called TwiML (Twilio Markup Language):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Hello! You've reached Comox Valley Plumbing. 
       What's the issue today?</Say>
  <Record maxLength="60" />
</Response>
```

This tells Twilio:
1. Say that message to the caller
2. Record their response (up to 60 seconds)
3. Send the recording back to your server

### Step 4: Agent Processes the Audio

**Now you have:**
- Audio file of what the customer said
- Twilio call_id (unique identifier)

**Your agent does:**

```python
# Convert audio to text (transcription)
transcript = transcribe_audio(audio_file)
# "I need emergency plumbing at 123 Main St"

# Run Lead Capture Agent
agent.invoke({
    "input": f"Customer said: {transcript}",
    "call_id": call_id
})

# Agent extracts:
# - Service type: "plumbing"
# - Urgency: "emergency"
# - Address: "123 Main St"
# - Phone: (extract from call_from)

# Save to database
job = create_job(...)

# Tell Twilio to say something back
say_to_customer("Thanks! A tech will call you back within 30 minutes.")
```

### Step 5: Conversation Loop

**The conversation can be interactive:**

```
Twilio: "What's the problem?"
Customer: "Toilet is overflowing"
         ↓
Transcribed → Sent to your server
         ↓
Agent thinks: "Need address. Ask them."
         ↓
Server responds to Twilio: "Say: What's your address?"
         ↓
Twilio: "What's your address?"
Customer: "123 Main Street"
         ↓
Transcribed → Back to server
         ↓
Agent thinks: "Got it. I have enough info. Confirm and save."
         ↓
Server responds: "Say: Thanks! A plumber will call soon. Goodbye."
         ↓
Twilio hangs up the call
         ↓
Call data saved to database
```

---

## Real-World Example: Incoming Call Walkthrough

### Timeline

```
TIME 0:00 — Customer dials 250-555-1234
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Customer is on phone, call ringing...


TIME 0:02 — Twilio receives the call
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Twilio doesn't answer directly.

Instead, Twilio sends HTTP POST to your server:
  POST /api/calls/incoming HTTP/1.1
  Host: yourserver.com
  
  {
    "CallSid": "CA1234567890abcdef",
    "From": "+1 (250) 555-9876",
    "To": "+1 (250) 555-1234",
    "CallStatus": "ringing"
  }

Your FastAPI server receives this instantly.


TIME 0:03 — Your Server Responds with Instructions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your server sends back TwiML:

  <Response>
    <Say>Hi! Thanks for calling Comox Valley Plumbing. 
         What service do you need?</Say>
    <Record maxLength="120" />
  </Response>

Twilio receives these instructions and plays the message to customer.


TIME 0:05 — Customer Hears Message & Speaks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Twilio: "Hi! Thanks for calling Comox Valley Plumbing. 
         What service do you need?"

Customer: "Hi, I have an emergency. My toilet is overflowing 
          in the master bathroom at 123 Main Street."

Twilio records this (up to 120 seconds).


TIME 0:10 — Twilio Sends Recording to Your Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Twilio sends the recording back:

  POST /api/calls/recording HTTP/1.1
  Host: yourserver.com
  
  {
    "CallSid": "CA1234567890abcdef",
    "RecordingUrl": "https://api.twilio.com/recordings/RE123...",
    "RecordingDuration": "5"
  }

Your server downloads the audio file.


TIME 0:11 — Your Server Transcribes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your server uses Twilio's transcription (or Deepgram/AssemblyAI):

  Original audio: [5 seconds of customer speaking]
  Transcript: "Hi, I have an emergency. My toilet is 
              overflowing in the master bathroom at 
              123 Main Street."


TIME 0:12 — Agent Processes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your Lead Capture Agent runs:

  Agent thinks:
    1. analyze_caller_intent()
       → service_type = "plumbing"
       → urgency = "emergency"
       → problem = "toilet overflowing"
    
    2. extract_contact_info()
       → phone = "+1 (250) 555-9876"  [from Twilio data]
       → address = "123 Main Street"  [from transcript]
       → name = (ask next?)
    
    3. Agent decision: "I need their name. Ask."
    
    4. Return instructions to Twilio:
       "Ask them their name"


TIME 0:13 — Twilio Asks for Name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your server sends back TwiML:

  <Response>
    <Say>Thanks for that information. 
         Can I get your name please?</Say>
    <Record maxLength="30" />
  </Response>

Twilio plays message to customer.

Customer: "John Smith"

Twilio records and sends back to your server.


TIME 0:15 — Agent Extracts Name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Transcript: "John Smith"

Agent runs extract_contact_info() again:
  → name = "John Smith"
  → phone = "+1 (250) 555-9876"
  → address = "123 Main Street"

Agent thinks: "I have everything I need. Save and thank them."


TIME 0:16 — Agent Saves to Database
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
store_lead_in_database() is called:

  INSERT INTO jobs (
    customer_name = "John Smith",
    customer_phone = "250-555-9876",
    customer_address = "123 Main Street",
    service_type = "plumbing",
    urgency = "emergency",
    problem_description = "toilet overflowing",
    status = "incoming"
  )

Job is saved! ID: job_xyz789


TIME 0:17 — Agent Says Goodbye
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your server sends back TwiML:

  <Response>
    <Say>Perfect John! A plumber will call you 
         back within 30 minutes. Thank you!</Say>
    <Hangup />
  </Response>

Twilio plays message and hangs up the call.

Customer's phone: [Call ends]


TIME 0:18 — Contractor Gets Notified
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
notify_contractor_dashboard() sends notification:

  WebSocket message to contractor's browser:
  "New emergency plumbing job! 
   John Smith at 123 Main Street"

Contractor's dashboard: 🔔 Alert pops up with job details


TIME 0:30 — Contractor Calls Customer Back
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Contractor sees job on dashboard, calls John directly:
  "Hi John, this is Bob from Comox Valley Plumbing..."

Job flows into normal workflow (generate quote, schedule, etc.)
```

---

## The Three Ways Agents Access Calls

### Method 1: Twilio Voice API (Recommended for MVP)

**What:** Interactive voice conversation (like above)
**How it works:** Twilio → Your server → TwiML responses → Back to Twilio
**Pros:**
- Fully automated (no human needed)
- Natural conversation flow
- Can ask follow-up questions
- Low cost ($0.01–0.03 per minute)

**Cons:**
- Speech recognition can fail on accents
- More complex setup

**Cost:** ~$20/month (Twilio) + $0.03/min call time

**Best for:** Emergency calls, high-urgency jobs

---

### Method 2: Call Recording + Async Processing

**What:** Twilio records call, your agent transcribes later
**How it works:**
1. Contractor answers phone manually
2. Twilio records the call
3. After call ends, recording sent to your server
4. Your agent transcribes + extracts info
5. Job appears on dashboard

**Pros:**
- Simple (contractor just answers normally)
- Works with any phone
- Transcription more accurate (full conversation)

**Cons:**
- Not real-time (delay of minutes)
- Contractor still had to answer phone
- Agent sees conversation after-the-fact

**Cost:** ~$10/month (Twilio) + transcription ($0.01–0.05/min)

**Best for:** Routine jobs, lower urgency

---

### Method 3: Missed Call Handler

**What:** Caller gets voicemail, agent calls them back
**How it works:**
1. Contractor can't answer (busy)
2. Caller gets: "Leave message or press 1 for callback"
3. If press 1, system captures phone number
4. Agent calls them back automatically
5. Conversation via Method 1 (interactive)

**Pros:**
- Catches every call (even when contractor busy)
- No missed leads
- Better customer experience (agent calls back)

**Cons:**
- Agent needs to initiate outbound call (costs more)
- Timing delay

**Cost:** ~$20/month + $0.01–0.03/min outbound calls

**Best for:** Missed call recovery

---

## What's in Your lead_capture_agent.py Skeleton

```python
@app.post("/api/calls/incoming")
async def handle_incoming_call(request: Request):
    """
    Twilio webhook: incoming call.
    
    When a customer calls your business number,
    Twilio sends data to this endpoint.
    """
    
    form_data = await request.form()
    
    # form_data contains:
    # - CallSid (unique call ID)
    # - From (customer's phone)
    # - To (your business number)
    # - CallStatus (ringing, in-progress, completed)
    
    # In the skeleton, we SIMULATE with fake transcript
    # In production, you'd:
    # 1. Record the call (Twilio does this)
    # 2. Transcribe the audio (Twilio or Deepgram)
    # 3. Pass transcript to agent
    
    transcript = """Simulated: Customer called about emergency plumbing"""
    
    # Run the agent
    agent = create_lead_capture_agent()
    result = agent.invoke({"input": transcript})
    
    # Return TwiML back to Twilio
    return Response(
        content="""
        <Response>
            <Say>Thanks! A plumber will call you soon.</Say>
            <Hangup />
        </Response>
        """,
        media_type="application/xml"
    )
```

---

## The Real Setup (Week 1)

### Step 1: Sign Up for Twilio
```
Go to twilio.com
Sign up (free $15 credit)
Buy a phone number (250-555-XXXX)
Cost: $1–2/month
```

### Step 2: Configure Twilio Webhook
```
In Twilio Dashboard:
  → Phone Numbers
  → Select your number
  → Voice & Fax settings
  → A Call Comes In: POST to https://yourserver.com/api/calls/incoming
```

### Step 3: Your Server Receives Calls
```
Your FastAPI server is running:
  uvicorn lead_capture_agent:app

Contractor publishes phone number
Customer calls 250-555-XXXX
Twilio sends to your server
Your agent processes
Twilio gets response
Customer hears AI voice
```

### Step 4: For Testing Locally
```
Twilio can't reach localhost:8000 (not public)

Options:
1. Use ngrok (free): ngrok http 8000
   → Gives you public URL: https://abc123.ngrok.io
   → Point Twilio webhook to: https://abc123.ngrok.io/api/calls/incoming
   → Now Twilio can reach your local server

2. Deploy to production:
   → Heroku (free tier), Render, Railway, Fly.io
   → Point Twilio to: https://yourapp.herokuapp.com/api/calls/incoming

3. Twilio CLI (for testing):
   → Simulate calls locally without public URL
```

---

## The Full Architecture (How It All Connects)

```
CONTRACTOR'S PHONE
  ↓ (has phone number 250-555-1234)
  ↓
TWILIO (cloud phone service)
  ├─ Receives incoming calls
  ├─ Stores recordings
  ├─ Transcribes audio
  └─ Sends webhooks to your server
  ↓
YOUR SERVER (FastAPI)
  ├─ /api/calls/incoming (receives call notifications)
  ├─ /api/calls/recording (receives recordings)
  ├─ Runs agents to process data
  └─ Sends TwiML responses back to Twilio
  ↓
LANGCHAIN AGENTS
  ├─ Lead Capture (understands what they need)
  ├─ Extract contact (gets their info)
  ├─ Store in DB (saves it)
  └─ Notify contractor (alerts them)
  ↓
POSTGRESQL DATABASE
  └─ Stores all job data
  ↓
CONTRACTOR'S DASHBOARD
  ├─ WebSocket notifications (real-time)
  └─ Shows new job + can approve quote
```

---

## Costs (Real Numbers)

### Twilio Pricing
- **Inbound calls:** $0.0075 per minute
- **Outbound calls:** $0.013 per minute
- **Phone number:** $1–2 per month
- **Transcription:** Included or $0.000015 per second

**Example:** 50 calls/month × 5 min avg = $1.88/month + $1.50 number = **~$3.50/month**

### Deepgram (Better Transcription)
- **Transcription:** $0.0059 per minute
- **Example:** 50 calls × 5 min = $1.48/month

### Contractor's Phone Service (They Already Have)
- **Cost:** $0 (uses existing phone)
- **Number:** You provide (via Twilio)
- **Rerouting:** No extra hardware needed

---

## What Happens in Production

### Week 1 (MVP Testing)
```
Contractor (you):
  1. Sign up for Twilio
  2. Get phone number
  3. Deploy your server to public URL (ngrok or Heroku)
  4. Point Twilio webhook to your server
  5. Test by calling the number yourself
  6. Watch agent process your call
  7. Verify job saved to database
```

### Week 2 (Real Contractor Testing)
```
Beta Contractor:
  1. Gets phone number: 250-555-PLUMB
  2. Tells customers to call that number
  3. Customer calls
  4. Twilio routes to your server
  5. Your agent answers + extracts info
  6. Job appears on contractor's dashboard
  7. Contractor approves quote
  8. Everything flows normally
```

### Week 4 (Production Launch)
```
20 Contractors:
  - Each has their own Twilio number
  - Each gets routed to your server
  - Same code, different webhook data
  - Your agents scale to handle all 20 simultaneously
  - All data in same database (organized by contractor_id)
```

---

## Bottom Line

**The agent gets access to calls via Twilio webhooks:**

1. **Contractor** gets a Twilio phone number (e.g., 250-555-PLUMB)
2. **Customer** calls that number
3. **Twilio** intercepts the call, doesn't answer directly
4. **Twilio** sends HTTP request to YOUR SERVER with call data
5. **Your server** responds with TwiML instructions (what to say/record)
6. **Twilio** acts as the voice interface (plays messages, records customer)
7. **Your agent** processes the transcript
8. **Database** stores the job
9. **Contractor's dashboard** shows it in real-time

**The agent never "accesses" the phone directly. Instead:**
- Twilio is the phone system
- Your server is the intelligent middleman
- Agents process the data (text transcripts)
- Everything flows through standard HTTP webhooks

**Cost:** ~$3–5/month per contractor (Twilio + transcription)

Does this clear it up?
