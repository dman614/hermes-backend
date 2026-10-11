# Home Services AI Platform: Agents, Tools & Bots Explained

**Learning goal:** Understand what each "agent" does, what "tools" it has access to, and how they work together.

---

## Part 1: What's an Agent?

An **agent** is an AI that:
1. Receives a goal/input
2. Thinks through steps
3. Calls "tools" (functions) to execute those steps
4. Keeps looping until it reaches the goal
5. Returns results

**Real example:**
```
Goal: "A homeowner called about emergency plumbing. Schedule a technician."

Agent thinks:
  1. What info do I have? (name, phone, address, urgency)
  2. Is this emergency or routine? (→ uses "analyze_urgency" tool)
  3. Which technicians are available today? (→ uses "check_availability" tool)
  4. Which tech is closest to the address? (→ uses "find_closest_tech" tool)
  5. Write a quote based on job type (→ uses "generate_quote" tool)
  6. Book the appointment (→ uses "schedule_job" tool)
  7. Send confirmation SMS (→ uses "send_sms" tool)

Result: Job scheduled, quote generated, customer notified.
```

**Key insight:** The agent decides WHEN to use each tool. You don't hardcode "first do X, then Y, then Z." The agent figures it out.

---

## Part 2: Your Home Services Platform - 4 Core Agents

### Agent #1: Lead Capture Agent

**Purpose:** Answer incoming calls and extract job information.

**Inputs:**
- Phone call (via Twilio voice API)
- Caller's voice ("I need emergency plumbing at 123 Main St")

**Tools this agent has access to:**
```python
@tool
def analyze_caller_intent(transcript: str) -> dict:
    """Understand what the caller needs. Returns: service type, urgency, symptoms."""
    # AI listens to transcript, classifies
    return {
        "service_type": "plumbing",
        "urgency": "emergency",
        "symptoms": "toilet overflow in master bath"
    }

@tool
def extract_contact_info(transcript: str) -> dict:
    """Extract name, phone, address from caller speech."""
    return {
        "name": "John Smith",
        "phone": "250-555-1234",
        "address": "123 Main St, Campbell River, BC"
    }

@tool
def extract_job_details(transcript: str) -> dict:
    """Extract specifics: what's broken, any allergies, pet info, etc."""
    return {
        "problem_description": "Toilet overflowing",
        "has_pets": False,
        "preferred_time_window": "today before 5pm"
    }

@tool
def store_lead_in_database(contact_info: dict, job_details: dict) -> str:
    """Save to DB. Returns: job_id."""
    job = Job(
        contractor_id=contractor_id,
        customer_name=contact_info["name"],
        customer_phone=contact_info["phone"],
        customer_address=contact_info["address"],
        service_type=job_details["service_type"],
        urgency=job_details["urgency"],
        problem_description=job_details["problem_description"],
        status="incoming"
    )
    db.session.add(job)
    db.session.commit()
    return job.id
```

**Output:**
- Structured job record in database
- Return to frontend: "Job captured! Review quote before sending to customer."

**Owner interaction:** Owner sees job on dashboard, can edit details, approves before quote goes to customer.

---

### Agent #2: Quote Generation Agent

**Purpose:** Create a professional quote based on job details.

**Inputs:**
- Job details (service type, problem description, urgency, location)
- Historical pricing data (how much similar jobs charged)

