# Deployment Architecture & Model Selection: Claude vs DeepSeek

**Questions:**
1. How do you deploy agents to various contractors?
2. Should you use Claude or DeepSeek instead?

**Answers:**
1. Deploy via SaaS (cloud-hosted), not locally installed
2. Use Claude for now, consider DeepSeek later for cost optimization

---

## Part 1: Agent Deployment Architecture

### How NOT to Deploy (Wrong Way)

```
WRONG: Install locally on each contractor's computer

  Bob's Computer:
    ├── Hermes backend (FastAPI)
    ├── Database (PostgreSQL)
    ├── LangChain agents
    ├── All configuration
    └── API keys (security risk!)
  
  Problems:
    ❌ Bob has to install software (friction)
    ❌ Database on Bob's computer (security risk)
    ❌ Hard to update (each Bob gets update separately)
    ❌ Hard to support (each installation is different)
    ❌ You can't see what's happening (no visibility)
    ❌ Bob's internet goes down = no service
    ❌ Scaling: 100 contractors = 100 separate installations
```

### How to Deploy (Right Way: SaaS)

```
CORRECT: Cloud-hosted SaaS (all contractors share same backend)

  ☁️ HERMES CLOUD (AWS)
    ├── FastAPI Backend (1 instance)
    ├── PostgreSQL Database (shared, secure)
    ├── LangChain Agents (4 agents serving all contractors)
    ├── All API keys (secure in AWS Secrets Manager)
    └── Monitoring & logging
  
  Bob's Computer:
    ├── Web browser (Chrome/Safari)
    │   └── Opens: https://hermes.app
    │       ├── Dashboard
    │       ├── Upload invoice
    │       ├── View reminders
    │       └── Mark paid
    │
    └── Smartphone (iOS/Android)
        └── Hermes mobile app
            ├── Phone notifications
            ├── Take invoice photo
            ├── View schedule
            └── Accept/reject quotes
  
  Benefits:
    ✅ Bob just opens browser (no installation)
    ✅ Automatic updates (everyone gets latest version)
    ✅ Centralized database (better security)
    ✅ You have full visibility (monitoring, logs)
    ✅ Easy support (you see exactly what's happening)
    ✅ Scaling: 1 backend serves 100 contractors
    ✅ High availability (redundant servers)
    ✅ Automatic backups (no data loss risk)
```

---

## SaaS Deployment Architecture

### Cloud Stack (AWS Recommended)

```
┌──────────────────────────────────────────────────────────────┐
│                      INTERNET / BROWSERS                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ CLOUDFLARE CDN (Front layer)                           │  │
│  │ - Caches static content                                │  │
│  │ - DDoS protection                                      │  │
│  │ - Fast global delivery                                 │  │
│  └────────────────────────────────────────────────────────┘  │
│                            ↓                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ AWS APPLICATION LOAD BALANCER                          │  │
│  │ - Routes traffic to multiple backend instances         │  │
│  │ - Health checks                                        │  │
│  │ - SSL/TLS termination                                  │  │
│  └────────────────────────────────────────────────────────┘  │
│                            ↓                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ AWS ECS (Elastic Container Service)                    │  │
│  │ Container 1: FastAPI Backend (Port 8000)               │  │
│  │   ├── Lead Capture Agent                               │  │
│  │   ├── Quote Generation Agent                           │  │
│  │   ├── Scheduling Agent                                 │  │
│  │   └── Billing Agent                                    │  │
│  │                                                        │  │
│  │ Container 2: FastAPI Backend (Port 8000)               │  │
│  │ Container 3: FastAPI Backend (Port 8000)               │  │
│  │ [Multiple instances for high availability]             │  │
│  │                                                        │  │
│  │ Auto-scaling: 2-10 instances based on demand           │  │
│  └────────────────────────────────────────────────────────┘  │
│                            ↓                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ AWS RDS (PostgreSQL Database)                          │  │
│  │ - Multi-AZ (automatic failover)                        │  │
│  │ - Automated backups (7 days retention)                 │  │
│  │ - Read replicas (for scaling reads)                    │  │
│  │ - Encryption at rest                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                            ↓                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ AWS S3 (File Storage)                                  │  │
│  │ - Invoice images/PDFs                                  │  │
│  │ - Backups                                              │  │
│  │ - Lifecycle policies (automatic archival)              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ AWS Secrets Manager                                    │  │
│  │ - API keys (Twilio, OpenAI/DeepSeek, QB)              │  │
│  │ - Database credentials                                 │  │
│  │ - All encrypted                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ AWS CloudWatch                                         │  │
│  │ - Logs from all containers                             │  │
│  │ - Metrics (CPU, memory, requests)                      │  │
│  │ - Alerts (if something goes wrong)                     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Background Services                                    │  │
│  │ - Payment reminder scheduler (Celery)                  │  │
│  │ - Invoice processing queue                             │  │
│  │ - QB sync worker                                       │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## How Contractors Access Hermes

### Access Method 1: Web Dashboard (Primary)

```
Bob opens browser → https://hermes.app

