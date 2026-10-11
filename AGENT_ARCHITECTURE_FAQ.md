# Agent Architecture: Do We Need More Agents?

**Question:** Do we need more AI agents for parts database, invoice OCR, reminders, etc.?

**Answer:** No. We scale by adding tools to existing agents, not by adding more agents.

---

## Current Architecture: 4 Core Agents

### Agent 1: Lead Capture Agent
**Runs on:** Incoming phone call  
**Job:** Answer phone, capture customer info, extract job details  
**Output:** Structured lead data → Save to database

**Current tools:**
```
Tool 1: classify_service_type (plumbing/HVAC/electrical?)
Tool 2: assess_urgency (emergency/routine?)
Tool 3: extract_address_and_contact (where/who?)
Tool 4: save_lead (store in database)
```

---

### Agent 2: Quote Generation Agent
**Runs on:** Tech at job site  
**Job:** Generate professional quote based on parts used  
**Output:** PDF invoice for customer approval

**Current tools:**
```
Tool 1: list_parts_from_database (search for PVC pipe, etc.)
Tool 2: calculate_cost (qty × retail price + labor)
Tool 3: apply_markup (standard 30% or emergency 50%)
Tool 4: generate_invoice_pdf (create professional quote)
Tool 5: send_to_customer (email/SMS/iPad display)
```

---

### Agent 3: Scheduling Agent
**Runs on:** Dashboard (Bob or admin)  
**Job:** Optimize tech routes, schedule jobs  
**Output:** Calendar of all jobs for all techs

**Current tools:**
```
Tool 1: get_all_pending_jobs (list of jobs to schedule)
Tool 2: get_tech_availability (which techs free when?)
Tool 3: calculate_travel_time (Google Maps API)
Tool 4: optimize_route (shortest route for multiple jobs)
Tool 5: send_calendar_to_techs (SMS/email with schedule)
```

---

### Agent 4: Billing Agent
**Runs on:** End of job or manually  
**Job:** Create final invoice, collect payment, update QB  
**Output:** Paid invoice, QB bill synced

**Current tools:**
```
Tool 1: get_job_details (from database)
Tool 2: get_quote_from_job (if used)
Tool 3: calculate_final_total (parts + labor + tax)
Tool 4: create_payment_link (Stripe/PayPal)
Tool 5: sync_to_quickbooks (create QB bill)
Tool 6: record_payment (mark paid in QB)
```

---

## New Features: Enhanced Tools, Not New Agents

### Feature 1: Parts Database
**Where it fits:** Enhances Quote Generation Agent

**New tools added to Quote Agent:**
```
Tool 1 (EXISTING): list_parts_from_database
       ↓ ENHANCED with parts pricing
Tool 2 (NEW): search_parts_by_keyword ("pvc 3/4")
Tool 3 (NEW): get_bulk_pricing (if ordering 50+ units)
Tool 4 (NEW): check_inventory (how many in stock?)
Tool 5 (NEW): auto_reorder_if_low (trigger reorder if <5 units)
Tool 6 (NEW): get_supplier_info (which supplier cheapest?)
```

**Agent unchanged:** Quote Generation Agent just calls more tools

---

### Feature 2: Call Forwarding with Existing Number
**Where it fits:** Enhances Lead Capture Agent

**New tools added to Lead Capture Agent:**
```
Tool 1 (EXISTING): extract_address_and_contact
       ↓ ENHANCED to handle call forwarding
Tool 2 (NEW): identify_caller_original_number ("250-555-1234")
Tool 3 (NEW): map_to_hermes_forwarding_number ("Twilio number 🔄")
Tool 4 (NEW): match_to_contractor (which Bob is this for?)
Tool 5 (NEW): transcribe_call (if needed)
```

**Agent unchanged:** Lead Capture Agent just has more context

---

### Feature 3: Supplier Invoice OCR
**Where it fits:** Enhances Billing Agent (NEW WORKFLOW)

**New tools added to Billing Agent:**
```
Tool 1 (EXISTING): sync_to_quickbooks
Tool 2 (NEW): process_invoice_upload (Bob uploads photo/PDF)
Tool 3 (NEW): run_ocr_extraction (AWS Textract or Tesseract)
Tool 4 (NEW): parse_invoice_data (extract vendor, amount, date)
Tool 5 (NEW): validate_extraction (>90% confidence?)
Tool 6 (NEW): sync_supplier_invoice_to_qb (create QB Bill)
Tool 7 (NEW): schedule_payment_reminder (3 days before due)
```

