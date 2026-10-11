# Visual: How Your Platform Works (Animated in Your Head)

## The Phone Call Example

```
TIME 0:00 — INCOMING CALL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 Customer calls: "Hello? I have an emergency. My toilet is 
                   overflowing in the master bathroom. I'm John 
                   Smith at 123 Main St, Campbell River."

Twilio receives call → Transcribes to text → Sends to YOUR SERVER


TIME 0:05 — LEAD AGENT STARTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agent (GPT-4) thinks: "I need to understand this job and save it."

Step 1: Tool "analyze_caller_intent"
  Agent: "The caller said 'toilet overflowing' — that's plumbing.
          They said 'emergency' — high urgency."
  
  OUTPUT: {
    "service_type": "plumbing",
    "urgency": "emergency",
    "problem_description": "Toilet overflowing in master bathroom"
  }

Step 2: Tool "extract_contact_info"
  Agent: "I heard their name (John), phone (none explicitly, 
          but I could ask), and address (123 Main St, Campbell River)"
  
  OUTPUT: {
    "name": "John Smith",
    "phone": "250-555-1234",  # Usually given during call
    "address": "123 Main St, Campbell River, BC V9W 2B1"
  }

Step 3: Tool "store_lead_in_database"
  Agent: "Now I'll save this to the database so it's permanent."
  
  OUTPUT: {
    "job_id": "job_abc123xyz",
    "saved": True
  }

Step 4: Tool "notify_contractor_dashboard"
  Agent: "Alert the contractor immediately!"
  
  OUTPUT: {
    "notification_sent": True
  }


TIME 0:10 — CONTRACTOR'S DASHBOARD UPDATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 Contractor (owner) sees in browser:

  ┌─────────────────────────────────────────────────┐
  │  COMOX VALLEY PLUMBING — INCOMING JOBS          │
  ├─────────────────────────────────────────────────┤
  │  🚨 EMERGENCY — John Smith                       │
  │     Problem: Toilet overflowing                 │
  │     Address: 123 Main St, Campbell River        │
  │     Called: Just now                            │
  │                                                  │
  │  [Review]  [Generate Quote]  [Schedule]         │
  └─────────────────────────────────────────────────┘

Contractor reads and thinks: "Yep, that's the right info."


TIME 0:15 — CONTRACTOR CLICKS "GENERATE QUOTE"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(This triggers NEXT WEEK'S AGENT: Quote Generation Agent)

🤖 Quote Agent thinks: "Okay, a toilet overflow emergency in 
                      Campbell River. Let me make a quote."

Step 1: Tool "lookup_pricing_history"
  Agent: "I looked at our past plumbing emergency jobs. 
          Average: $400, Range: $250–$650"
  
  OUTPUT: {
    "avg_price": 400,
    "min_price": 250,
    "max_price": 650
  }

Step 2: Tool "estimate_labor_hours"
  Agent: "Toilet overflow typically takes 1.5–2 hours 
          (shut off water, remove, clean, reinstall)"
  
  OUTPUT: {
    "estimated_hours": 1.5,
    "hourly_rate": 95
  }

Step 3: Tool "calculate_total_cost"
  Agent: "1.5 hrs × $95 = $142.50 labor
          + $45 parts (new toilet seal kit)
          + $75 dispatch fee
          = $262.50 subtotal
          × 1.05 (tax)
          = $275.63 total"
  
  OUTPUT: {
    "labor": 142.50,
    "parts": 45.00,
    "dispatch": 75.00,
    "subtotal": 262.50,
    "tax": 13.13,
    "total": 275.63
  }

Step 4: Tool "format_quote_document"
  Agent: "Creating a professional PDF quote..."
  
  OUTPUT: {
    "pdf_url": "quotes/job_abc123xyz_quote.pdf",
    "ready_to_send": True
  }

Step 5: Tool "send_quote_to_owner_for_approval"
  Agent: "Notifying contractor to review before sending to customer"
  
  OUTPUT: {
    "approval_needed": True,
    "quote_id": "quote_abc123xyz"
  }


TIME 0:20 — CONTRACTOR REVIEWS QUOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 Dashboard updates:

  ┌─────────────────────────────────────────────────┐
  │  QUOTE READY FOR REVIEW                         │
  ├─────────────────────────────────────────────────┤
  │  Job: John Smith (Toilet Overflow)              │
  │                                                  │
  │  Labor (1.5 hrs @ $95/hr):    $142.50           │
  │  Parts (toilet seal kit):     $45.00            │
  │  Dispatch Fee:                $75.00            │
  │  Subtotal:                    $262.50           │
  │  Tax (5%):                    $13.13            │
  │  ────────────────────────────────────           │
  │  TOTAL:                       $275.63           │
  │                                                  │
  │  Looks good? [Edit] [Approve & Send]            │
  └─────────────────────────────────────────────────┘

Contractor: "That's fair for an emergency. Send it."


TIME 0:22 — CONTRACTOR CLICKS "APPROVE & SEND"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quote Agent sends SMS to customer:

  📱 John's Phone:
  "Hi John! Your emergency plumbing quote is ready:
   $275.63 (toilet repair + seal kit)
   Ready today? Reply YES or call us."


TIME 0:30 — CUSTOMER REPLIES "YES"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(This triggers NEXT WEEK'S AGENT: Scheduling Agent)

🤖 Scheduling Agent thinks: "Customer accepted quote. 
                           Book the earliest available tech."

Step 1: Tool "get_available_technicians"
  Agent: "Who's available for plumbing TODAY?"
  
  OUTPUT: [
    {"name": "Bob", "available": True, "rating": 4.8},
    {"name": "Alice", "available": True, "rating": 4.6}
  ]

Step 2: Tool "calculate_travel_time"
  Agent: "Bob is in Courtenay (10 km from Campbell River)
          = 12 minutes drive. Alice is in Campbell River 
          = 5 minutes drive. Go with Alice."
  
  OUTPUT: {
    "selected_tech": "Alice",
    "travel_time": 5,
    "arrival_time": "2:15 PM"
  }

Step 3: Tool "create_appointment_slot"
  Agent: "Block Alice's calendar for 2:15 PM - 4:15 PM 
          (1.5 hr job + buffer)"
  
  OUTPUT: {
    "appointment_id": "appt_xyz789",
    "confirmed": True
  }

Step 4: Tool "send_appointment_confirmation"
  Agent: "Notify customer and technician"
  
  📱 John's Phone:
  "Hi John! Your plumber Alice will arrive 
   at 2:15 PM today. Address: 123 Main St.
   She has 4.8★ rating. See you soon!"

  📱 Alice's Phone (Tech App):
  "NEW JOB: Toilet overflow at 123 Main St
   Customer: John Smith
   Arrival: 2:15 PM (5 min drive)
   Est. Time: 1.5 hrs
   Quote Approved: $275.63
   [Navigate] [Accept]"


TIME 2:15 PM — ALICE ARRIVES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Alice completes work, takes photo, gets customer to sign on her tablet.
Job data syncs to database:

DATABASE UPDATE:
  jobs.status = "completed"
  jobs.actual_duration_hours = 1.3
  jobs.completion_notes = "Replaced flush valve, customer happy"
  jobs.customer_signature_url = "signatures/john_smith_123main.jpg"


TIME 2:45 PM — BILLING AGENT RUNS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Next week's 4th agent triggers)

🤖 Billing Agent thinks: "Job is done. Generate invoice."

Step 1: Tool "get_job_completion_data"
  Agent: "Reads: 1.3 hours actual, no extra parts used"
  
  OUTPUT: {
    "actual_hours": 1.3,
    "parts_cost": 0,
    "labor_rate": 95
  }

Step 2: Tool "calculate_final_invoice"
  Agent: "1.3 hrs × $95 = $123.50 labor
          + $0 parts (seal kit was included in quote)
          + $75 dispatch
          = $198.50 (UNDER the $275.63 quote!)"
  
  OUTPUT: {
    "total_due": 198.50,
    "difference": -77.13  # Under quote
  }

Step 3: Tool "generate_invoice_pdf"
  Agent: "Creating invoice..."

Step 4: Tool "send_invoice_to_customer"
  Agent: "Sending to John"
  
  📱 John's Phone:
  "Hi John! Thanks for choosing us. Your final invoice: $198.50
   (we came in under the quote!). Pay here: [link]
   
   Rate your experience: [Rate Alice]"


TIME AFTER JOB — CUSTOMER PAYS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
John clicks payment link, pays $198.50.

DATABASE UPDATE:
  payments.invoice_id = invoice_id
  payments.amount = 198.50
  payments.status = "paid"
  jobs.status = "paid"


TIME END OF DAY — CONTRACTOR CHECKS DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 Dashboard summary:

  ┌─────────────────────────────────────────────────┐
  │  TODAY'S SUMMARY                                │
  ├─────────────────────────────────────────────────┤
  │  ✅ 1 Job Completed                             │
  │  💰 Revenue: $198.50                            │
  │  ⏱️  Time Spent: 1.3 hrs actual (0.3 hrs saved) │
  │  ⭐ Customer Rating: (pending)                  │
  │                                                  │
  │  Without AI: ~3 hours manual work               │
  │  With AI: ~5 minutes approval work              │
  │                                                  │
  │  Time Saved Today: 2h 55m                       │
  │  Value of Time Saved: ~$280 @ $95/hr            │
  └─────────────────────────────────────────────────┘

CONTRACTOR THINKS: "This platform saved me 3 hours today 
                   on one job. If I get 5 jobs per week,
                   that's 15 hours saved = $1,425/week 
                   = $74K/year!"


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Key Insights

### 1. **Agents Run Automatically (After Owner Approves)**
Once contractor approves the quote, everything else runs without them:
- Agent books appointment
- Agent sends SMS to customer
- Agent sends job card to tech
- Agent tracks payment
- Agent sends reminders

### 2. **Owner Only Does These Actions**
- Click "Review" (optional, usually auto-correct)
- Click "Generate Quote"
- Click "Approve & Send"
- View dashboard (real-time updates)

### 3. **Customer Experience is Seamless**
- 1 call to book
- SMS confirmation
- Tech arrives on time
- Pay online
- Rate experience

---

## The Database Row by Row

After this job completes, here's what's in your database:

```sql
-- JOBS TABLE
SELECT * FROM jobs WHERE id = 'job_abc123xyz';
┌──────────────┬──────────────┬────────────┬──────────────┬──────────────┬─────────────┬───────────────┐
│ id           │ customer_name│ phone      │ address      │ service_type │ urgency     │ status        │
├──────────────┼──────────────┼────────────┼──────────────┼──────────────┼─────────────┼───────────────┤
│ job_abc123xyz│ John Smith   │ 250-555-123│ 123 Main St  │ plumbing     │ emergency   │ paid          │
└──────────────┴──────────────┴────────────┴──────────────┴──────────────┴─────────────┴───────────────┘