1. Login (email + password)
   └── Authenticates against contractors table
   
2. Dashboard (what contractors see)
   ├── Today's jobs (list)
   ├── Pending quotes (waiting for approval)
   ├── Upcoming payments (invoices due soon)
   ├── Unpaid invoices (what's owed to suppliers)
   └── Quick actions
       ├── [Upload Invoice]
       ├── [View Schedule]
       ├── [View Payments]

3. Nav Menu
   ├── Dashboard (home)
   ├── Jobs (active, completed, historical)
   ├── Quotes (pending, sent, accepted)
   ├── Invoices
   │   ├── Customer Invoices (Bob created)
   │   ├── Supplier Invoices (Bob received)
   ├── Payments (received, owed)
   ├── Reports (revenue, profit, aging AR/AP)
   ├── Settings (profile, QB connection, API keys)
   └── Support (help, contact us)
```

### Access Method 2: Mobile App (Native iOS/Android)

```
Bob opens Hermes app on phone

1. Notifications (push)
   ├── "New customer call received: Emergency at 123 Main St"
   ├── "Payment reminder: Home Depot due in 3 days ($269.64)"
   ├── "Invoice ready: Customer approved $590.32 quote"
   └── "New job scheduled for you: Wed 2 PM - Parker job"

2. Quick Actions (home screen)
   ├── [Upload Invoice] → Take photo, OCR, auto-sync to QB
   ├── [View Today] → All jobs scheduled today
   ├── [Accept Quote] → Tech approves job quote
   ├── [Mark Paid] → Record payment for invoice

3. Full access to web features (responsive design)
```

---

## How Multi-Tenancy Works

### Data Isolation (Contractor Separation)

```
One PostgreSQL database serves ALL contractors

But data is completely isolated:

contractors table:
  id | name | email | phone | qb_realm_id | qb_token | subscription_status
  1  | Bob's Plumbing | bob@... | 250-555-1234 | QB123 | active
  2  | Sarah's HVAC | sarah@... | 250-555-5678 | QB456 | active
  3  | Mike's Electric | mike@... | 250-555-9012 | QB789 | active

leads table:
  id | contractor_id | customer_name | phone | service_type
  10 | 1 | John Smith | 250-555-1111 | plumbing
  11 | 2 | Jane Doe | 250-555-2222 | hvac
  12 | 1 | Bob Johnson | 250-555-3333 | plumbing

When Bob logs in:
  ✓ Can see: leads where contractor_id = 1
  ✓ Cannot see: leads where contractor_id = 2 or 3

When Sarah logs in:
  ✓ Can see: leads where contractor_id = 2
  ✓ Cannot see: leads where contractor_id = 1 or 3

Data isolation enforced at database level AND application level
```

### Security: Row-Level Security (RLS)

```sql
-- PostgreSQL Row-Level Security Policy
-- Ensures Bob can only see his own data

CREATE POLICY lead_access ON leads
  USING (contractor_id = current_contractor_id());
  
When Bob's request comes in:
  current_contractor_id() = 1
  SELECT * FROM leads
  → Only returns leads where contractor_id = 1

If Bob tries to hack:
  SELECT * FROM leads WHERE contractor_id = 2
  → PostgreSQL enforces policy
  → Returns nothing (even if SQL is valid)
```

---

## Contractor Onboarding Flow

```
1. BOB SIGNS UP
   ├── Email: bob@plumbing.com
   ├── Password: [secure]
   ├── Business name: Bob's Plumbing
   ├── Phone: 250-555-1234
   └── Location: Comox Valley, BC

2. HERMES SETS UP CONTRACTOR ACCOUNT
   ├── Creates contractor row
   ├── Creates empty QB connection
   ├── Creates empty Twilio number mapping
   └── Sends welcome email

3. BOB CONNECTS EXTERNAL SERVICES
   ├── Twilio: "I'll forward my 250-555-1234 to Hermes"
   │   └── Hermes records: forwarding_number = 250-555-1234
   │                       twilio_number = 250-555-HERMES
   │
   ├── QuickBooks: "Connect your QB account"
   │   └── OAuth flow: Bob logs into QB
   │       Hermes gets: qb_realm_id + qb_token
   │
   └── Stripe: "Enable payments"
       └── Bob enters Stripe API key
           (stored in AWS Secrets Manager)

4. BOB INVITES TECHS
   ├── Sarah (tech 1)
   │   └── Gets contractor_id = 1, role = "tech"
   ├── Mike (tech 2)
   │   └── Gets contractor_id = 1, role = "tech"
   └── Admin (Bob)
       └── Gets contractor_id = 1, role = "admin"

5. SYSTEM READY
   ├── Incoming calls to 250-555-1234 → Hermes
   ├── Quotes stored securely (only Bob, Sarah, Mike see)
   ├── QB syncs to Bob's QB account
   ├── Reminders sent to Bob's phone
   └── No data leakage (Sarah can't see other contractors)
```

---

## Cost of Cloud Deployment

### AWS Pricing (Monthly, for 50 Contractors)

```
Compute (ECS Fargate):
  - 3 container instances (2 CPU, 4GB RAM each)
  - ~500 requests/second capacity (overkill for 50 contractors)
  - Cost: $300-400/month

Database (RDS PostgreSQL):
  - db.t3.small (suitable for 50 contractors)
  - Multi-AZ (automatic failover)
  - Automated backups
  - Cost: $80-100/month

Storage (S3):
  - Invoice images/PDFs (~2GB for 50 contractors)
  - Cost: <$1/month

CDN (CloudFlare):
  - Free tier or $20/month (very cheap)

DNS, SSL, etc:
  - Cost: $10-20/month

Secrets Manager:
  - $0.40/secret × 5 secrets = $2/month

CloudWatch Logs:
  - Cost: $0.50-1/month (very cheap)

TOTAL: ~$400-520/month for 50 contractors

Per contractor: $8-10/month (infrastructure cost)
You charge: $500/month
Margin: $490/month per contractor (98%)
```

### Scaling Numbers

```
50 contractors:
  Revenue: 50 × $500 = $25K/month
  Infrastructure: $400-520/month
  Margin: $24,480/month

100 contractors:
  Revenue: 100 × $500 = $50K/month
  Infrastructure: $600-800/month (minimal increase)
  Margin: $49,200/month

500 contractors:
  Revenue: 500 × $500 = $250K/month
  Infrastructure: $2K-3K/month (still scales linearly)
  Margin: $247K-248K/month

Conclusion: Infrastructure cost is <2% of revenue
You can afford to be generous with uptime/features
```

---

## Contractor Isolation & Security

### What Each Contractor Sees

```
BOB (Contractor 1)
├── His own 3 techs (Sarah, Mike, Alex)
├── His own jobs (100+ this year)
├── His own quotes (50+ pending)
├── His own invoices (50+ sent, 30+ paid)
├── His own supplier invoices
├── His QB connection (private API key)
├── His payment history
└── His SMS notifications

Sarah CANNOT see:
  ❌ Other contractors' jobs
  ❌ Other contractors' invoices
  ❌ Other contractors' QB accounts
  ❌ Other contractors' phone numbers
  ❌ Other contractors' data

Enforced by:
  1. Database row-level security
  2. Application-level checks
  3. Authentication tokens (JWT)
```

### Security Measures

```
1. AUTHENTICATION
   - Email + Password (hashed with bcrypt)
   - 2FA (optional, recommended)
   - Session tokens (JWT, expires in 8 hours)

2. AUTHORIZATION
   - Role-based (admin, tech, viewer)
   - Row-level security (SQL policies)
   - API checks (every endpoint verifies contractor_id)

3. ENCRYPTION
   - Data in transit: HTTPS/TLS 1.3
   - Data at rest: AES-256 (AWS RDS encryption)
   - Secrets: AWS Secrets Manager

4. AUDIT TRAIL
   - Every action logged (who did what, when)
   - QB sync logs (for compliance)
   - Invoice processing logs

5. COMPLIANCE
   - PCI-DSS for payment processing (via Stripe)
   - GDPR (can export data, can delete account)
   - Canadian privacy laws (data stored in CA region)
```

---

## Part 2: Claude vs DeepSeek

### Current Choice: Claude (Anthropic)

**Why Claude for MVP:**

```
Pros:
  ✅ Excellent reasoning (needed for agents)
  ✅ Long context window (100K tokens)
  ✅ Reliable & stable (production-ready)
  ✅ Good tool-calling support
  ✅ Safety guardrails (won't generate bad advice)
  ✅ Cost: $3 per 1M input tokens, $15 per 1M output

Cons:
  ❌ More expensive than DeepSeek
  ❌ Slower responses (2-3 seconds vs 500ms)
  ❌ Needs API key (rate limiting)

Best for: MVP, accuracy critical, reasoning complex
```

### Alternative: DeepSeek-V3

**Why consider DeepSeek:**

```
Pros:
  ✅ Very cheap ($0.27 per 1M input tokens)
  ✅ Fast (500ms responses)
  ✅ Good reasoning (better than expected for cost)
  ✅ Open source (can run locally)
  ✅ No rate limiting (pay per token, no caps)
  ✅ Can fine-tune (train on your data)

Cons:
  ❌ Newer (less battle-tested)
  ❌ Tool-calling support is newer
  ❌ Smaller company (Alibaba)
  ❌ Less safety guardrails
  ❌ Chinese company (geopolitical concerns)
  ❌ Latency can be high (hosted in China)

Best for: Cost-sensitive, high volume, custom workflows
```

---

## Honest Comparison: Claude vs DeepSeek

| Factor | Claude | DeepSeek | Winner |
|--------|--------|----------|--------|
| **Reasoning quality** | Excellent | Good | Claude |
| **Cost per call** | $0.001-0.003 | $0.0001-0.0008 | DeepSeek (10x cheaper) |
| **Response speed** | 2-3 sec | 500ms | DeepSeek (5-6x faster) |
| **Tool-calling** | Excellent | Good | Claude |
| **Stability** | Production-proven | Newer | Claude |
| **Accuracy** | 95%+ | 90%+ | Claude |
| **Context window** | 100K tokens | 128K tokens | DeepSeek |
| **Can run locally** | No | Yes | DeepSeek |
| **Fine-tuning** | Limited | Supported | DeepSeek |
| **For MVP** | ✅ Best | Risky | Claude |
| **For Scale** | Expensive | Cheap | DeepSeek |

---

## Cost Analysis: 1,000 Contractors Using Agents

### Scenario: Agent calls per day per contractor

```
Lead Capture Agent (incoming call):
  - 1 call per contractor per day
  - Tokens: 500 input, 200 output

Quote Generation Agent (tech creates quote):
  - 2 calls per contractor per day
  - Tokens: 800 input, 400 output per call

Billing Agent (create invoice, sync QB):
  - 1 call per contractor per day
  - Tokens: 1000 input, 300 output

Total per contractor per day: 4 agent calls
Total for 1,000 contractors per day: 4,000 agent calls

Monthly: 4,000 × 30 = 120,000 agent calls
```

### Cost with Claude

```
Per agent call:
  Input: 500 tokens average × $0.003 per 1M = $0.0015
  Output: 300 tokens average × $0.015 per 1M = $0.0000045
  Total: ~$0.0016 per call

Monthly (120,000 calls):
  Claude cost: 120,000 × $0.0016 = $192/month

Annual: $2,304

For 1,000 contractors:
  Revenue: 1,000 × $500 = $500K/month
  Claude cost: $192/month
  Margin: $499,808/month

Claude cost as % of revenue: 0.04%
```

### Cost with DeepSeek

```
Per agent call:
  Input: 500 tokens × $0.0008 per 1M = $0.0000004
  Output: 300 tokens × $0.003 per 1M = $0.0000009
  Total: ~$0.00000130 per call

Monthly (120,000 calls):
  DeepSeek cost: 120,000 × $0.00000130 = $0.156/month

Annual: $1.87

For 1,000 contractors:
  Revenue: $500K/month
  DeepSeek cost: $0.156/month
  Margin: $499,999.84/month

DeepSeek cost as % of revenue: 0.00003%
```

### Comparison

```
Claude: $2,304/year (both MVP and scale)
DeepSeek: $19/year (10,000x cheaper)

But...

Claude (MVP):
  - Better reasoning (fewer errors)
  - Faster to market
  - Easier debugging
  - Production-proven

DeepSeek (Scale):
  - Much cheaper
  - Still accurate enough
  - Locally hostable
  - Fine-tunable
```

---

## Recommendation: Hybrid Strategy

### Phase 1: MVP (Weeks 1-12) - USE CLAUDE

```
WHY:
  - Accuracy critical (building trust with first customers)
  - Speed to market important
  - Debugging easier
  - Tool-calling mature

Cost: $192/month (negligible)
Impact: Better product, happier customers
```

### Phase 2: Scale (Month 6+) - SWITCH TO DEEPSEEK

```
WHY:
  - You have data now (can assess accuracy)
  - Cost matters at 100+ contractors
  - DeepSeek v3 now mature enough
  - You can A/B test (gradual rollout)

Cost: $19/month vs $192 (saves $2,285/year)
Impact: Much higher margins as you scale

Implementation:
  1. Parallel run: Claude for 50%, DeepSeek for 50%
  2. Compare accuracy
  3. If >90%, fully switch to DeepSeek
  4. Keep Claude as backup for high-stakes calls
```

### Phase 3: Production (Year 2+) - OPTIMIZE

```
OPTIONS:
  A. Run DeepSeek locally (on your servers)
     - Zero API costs
     - Full control
     - Latency <100ms
     - Cost: $500/month server + ops
     - Saves: $190/month on API = break-even fast

  B. Fine-tune DeepSeek on your data
     - Custom model trained on your agent workflows
     - Better accuracy than base model
     - Cost: $1K one-time + $50/month hosting
     - Improve: 90% → 95%+ accuracy

  C. Hybrid: Claude + DeepSeek
     - High-stakes (quotes, QB sync) = Claude
     - High-volume (leads, scheduling) = DeepSeek
     - Best of both worlds
     - Cost: $100/month mixed
```

---

## Honest Truth: Model Selection

### For Your Use Case

**Claude is better if:**
- Accuracy > cost (which is true for MVP)
- You want minimal debugging
- You want proven production stability
- You don't have 100+ contractors yet

**DeepSeek is better if:**
- You have 500+ contractors
- You've proven accuracy with your data
- You want to maximize margins
- You can accept 1-2% error rate (fine for most tasks)

---

## Deployment Decision Matrix

```
Question: "Which model should I use?"

Answer depends on these factors:

1. TIMELINE
   MVP (weeks 1-12): Claude ✓
   Scale (month 6+): Hybrid or DeepSeek

2. ACCURACY NEED
   High (quotes, QB): Claude ✓
   Medium (scheduling): DeepSeek OK
   Low (internal): DeepSeek ✓

3. BUDGET
   Tight: DeepSeek ($19/year)
   Comfortable: Claude ($2.3K/year)
   Hybrid: Both ($100/year mixed)

4. VOLUME
   <100 contractors: Claude (costs don't matter)
   >500 contractors: DeepSeek (margins matter)
   >5,000 contractors: Self-hosted DeepSeek (zero API costs)
```

---

## Final Recommendation

### Your Strategy (September 2026)

```
PHASE 1 (Weeks 1-12): MVP with Claude
├── Why: Accuracy critical for launch
├── Cost: $2.3K/year (negligible)
├── Timeline: Faster iteration
└── Status: Launch with confidence

PHASE 2 (Month 6): Evaluate DeepSeek
├── After: 20-50 paying customers
├── Do: Compare Claude vs DeepSeek accuracy
├── If: DeepSeek >90% accuracy, switch
├── Save: $2,285/year
└── Status: Maintain quality, improve margins

PHASE 3 (Year 2): Optimize
├── Options:
│   1. Self-host DeepSeek (zero API costs)
│   2. Fine-tune DeepSeek (better accuracy)
│   3. Hybrid (Claude for critical, DeepSeek for bulk)
├── Cost: $50-500/month (your choice)
└── Status: Maximum margins while maintaining quality
```

---

## Summary

**Q: How do you deploy agents to contractors?**
A: Via cloud SaaS (AWS ECS + RDS). Bob just opens browser. All data isolated & secure.

**Q: Should you use Claude or DeepSeek?**
A: Claude for MVP (better + proven). DeepSeek for scale (10x cheaper + fast enough).

**Timeline:**
- Week 1-12: Claude (MVP)
- Month 6+: Evaluate DeepSeek
- Year 2: Self-host or hybrid

**Cost impact:**
- Claude: $2.3K/year (0.004% of revenue at scale)
- DeepSeek: $19/year (0.0000003% of revenue)
- Self-hosted: $6K/year + ops (break-even at 500+ contractors)