**Tools this agent has access to:**
```python
@tool
def lookup_pricing_history(service_type: str, urgency: str) -> dict:
    """What have we charged for similar jobs?"""
    jobs = db.query(Job).filter(
        Job.service_type == service_type,
        Job.urgency == urgency,
        Job.status == "completed"
    ).order_by(Job.completed_date.desc()).limit(10)
    
    prices = [j.quote_amount for j in jobs]
    return {
        "avg_price": sum(prices) / len(prices),
        "min_price": min(prices),
        "max_price": max(prices),
        "similar_jobs": len(prices)
    }

@tool
def estimate_labor_hours(service_type: str, problem_description: str) -> float:
    """How long does this job typically take?"""
    # Lookup from your company's historical data
    estimates = {
        "plumbing": {"simple": 1.5, "moderate": 3, "complex": 5},
        "hvac": {"simple": 2, "moderate": 4, "complex": 6},
        "electrical": {"simple": 2, "moderate": 3.5, "complex": 5}
    }
    return estimates[service_type]["moderate"]  # Simplified

@tool
def calculate_total_cost(
    service_type: str,
    labor_hours: float,
    parts_cost: float,
    dispatch_fee: float = 75
) -> dict:
    """Calculate quote including labor + parts + fees."""
    hourly_rate = 95  # Your company's rate
    labor_cost = labor_hours * hourly_rate
    total = labor_cost + parts_cost + dispatch_fee
    
    return {
        "labor_cost": labor_cost,
        "parts_cost": parts_cost,
        "dispatch_fee": dispatch_fee,
        "subtotal": total,
        "tax_rate": 0.05,
        "tax": total * 0.05,
        "total_with_tax": total * 1.05
    }

@tool
def format_quote_document(job_id: str, cost_breakdown: dict) -> str:
    """Generate professional PDF quote."""
    # Create beautiful PDF with company logo, terms, etc.
    quote_html = f"""
    <html>
    <h1>Service Quote</h1>
    <p>Job: {job_id}</p>
    <p>Service: Plumbing Emergency</p>
    ...
    <p>Total: ${cost_breakdown['total_with_tax']}</p>
    </html>
    """
    pdf = generate_pdf(quote_html)
    return f"quotes/{job_id}_quote.pdf"

@tool
def send_quote_to_owner_for_approval(job_id: str, quote_path: str) -> dict:
    """Notify owner via dashboard/email."""
    # Send notification to owner dashboard
    # Owner can: approve & send to customer, edit amount, reject
    return {
        "notification_sent": True,
        "quote_id": f"quote_{job_id}",
        "approval_deadline": "today at 5pm"
    }
```

**Output:**
- Professional PDF quote
- Notification to contractor (owner): "New quote ready for approval"

**Owner interaction:** Owner reviews quote on dashboard, can adjust price, then approves (or rejects) before it goes to customer.

---

### Agent #3: Scheduling Agent

**Purpose:** Schedule the technician and coordinate the appointment.

