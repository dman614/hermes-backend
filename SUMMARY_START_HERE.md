# Home Services Platform — Everything You Now Know

## Summary of What We've Covered

### 1. The Business (Comox Valley, BC)
- **Market:** 35–50 HVAC/plumbing/electrical contractors
- **Problem:** Contractors waste 2–3 hours per job on manual work
- **Solution:** AI agents automate scheduling, quoting, lead capture, billing
- **Pricing:** $299–799 CAD/month (vs Jobber $169–349, yours has more AI)
- **Year 1 Goal:** 10–15 customers = $82–123K CAD ARR

### 2. The Architecture (4 Agents)

#### Agent #1: Lead Capture
- Receives: Incoming phone call
- Tools: analyze_intent, extract_contact, store_in_db, notify_dashboard
- Outputs: Job record saved, contractor notified
- Time: ~1 minute

#### Agent #2: Quote Generation
- Receives: Job details
- Tools: lookup_pricing, estimate_labor, calculate_cost, generate_pdf, send_for_approval
- Outputs: Professional quote, contractor reviews, approves, sends to customer
- Time: ~2 minutes (after contractor approval)

#### Agent #3: Scheduling
- Receives: Customer accepted quote
- Tools: get_available_techs, calculate_travel_time, select_best_tech, create_appointment, send_confirmation
- Outputs: Appointment booked, customer notified, tech notified, calendar blocked
- Time: ~30 seconds