**Agent unchanged:** Billing Agent now handles both customer invoices AND supplier invoices

---

### Feature 4: Payment Reminders
**Where it fits:** NOT an agent—a background scheduler

**This is not an agent, it's a background job:**
```
Every day at 9:00 AM:
  - Check all unpaid invoices
  - If due in 3 days: Send SMS reminder
  - If due today: Send SMS alert
  - If overdue: Send SMS warning
  
No AI reasoning needed—just scheduled tasks
Could be cron job or Celery task, not an agent
```

---

## Architecture Diagram: Agents + Tools

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT 1: LEAD CAPTURE                                       │
│ Trigger: Incoming phone call                                │
│ Tools: classify_service, assess_urgency, extract_contact,   │
│        + NEW: identify_forwarding, match_to_contractor      │
│ Output: Structured lead → Database                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ AGENT 2: QUOTE GENERATION                                   │
│ Trigger: Tech at job site                                   │
│ Tools: list_parts, calculate_cost, apply_markup,            │
│        generate_invoice, send_to_customer                   │
│        + NEW: search_parts, get_bulk_pricing,               │
│              check_inventory, auto_reorder                  │
│ Output: Professional quote (PDF) → Customer                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ AGENT 3: SCHEDULING                                         │
│ Trigger: Dashboard or API call                              │
│ Tools: get_pending_jobs, get_tech_availability,             │
│        calculate_travel, optimize_route, send_calendar      │
│ Output: Optimized schedule → Techs                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ AGENT 4: BILLING                                            │
│ Trigger: End of job OR Bob uploads supplier invoice         │
│ Tools: get_job_details, calculate_total, create_payment,    │
│        sync_to_qb, record_payment                           │
│        + NEW: process_invoice_upload, run_ocr,              │
│              parse_invoice, validate_extraction,             │
│              sync_supplier_invoice_to_qb,                    │
│              schedule_payment_reminder                       │
│ Output: Paid invoice → QB + Payment reminder → SMS          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ BACKGROUND SCHEDULER (NOT an agent)                         │
│ Daily: Check invoice due dates                              │
│        Send reminders (no AI, just scheduling)              │
│ Output: SMS to contractors                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Why More Tools, Not More Agents?

### What is an Agent?
```
Agent = AI that chains tools together to solve a problem
        Reads context → Decides which tool to call → 
        Reads result → Decides next step → 
        Calls next tool → Repeat until done

Example:
  Agent receives: "I need a quote"
  Thinks: "I need to get parts list"
  Calls: list_parts()
  Gets: [PVC Pipe, Elbow, Cement]
  Thinks: "Now I need to get prices"
  Calls: get_bulk_pricing(PVC_Pipe)
  Gets: $42 (1-10) or $39.90 (11-50)
  Etc.
```

### What is a Tool?
```
Tool = Single function agent can call
       No thinking, just execute

Examples:
  - search_parts ("pvc")
  - get_price (part_id)
  - sync_to_qb (bill_data)
  - send_sms (phone, message)
```

### Why Agents Scale with More Tools, Not More Agents

**Wrong approach (adds complexity):**
```
Agent 1: Lead Capture
Agent 2: Quote Generation
Agent 3: Scheduling
Agent 4: Billing
Agent 5: Parts Manager ← NEW AGENT
Agent 6: Invoice OCR Manager ← NEW AGENT
Agent 7: Payment Reminder Manager ← NEW AGENT

Total: 7 agents all running independently
Problem: Coordination is hard, redundant processing, expensive
```

**Right approach (simpler, faster, cheaper):**
```
Agent 1: Lead Capture (+2 new tools)
Agent 2: Quote Generation (+6 new tools) ← handles parts
Agent 3: Scheduling (unchanged)
Agent 4: Billing (+6 new tools) ← handles invoices + reminders

Total: 4 agents, ~20 tools total
Better: Coordinated, efficient, cheaper to run
```

---

## Tool Inventory: Current vs After All Features

### Current (Week 1)
```
Agent 1 (Lead Capture): 4 tools
Agent 2 (Quote Generation): 5 tools
Agent 3 (Scheduling): 5 tools
Agent 4 (Billing): 6 tools

Total: 20 tools
```

### After All Features (Week 4)
```
Agent 1 (Lead Capture): 4 + 2 new = 6 tools
Agent 2 (Quote Generation): 5 + 6 new = 11 tools (parts DB)
Agent 3 (Scheduling): 5 tools (unchanged)
Agent 4 (Billing): 6 + 7 new = 13 tools (invoices + QB)

Total: 35 tools
```

