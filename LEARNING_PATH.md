# How to Learn & Build This Together

## What You Just Learned

### 1. Agents, Tools, Bots (Terminology)
- **Tool** = A single function (e.g., `extract_contact_info`)
- **Agent** = An AI that chains tools together (e.g., Lead Capture Agent)
- **Bot** = The entire system (your home services platform)

### 2. Your 4 Agents (Week by Week)
- **Week 1:** Lead Capture (answers phone, extracts info)
- **Week 2:** Quote Generation (calculates price, makes PDF)
- **Week 3:** Scheduling (books appointment, notifies tech)
- **Week 4:** Billing (invoices, payment tracking)

### 3. Database as Central Hub
All agents read/write to the same PostgreSQL database. No agent talks directly to another agent.

---

## What We're About to Build

### The First Agent (Week 1): Lead Capture

**What happens:**

```
Step 1: Incoming Call
  Customer: "I need emergency plumbing"
  Twilio receives call → sends transcript to your server

Step 2: Lead Agent Runs
  Tool #1: Analyze intent
    INPUT: "I need emergency plumbing"
    OUTPUT: service_type="plumbing", urgency="emergency"
  
  Tool #2: Extract contact
    INPUT: Call transcript
    OUTPUT: name="John", phone="250-555-1234", address="123 Main St"
  
  Tool #3: Store in database
    INPUT: Contact info + job details
    OUTPUT: job_id="abc123"
  
  Tool #4: Notify dashboard
    INPUT: job_id
    OUTPUT: "Contractor notified!"

Step 3: Contractor Sees on Dashboard
  "New emergency plumbing job! John Smith at 123 Main St"
  Next action: Review and approve quote
```

---

## Files You Now Have

### 1. `/home/Dman/home-services-agents-explained.md`
**What:** Detailed explanation of all 4 agents, what tools they need, how they coordinate
**Read it when:** You want to understand the "why" behind each agent
**Key section:** "Part 2: Your 4 Core Agents" — shows exactly what each agent does

### 2. `/home/Dman/lead_capture_agent.py`
**What:** Complete Python code skeleton for the Lead Capture Agent
**Read it when:** You're ready to understand the actual code
**Key sections:**
- `@tool` functions (lines 60-120) — the individual tools
- `create_lead_capture_agent()` (lines 150-190) — how the agent chains them
- `/api/calls/incoming` endpoint (lines 210-250) — where the agent runs

### 3. `/home/Dman/comox-valley-market-research.md`
**What:** Go-to-market plan, contractor list, chamber contacts
**Read it when:** You're thinking about sales/customers

---

## Learning Path (This Week)

### Day 1: Understand the Concept (You're Here)
- [ ] Read: `home-services-agents-explained.md` (Part 1-3)
- [ ] Skim: `lead_capture_agent.py` (don't memorize, just see structure)
- [ ] Ask me: "Why do we need a database in the middle?"

### Day 2: Run the Code
- [ ] Install: `pip install fastapi uvicorn langchain langchain-openai sqlalchemy psycopg2`
- [ ] Set up PostgreSQL (or use Supabase for free)
- [ ] Run: `uvicorn lead_capture_agent:app --reload`
- [ ] Test endpoint: `curl http://localhost:8000/health`

### Day 3: Trace Through an Example
- [ ] Call the `/api/calls/incoming` endpoint
- [ ] Watch the agent think (verbose=True means we see every step)
- [ ] Check database: `SELECT * FROM jobs;`
- [ ] Ask me: "What did the agent actually do?"

### Day 4-5: Modify + Understand
- [ ] Change the simulated transcript → see agent adapt
- [ ] Add a new tool (e.g., `validate_phone_number`)
- [ ] Understand why each tool is separate (not one big function)

---

## The Big Picture: Why We're Doing This

### The Problem
Contractors waste 2-3 hours per job on manual work:
1. Answering phone ❌
2. Writing down info ❌
3. Looking up prices ❌
4. Making quote ❌
5. Booking appointment ❌
6. Texting tech ❌

### The Solution (Your Platform)
AI does all of it automatically, owner just approves:
1. AI answers phone ✅ (Lead Agent)
2. AI extracts info ✅ (Lead Agent)
3. AI looks up prices ✅ (Quote Agent)
4. AI makes quote ✅ (Quote Agent)
5. AI books appointment ✅ (Scheduling Agent)
6. AI texts tech ✅ (Scheduling Agent)
= **5 minutes owner time** instead of 2-3 hours

---

## Next Step: Let's Build

### Option A: Deep Dive (Recommended)
I'll walk you through the code line-by-line:
1. What each import does
2. How to define a tool
3. How LangChain creates an agent loop
4. How to test it

### Option B: Just Run It
You setup the environment and run the skeleton, ask questions as they come up.

### Option C: Build a Different Way
Tell me if you want to use different tech (e.g., different LLM, different framework).

---

## Questions You Might Have

**Q: Do I need to understand LangChain deeply?**
A: No. Just know: LangChain chains tools together in a loop. We tell it what tools exist, it figures out which to use and when.

**Q: Can I use a different database?**
A: Yes. PostgreSQL/Supabase is recommended for cost+scale, but you could use MySQL, MongoDB, etc. Same agent code works.

**Q: Do I need a real Twilio account?**
A: For the MVP, we'll simulate calls. But eventually yes, you'll need Twilio ($0.01 per call to test).

**Q: Can I run this locally?**
A: Yes. We'll use local PostgreSQL or Supabase (free tier). Everything works on your laptop.

**Q: How long until I have a working MVP?**
A: If we focus: 1-2 weeks for Lead Capture Agent + basic dashboard. Add Quote + Scheduling = 3-4 weeks total.

**Q: Will my contractor customers need to understand agents/LangChain?**
A: No. They just see: "New job in" → review → approve → done. No tech knowledge needed.

---

## What's Your Next Move?

You have 3 options:

### 1. Read Deeper
"I want to understand agents better. Tell me how the agent loop works."

### 2. Build Now
"Let's set up the environment and get the skeleton running."

### 3. Ask Questions
"I don't understand [X]. Explain it differently."

**What sounds good?**