**Inputs:**
- Job details (service type, address, urgency, estimated time)
- Available technicians (who's free, location, specialization)
- Customer preferences (preferred date/time)

**Tools this agent has access to:**
```python
@tool
def get_available_technicians(date: str, service_type: str) -> list:
    """Which technicians are free on this date and qualified?"""
    available = db.query(Technician).filter(
        Technician.service_types.contains(service_type),
        ~Technician.is_scheduled(date)  # Not already booked
    ).all()
    
    return [{
        "tech_id": t.id,
        "name": t.name,
        "specialties": t.service_types,
        "rating": t.avg_rating,
        "scheduled_jobs_today": len(t.jobs_on_date(date))
    } for t in available]

@tool
def calculate_travel_time(from_address: str, to_address: str) -> float:
    """How long to drive between two addresses?"""
    # Use Google Maps API or simple distance calc
    distance_km = calculate_distance(from_address, to_address)
    return distance_km / 60 * 1.2  # km / avg_speed * buffer

@tool
def select_best_technician(
    available_techs: list,
    job_address: str,
    last_tech_location: dict
) -> dict:
    """Pick the closest, highest-rated tech who can get there in time."""
    # Scoring: distance (40%) + rating (40%) + experience (20%)
    best = max(available_techs, key=lambda t: score_tech(t, job_address))
    return best

@tool
def create_appointment_slot(
    tech_id: str,
    job_id: str,
    customer_address: str,
    estimated_duration: float,
    preferred_date: str
) -> dict:
    """Block this technician's calendar."""
    appointment = Appointment(
        technician_id=tech_id,
        job_id=job_id,
        date=preferred_date,
        start_time="14:00",  # 2 PM
        end_time="15:30",    # 1.5 hr job
        customer_address=customer_address,
        status="scheduled"
    )
    db.session.add(appointment)
    db.session.commit()
    
    return {
        "appointment_id": appointment.id,
        "tech_name": appointment.technician.name,
        "date": preferred_date,
        "time": "2:00 PM - 3:30 PM",
        "address": customer_address
    }

@tool
def send_appointment_confirmation(
    job_id: str,
    customer_phone: str,
    appointment_details: dict
) -> dict:
    """SMS/email confirmation to customer."""
    sms_body = f"""
    Hi {customer.name}! Your appointment is scheduled:
    Date: {appointment_details['date']}
    Time: {appointment_details['time']}
    Tech: {appointment_details['tech_name']}
    We'll see you soon! Reply STOP to cancel.
    """
    send_sms(customer_phone, sms_body)
    return {"sms_sent": True}

@tool
def notify_technician(tech_id: str, appointment_details: dict) -> dict:
    """Send job card to tech's phone/app."""
    # Push notification or SMS with full job details
    return {"notification_sent": True}
```

**Output:**
- Appointment scheduled
- Customer notified (SMS: "Your plumber is Bob, arriving 2-3:30 PM")
- Technician notified (job card on their phone)
- Owner notified (job status: "scheduled")

**Owner interaction:** Owner approves time window (can override if needed), but agent makes the recommendation.

---

### Agent #4: Billing & Follow-up Agent

**Purpose:** After job is complete, generate invoice, track payment, send follow-ups.

**Inputs:**
- Completed job details (what was done, how long, parts used)
- Payment info (customer payment method)

**Tools this agent has access to:**
```python
@tool
def get_job_completion_data(job_id: str) -> dict:
    """What actually happened on the job? From tech's field notes."""
    job = db.query(Job).filter(Job.id == job_id).first()
    return {
        "parts_used": job.parts_used,  # Plumber logged in app
        "actual_duration": job.actual_duration_hours,
        "problem_description": job.problem_description,
        "solution_description": job.resolution_notes,
        "customer_signature": job.signature_url
    }

@tool
def calculate_final_invoice(
    job_id: str,
    original_quote: dict,
    actual_work: dict
) -> dict:
    """Calculate final amount (might differ from quote if scope changed)."""
    # Labor
    labor_hours = actual_work["actual_duration"]
    labor_cost = labor_hours * 95
    
    # Parts
    parts_cost = actual_work["parts_used_cost"]
    
    # Any adjustments
    total = labor_cost + parts_cost + 75  # dispatch fee
    
    return {
        "line_items": [
            {"description": "Labor (2.5 hrs @ $95/hr)", "amount": 237.50},
            {"description": "Parts (shut-off valve)", "amount": 45.00},
            {"description": "Dispatch Fee", "amount": 75.00}
        ],
        "subtotal": total,
        "tax": total * 0.05,
        "total_due": total * 1.05,
        "original_quote": original_quote["total"],
        "variance": total * 1.05 - original_quote["total"]  # Over/under quote
    }

@tool
def generate_invoice_pdf(job_id: str, invoice_data: dict) -> str:
    """Create professional invoice."""
    # Similar to quote, but now with completion details
    return f"invoices/{job_id}_invoice.pdf"

@tool
def send_invoice_to_customer(customer_phone: str, invoice_path: str) -> dict:
    """Email/SMS invoice and payment link."""
    payment_link = f"https://pay.yourcompany.com/invoice/{invoice_id}"
    sms = f"Your invoice is ready! Pay here: {payment_link}"
    send_sms(customer_phone, sms)
    return {"invoice_sent": True}

@tool
def track_payment(invoice_id: str) -> dict:
    """Check: has customer paid?"""
    payment = db.query(Payment).filter(Payment.invoice_id == invoice_id).first()
    return {
        "paid": payment is not None,
        "amount_paid": payment.amount if payment else 0,
        "date_paid": payment.date if payment else None,
        "balance_due": invoice["total"] - (payment.amount if payment else 0)
    }

@tool
def send_payment_reminder(customer_phone: str, invoice_id: str, days_overdue: int) -> dict:
    """Gentle reminder if unpaid after 3 days."""
    if days_overdue > 3:
        sms = f"Friendly reminder: Your invoice is 3 days overdue. Pay now: {payment_link}"
        send_sms(customer_phone, sms)
    return {"reminder_sent": True}

@tool
def request_review(customer_phone: str, service_info: dict) -> dict:
    """Ask customer to rate the service."""
    sms = f"How was your experience with {tech_name}? Rate here: {review_link}"
    send_sms(customer_phone, sms)
    return {"review_request_sent": True}
```

**Output:**
- Invoice generated and sent
- Payment tracked
- Reminders sent (if unpaid)
- Review request sent

**Owner interaction:** Owner sees invoice on dashboard, can manually adjust if needed. Automatic reminders run nightly.

---

## Part 3: How Agents Coordinate (Database as Central Hub)

**Key principle:** Agents don't talk to each other directly. They all read/write to a shared database.

```
┌─────────────────────────────────────────────────────────────────┐
│  SHARED DATABASE (PostgreSQL)                                   │
│                                                                  │
│  Tables:                                                        │
│  - jobs (incoming leads)                                        │
│  - quotes (generated quotes)                                    │
│  - appointments (scheduled times)                               │
│  - appointments (scheduled times)                               │
│  - technicians (team members)                                   │
│  - invoices (billing)                                           │
│  - payments (received payments)                                 │
│  - customer_feedback (reviews)                                  │
└─────────────────────────────────────────────────────────────────┘
        ▲           ▲           ▲           ▲
        │           │           │           │
   ┌────┴─┐    ┌────┴─┐    ┌────┴─┐    ┌────┴─┐
   │Lead  │    │Quote │    │Schedule  │    │Billing│
   │Agent │    │Agent │    │Agent     │    │Agent  │
   └──────┘    └──────┘    └──────────┘    └───────┘
```

**Workflow example:**

1. **Lead Agent receives call**
   - Extracts info
   - Writes to `jobs` table with status="incoming"
   - Notifies owner: "New lead! Review on dashboard."

2. **Owner reviews on dashboard, clicks "Generate Quote"**
   - Triggers Quote Agent
   - Quote Agent reads `jobs` table (the lead)
   - Quote Agent looks up pricing history from completed `jobs`
   - Quote Agent writes to `quotes` table
   - Dashboard updates: "Quote generated! Ready to send?"

3. **Owner approves quote on dashboard**
   - Quote Agent sends to customer
   - Updates `jobs` table: status="quote_sent"

4. **Customer calls to confirm or modifies request**
   - Lead Agent gets follow-up call
   - Updates `jobs` table with new info

5. **Owner books appointment**
   - Triggers Scheduling Agent
   - Scheduling Agent reads: `jobs`, `technicians`, `appointments` tables
   - Scheduling Agent creates appointment in `appointments` table
   - Sends to customer via SMS
   - Updates `jobs` table: status="scheduled"

6. **Technician completes job, logs in app**
   - Tech logs: time spent, parts used, photos, customer signature
   - Updates `jobs` table: status="completed"

7. **Billing Agent runs (nightly or on-demand)**
   - Reads completed `jobs`
   - Generates invoice, writes to `invoices` table
   - Sends to customer
   - Schedules daily payment checks

**Why this design?**
- ✅ Each agent is independent (can run in parallel)
- ✅ No direct agent-to-agent coupling (easier to debug)
- ✅ Database is source of truth (no data loss)
- ✅ Owner approval happens between agents (human-in-the-loop)
- ✅ Easy to add new agents later (just read/write to DB)

---

## Part 4: Tools vs Agents vs Bots - Terminology

**Tool:** A single function an agent can call.
```python
@tool
def send_sms(phone: str, message: str) -> dict:
    """Send SMS to customer."""
    # One responsibility
```

**Agent:** An AI orchestrator that chains multiple tools together.
```python
agent = LeadCaptureAgent(tools=[analyze_intent, extract_contact, store_in_db])
result = agent.run("I need emergency plumbing")
# Agent decides which tools to call and in what order
```

**Bot:** A broader system (can include multiple agents).
```python
# The entire "Home Services Platform" is a bot system:
bot = HomeSrvicesPlatform(
    agents=[LeadAgent, QuoteAgent, SchedulingAgent, BillingAgent],
    database=PostgreSQL(),
    integrations=[Twilio, Stripe, Google Maps]
)
```

**Skill (in Hermes):** Reusable procedures/tools for the agent (me).
- You won't write "skills" — those are for Hermes to use
- You'll write **agents** (for your customers' contractors)