### Cost Comparison
```
Cost to run one agent call: ~$0.001 (LangChain + OpenAI)

Current: 4 agents × ~10 calls per workflow = 40 calls/workflow
Cost: $0.04 per workflow

If we had 7 agents: 7 agents × ~8 calls each = 56 calls/workflow
Cost: $0.056 per workflow (+40% expensive)

Plus: 7 agents = more complex, harder to debug, slower
```

---

## How Each Feature Integrates

### Parts Database (Feature 1)
**Added to:** Quote Generation Agent
**New tools:**
```
def search_parts(keyword):
    """Search parts database by keyword"""
    # SELECT * FROM parts WHERE name LIKE '%keyword%'
    # Return: List of parts with prices

def get_bulk_pricing(part_id, quantity):
    """Get price for bulk order"""
    # If ordering 50+ units, apply bulk discount
    # Return: Adjusted price

def check_inventory(part_id):
    """Check stock level"""
    # SELECT stock FROM parts WHERE id = part_id
    # Return: Current stock, reorder point

def auto_reorder_if_low(part_id):
    """Trigger reorder if stock low"""
    # If current_stock < reorder_point, create PO
    # Return: Order confirmation
```

**Agent flow:**
```
Tech: "Generate quote for PVC pipe job"
Agent: Calls search_parts("pvc")
       Gets: [PVC Pipe 3/4", PVC Elbow, PVC Cement]
Agent: Calls get_bulk_pricing("PVC Pipe 3/4", qty=2)
       Gets: $42/unit (standard, no bulk discount for qty=2)
Agent: Calls check_inventory("PVC Pipe 3/4")
       Gets: 12 units in stock
Agent: Calls calculate_cost()
       Includes parts + labor + tax
Agent: Calls generate_invoice()
       Returns: Professional PDF quote
Agent: Calls send_to_customer()
       SMS/email to customer
Done in <5 seconds
```

---

### Supplier Invoice OCR (Feature 2)
**Added to:** Billing Agent (new workflow)
**New tools:**
```
def process_invoice_upload(file_path):
    """Accept photo/PDF from Bob"""
    # Save to AWS S3
    # Return: S3 path + file info

def run_ocr_extraction(file_path):
    """Extract text from image/PDF"""
    # AWS Textract or Tesseract
    # Return: Raw text + confidence scores

def parse_invoice_data(raw_text):
    """Extract structured data from OCR text"""
    # Vendor name, invoice #, date, due date, items, total
    # Return: Structured dict with confidence scores

def validate_extraction(parsed_data):
    """Check if confidence >90%"""
    # If low confidence, flag for manual review
    # Return: Approval or rejection recommendation

def sync_supplier_invoice_to_qb(parsed_data):
    """Create QB Bill from parsed invoice"""
    # QB API: Create Bill with vendor, items, total
    # Return: QB Bill ID

def schedule_payment_reminder(invoice_id, due_date):
    """Create reminder tasks"""
    # Add to reminder table: 3 days before, on due date
    # Return: Reminder IDs
```

**Agent flow:**
```
Bob: Takes photo of Home Depot invoice
     Uploads to Hermes

Agent: Calls process_invoice_upload()
       Gets: S3 path
Agent: Calls run_ocr_extraction()
       Gets: Raw text (confidence: 98%)
Agent: Calls parse_invoice_data()
       Gets: {vendor: "Home Depot", invoice#: "...", total: $269.64, due: Oct 1}
Agent: Calls validate_extraction()
       Gets: Approval (confidence >90%)
Agent: Calls sync_supplier_invoice_to_qb()
       Gets: QB Bill ID created
Agent: Calls schedule_payment_reminder()
       Gets: Reminders scheduled for Sept 28, Sept 30
Done in <10 seconds
```

---

### Payment Reminders (Feature 3)
**NOT an agent—a background scheduler**

**Why it's not an agent:**
- No AI reasoning needed
- Just "if today == reminder_date, send SMS"
- Scheduled job, not reactive