-- QUOTES TABLE
SELECT * FROM quotes WHERE job_id = 'job_abc123xyz';
┌──────────────┬──────────────┬─────────┬──────────┬───────┬──────────┐
│ id           │ job_id       │ labor   │ parts    │ total │ status   │
├──────────────┼──────────────┼─────────┼──────────┼───────┼──────────┤
│ quote_...    │ job_abc123xyz│ $142.50 │ $45.00  │ $275.6│ approved │
└──────────────┴──────────────┴─────────┴──────────┴───────┴──────────┘

-- APPOINTMENTS TABLE
SELECT * FROM appointments WHERE job_id = 'job_abc123xyz';
┌──────────────┬──────────┬───────────┬────────────┬──────┐
│ id           │ tech_name│ date      │ time       │ status│
├──────────────┼──────────┼───────────┼────────────┼──────┤
│ appt_xyz789  │ Alice    │ 2024-09-02│ 2:15 PM    │ completed │
└──────────────┴──────────┴───────────┴────────────┴──────┘

-- INVOICES TABLE
SELECT * FROM invoices WHERE job_id = 'job_abc123xyz';
┌──────────────┬──────────────┬────────┬───────┐
│ id           │ job_id       │ total  │ paid  │
├──────────────┼──────────────┼────────┼───────┤
│ invoice_...  │ job_abc123xyz│ $198.50│ yes   │
└──────────────┴──────────────┴────────┴───────┘

-- PAYMENTS TABLE
SELECT * FROM payments WHERE invoice_id = 'invoice_...';
┌──────────────┬──────────────┬────────┬──────────┐
│ id           │ invoice_id   │ amount │ date     │
├──────────────┼──────────────┼────────┼──────────┤
│ pay_...      │ invoice_...  │ $198.50│ 2024-09-02│
└──────────────┴──────────────┴────────┴──────────┘
```

---

## Does This Make Sense?

✅ Contractor gets call → AI extracts info → Dashboard notification
✅ Contractor approves quote → AI sends to customer
✅ Customer says yes → AI schedules + notifies tech
✅ Tech completes → AI generates invoice
✅ Customer pays → Dashboard shows revenue

**All of that happens automatically. Contractor just approves once.**

This is the power of agents.