---

## Part 5: What You'll Build (MVP - 4 Weeks)

### Week 1-2: Lead Capture Agent
- [ ] Twilio voice integration (receive calls)
- [ ] OpenAI Realtime API (AI listens & speaks)
- [ ] Extract job details (intent, address, urgency)
- [ ] Store in PostgreSQL
- [ ] Dashboard notification to owner

### Week 3: Quote Generation Agent
- [ ] Lookup pricing history
- [ ] Estimate labor hours
- [ ] Calculate cost breakdown
- [ ] Generate PDF quote
- [ ] Owner approval on dashboard

### Week 4: Scheduling Agent
- [ ] Get available technicians
- [ ] Select best tech (closest, highest rated)
- [ ] Create appointment
- [ ] Send SMS to customer & tech
- [ ] Show on owner dashboard

### Bonus (if time): Billing Agent
- [ ] Invoice generation
- [ ] Payment tracking
- [ ] Follow-up reminders

---

## Part 6: The Stack You'll Use

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js + React | Dashboard for owner (approve quotes, schedule, see jobs) |
| **API** | FastAPI (Python) | Backend server that runs agents |
| **AI Agent** | LangChain + GPT-4 | Decision-making for each agent |
| **Voice** | Twilio + OpenAI Realtime | Phone calls (lead capture) |
| **Database** | PostgreSQL | Central hub for all data |
| **SMS/Email** | Twilio | Notifications to customer & tech |
| **Payments** | Stripe | Invoice payment processing |
| **Storage** | AWS S3 | Store PDFs (quotes, invoices) |

---

## Next Steps

1. **Understand the concept** (what you just read)
2. **Start coding Lead Capture Agent** (Week 1)
   - I'll show you exact FastAPI + LangChain code
   - We'll integrate Twilio voice
   - Get it working end-to-end
3. **Build owner dashboard** (Week 2)
   - React components
   - Real-time updates
   - Approval buttons
4. **Add Quote Agent** (Week 3)
5. **Add Scheduling Agent** (Week 4)

---

## Key Insight: Why Agents > Manual Workflows

**Without agents (old way):**
1. Contractor manually answers phone
2. Writes down customer info on paper
3. Manually looks up pricing
4. Types quote in Word
5. Emails quote to customer
6. Manually checks calendar
7. Texts technician
= **2-3 hours per job**

**With agents (your platform):**
1. AI answers phone (Lead Agent)
2. Extracts info automatically
3. Looks up pricing automatically (Quote Agent)
4. Generates quote automatically
5. Owner approves (5 minutes)
6. AI books appointment (Scheduling Agent)
7. Texts everyone automatically
= **5 minutes owner time**

**That's the value prop.**

---

Ready to start coding? I'll build the first agent with you step-by-step.