**Implementation:**
```python
# Background scheduler (runs daily)
def send_payment_reminders():
    """Cron job or Celery task"""
    
    # Get all unpaid invoices
    unpaid = SupplierInvoice.filter(payment_status='Unpaid')
    
    for invoice in unpaid:
        # Check if reminder due
        if invoice.due_date - today == 3:  # 3 days before
            send_sms(invoice.contractor, f"Payment due in 3 days: {invoice.total}")
        
        elif invoice.due_date == today:  # On due date
            send_sms(invoice.contractor, f"⚠️ DUE TODAY: {invoice.total}")
        
        elif invoice.due_date < today:  # Overdue
            send_sms(invoice.contractor, f"🚨 OVERDUE: {invoice.total} was due {overdue_days} days ago")
```

**Not an AI agent:**
- No tool chaining
- No decision-making
- Just executing a schedule

---

## Summary: Agent Architecture

| Component | Purpose | # of Agents | # of Tools |
|-----------|---------|-----------|-----------|
| Lead Capture | Answer phone, extract info | 1 | 6 |
| Quote Generation | Generate professional quotes (+ parts DB) | 1 | 11 |
| Scheduling | Optimize tech routes | 1 | 5 |
| Billing | Create invoices (+ supplier invoices + QB) | 1 | 13 |
| Payment Reminders | Send scheduled SMS reminders | 0 (scheduler) | N/A |
| **TOTAL** | | **4** | **35** |

---

## Cost Analysis: Agents vs Tools

### Current System (4 agents, 20 tools)
```
Per workflow execution:
  - Agent 1 runs: 1 agent call + 4 tool calls = 5 calls
  - Agent 2 runs: 1 agent call + 5 tool calls = 6 calls
  - Agent 4 runs: 1 agent call + 6 tool calls = 7 calls
  Total: 18 calls per workflow
  Cost: 18 × $0.001 = $0.018

Runs per month: ~1,000 workflows
Monthly cost: $18
Annual cost: $216
```

### If We Had 7 Agents Instead
```
Per workflow execution:
  - Agent 1: 5 calls
  - Agent 2: 6 calls
  - Agent 3: 6 calls
  - Agent 4: 7 calls
  - Agent 5 (Parts): 3 calls (redundant)
  - Agent 6 (Invoice): 4 calls (redundant)
  - Agent 7 (Reminders): 2 calls (redundant)
  Total: 33 calls per workflow (+83% more!)
  Cost: 33 × $0.001 = $0.033

Monthly cost: $33 (+83% more expensive)
Annual cost: $396 (+$180 wasted)
```

**More agents = more expensive and more complex.**

---

## Scaling as We Grow

### As You Acquire More Contractors
```
Week 4: 5 contractors
  - 50 phone calls/week
  - 40 quotes generated/week
  - 20 invoices entered/week
  
Week 8: 15 contractors
  - 150 phone calls/week
  - 120 quotes generated/week
  - 60 invoices entered/week

Scaling: Agent calls scale with usage
         But same 4 agents handle everything
         Just process more tool calls
```

### If We Add New Verticals (Phase 2: Dealerships)

**Option 1 (Wrong): Add new agents for dealerships**
```
Agent 1: Plumbing Lead Capture
Agent 2: Plumbing Quote Generation
Agent 3: Dealership Lead Capture ← NEW
Agent 4: Dealership Quote Generation ← NEW
Agent 5: Dealership Financing ← NEW
Agent 6: Dealership Inventory ← NEW

Problem: Duplicate logic, hard to maintain
```

**Option 2 (Right): Extend existing agents with new tools**
```
Agent 1: Lead Capture (+ tool: detect_industry)
         Can handle both plumbing and dealerships

Agent 2: Quote Generation (+ tools: get_dealership_inventory, check_financing_options)
         Can generate both job quotes and car quotes

Same 4-agent architecture, more tools
Cleaner, cheaper, easier to maintain
```

---

## Conclusion

**Do you need more agents?**

**No.**

**Why?**
1. **Scalability:** Agents scale by adding tools, not by adding more agents
2. **Cost:** More agents = more API calls = higher costs
3. **Complexity:** More agents = harder to coordinate and debug
4. **Architecture:** LangChain agents are designed to chain multiple tools together
5. **Performance:** One agent with 10 tools is faster than 10 agents with 1 tool each

**What you need:**
- 4 core agents (unchanged)
- 35 tools total (growing from 20)
- 1 background scheduler (for reminders, not an agent)

**Timeline:**
- Week 1: 4 agents, 20 tools ✓
- Week 2-4: 4 agents, 35 tools (just add tools to existing agents)
- Phase 2: 4 agents, 50+ tools (add dealership-specific tools)

**Bottom line:** You scale Hermes by enriching the tool ecosystem, not by creating more agents. This keeps the system simple, fast, and cheap.