#### Agent #4: Billing
- Receives: Job completed (from tech's app)
- Tools: get_completion_data, calculate_invoice, generate_pdf, send_to_customer, track_payment, send_reminders
- Outputs: Invoice sent, payment tracked, reminders sent daily until paid
- Time: Fully automated nightly

### 3. The Data Model (PostgreSQL)

All agents read/write to these tables:
- `jobs` (incoming leads)
- `quotes` (generated quotes)
- `appointments` (scheduled times)
- `technicians` (team members)
- `invoices` (billing)
- `payments` (received money)
- `customer_feedback` (reviews)

**Key principle:** Database is the hub. No agent talks directly to another agent.

### 4. The Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Next.js + React + Tailwind | Owner's dashboard (approve, view, manage) |
| Backend | FastAPI (Python) | Server that runs agents |
| AI Logic | LangChain + GPT-4 | Agent orchestration and decision-making |
| Voice | Twilio + OpenAI Realtime | Phone calls (lead capture) |
| Database | PostgreSQL | Central data hub |
| Notifications | Twilio SMS/Email | SMS to customers, techs, contractor |
| Payments | Stripe API | Invoice payment processing |
| Storage | AWS S3 | PDFs (quotes, invoices) |

### 5. The Files You Have

| File | Purpose | When to Read |
|------|---------|--------------|
| `comox-valley-market-research.md` | Market research, contractor list, chambers, GTM timeline | When thinking about sales/customers |
| `home-services-agents-explained.md` | Detailed breakdown of all 4 agents, tools, workflows | When learning the concept |
| `lead_capture_agent.py` | Complete Python skeleton for Week 1 agent | When ready to code |
| `VISUAL_WALKTHROUGH.md` | Step-by-step example of a job from call to payment | When you want to "see" it working |
| `LEARNING_PATH.md` | How to learn + build this over 4 weeks | Your roadmap |

### 6. What an Agent Actually Does

```
Agent Loop:
1. Receives input/goal
2. Thinks: "What tools do I need?"
3. Calls first tool → gets result
4. Thinks: "What's next?"
5. Calls second tool → gets result
6. Repeats until goal complete
7. Returns final output

Example (Lead Capture):
  INPUT: "Customer called about emergency plumbing"
  Step 1: analyze_caller_intent() → "urgency=emergency, type=plumbing"
  Step 2: extract_contact_info() → "name=John, phone=250-555-1234, address=..."
  Step 3: store_in_database() → "job_id=abc123"
  Step 4: notify_dashboard() → "Contractor sees it"
  OUTPUT: Job saved, contractor notified
```

---

## Your Next Week (4 Options)

### Option 1: Deep Dive (Recommended for Learning)
**Goal:** Understand how everything works before coding

- [ ] Day 1–2: Read `home-services-agents-explained.md` (all parts)
- [ ] Day 3: Read `VISUAL_WALKTHROUGH.md` (trace example)
- [ ] Day 4: Skim `lead_capture_agent.py` (understand structure)
- [ ] Day 5: Ask me detailed questions

**Time: ~8 hours**

### Option 2: Learn by Building
**Goal:** Set up environment and run the code

- [ ] Day 1: Install dependencies
- [ ] Day 2: Set up PostgreSQL locally (or Supabase)
- [ ] Day 3: Run the Lead Capture Agent skeleton
- [ ] Day 4: Simulate a call, watch agent think
- [ ] Day 5: Modify + experiment

**Time: ~10 hours**

### Option 3: Speed Run (Aggressive)
**Goal:** Have a working MVP in 1 week

- [ ] Day 1–2: Setup + run skeleton
- [ ] Day 3–4: Add real Twilio integration
- [ ] Day 5: Build basic React dashboard
- [ ] Day 6–7: Test with real contractor

**Time: ~40 hours**

### Option 4: Business First
**Goal:** Validate with customers before building

- [ ] Day 1–2: Reach out to Comox Valley Chamber
- [ ] Day 3–4: Cold call contractors ("Want to be a beta customer?")
- [ ] Day 5–7: Gather feedback on what they'd actually use

**Time: ~15 hours**

---

## What Happens Next (My Recommendations)

### Short Term (Week 1–2)
1. **Pick your learning style** (Deep dive vs. Build vs. Validate)
2. **Get the Lead Capture Agent working**
3. **Test with a real contractor** (even with fake calls)

### Medium Term (Week 3–4)
1. **Add Quote Generator**
2. **Build basic React dashboard** (so contractor can approve)
3. **Prepare for sales outreach**

### Long Term (Week 5–8)
1. **Add Scheduling Agent**
2. **Land first 3 paying customers**
3. **Iterate based on real feedback**
4. **Document everything** (so you can scale)

---

## Key Concepts (Simplified)

**What's an agent?**
An AI that takes a goal, breaks it into steps, calls functions (tools), and returns a result.

**Why LangChain?**
It handles the "thinking loop" for you. You define tools, it figures out when to call them.

**Why database in the middle?**
Agents can't talk directly (causes bugs). Instead, they all read/write the same database.

**Why Twilio?**
It's the easiest way to receive phone calls and send SMS. Industry standard for small businesses.

**Why FastAPI?**
It's fast, modern, and works great with Python + LangChain. Perfect for this project.

**Why Next.js?**
It's the fastest way to build a React dashboard. You already know React from the restaurant MVP.

---

## How This Differs from Your Restaurant MVP

### Restaurant Platform (What You Built)
- **Agent:** Scheduling Agent (predicts labor %, suggests shifts)
- **Frequency:** Runs once per day (nightly)
- **Interface:** Owner approves on dashboard
- **Goal:** Optimize one restaurant's labor costs

### Home Services Platform (What You're Building Now)
- **Agents:** 4 agents (lead, quote, schedule, billing)
- **Frequency:** Runs continuously (every call, every approval)
- **Interface:** Dashboard for contractor to manage jobs
- **Goal:** Automate entire job workflow for multiple customers

**Reused Code:**
- FastAPI structure ✅
- LangChain agents ✅
- Database + ORM patterns ✅
- Authentication ✅
- React dashboard patterns ✅

---

## Questions You Might Still Have

**Q: How do I know if my agent is working correctly?**
A: Set `verbose=True` in LangChain. It prints every step the agent takes. You'll see exactly what it's thinking.

**Q: What if the agent makes a wrong decision?**
A: That's why owner approval is critical. Agent suggests, owner approves. No auto-execution until Phase 2.

**Q: How much does OpenAI's GPT-4 cost to run this?**
A: ~$0.01–0.05 per agent run (per job). Negligible for your MVP. Scale to 100 jobs/week = $5–25/week.

**Q: Can I use a cheaper LLM (Claude, Mistral)?**
A: Yes. LangChain supports all of them. GPT-4 is best for now (you'll have reasoning). Downgrade to GPT-4-turbo later if needed.

**Q: What if a contractor doesn't know how to use this?**
A: Phase 1: You personally onboard them + provide phone support. Phase 2: Self-serve + help docs.

**Q: How do I make money if I'm giving this to contractors?**
A: SaaS pricing ($299–799/mo). No per-transaction fees (they hate that). You keep everything.

---

## Let's Move Forward

**Pick one and let me know:**

1. **"I want to understand the code first"** → I'll walk you through `lead_capture_agent.py` line-by-line
2. **"I want to set up and run it"** → I'll help you install dependencies + get PostgreSQL working
3. **"I want to learn by doing"** → We'll code together, I'll explain as we go
4. **"I want to talk to contractors first"** → I'll help you write cold call scripts + chamber pitch

What sounds right?
