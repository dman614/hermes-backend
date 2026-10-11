# Parts Database & Billing System: Pre-Populated Supply Costs

**Purpose:** Store common plumbing/HVAC/electrical parts with cost so quotes auto-calculate  
**Benefit:** Quote generation goes from manual 2-3 hours to 30 seconds  
**Database:** PostgreSQL with parts catalog pre-loaded  

---

## The Problem Bob Has Today

```
Customer: "I need new pipes and fittings"
Bob: "Okay, let me calculate..."
     [Pulls out calculator or searches suppliers online]
     "PVC pipe, 3/4" diameter, 10 feet..."
     [Googles: "PVC pipe 3/4 10 feet cost"]
     [Finds: Home Depot $45, Rona $48, Local supplier $42]
     "Fitting elbow 3/4"..."
     [Googles again]
     [Takes 30-45 minutes to get pricing]
     [Still not accurate - pricing changes weekly]
     [Doesn't know his actual wholesale cost]
     [Quotes either too low or too high]

Result: 45 minutes per quote, inconsistent pricing, lost margin
```

---

## The Solution: Pre-Populated Parts Database

### How It Works

```
BEFORE (Manual):
  Customer asks for quote
  Bob: Spends 45 min researching parts
  Bob: Manually calculates
  Result: Quote in 2-3 hours, inconsistent pricing

AFTER (Database):
  Customer asks for quote
  Tech takes photo of what needs fixing
  Tech taps "Generate Quote"
  System auto-selects parts from database:
    - PVC Pipe 3/4" x 10ft: $42 (wholesale cost in database)
    - Elbow Fitting 3/4": $3.50 (in database)
    - Primer: $8 (in database)
    - Thread sealant: $6 (in database)
  System adds 30% markup (Bob's standard)
  Generates professional quote: $110 parts + 2hrs labor
  
Result: Quote in 30 seconds, consistent pricing, accurate margin
```

---

## Database Structure

### Parts Table (PostgreSQL)

```sql
CREATE TABLE parts (
  id SERIAL PRIMARY KEY,
  sku VARCHAR(50) UNIQUE,                    -- e.g., "PVC-3/4-10FT"
  name VARCHAR(200),                         -- e.g., "PVC Pipe 3/4\""
  category VARCHAR(100),                     -- "Pipe", "Fitting", "Valve", etc.
  subcategory VARCHAR(100),                  -- "PVC", "Copper", "Brass"
  
  -- Pricing
  wholesale_cost DECIMAL(10, 2),             -- What Bob pays suppliers ($42)
  retail_markup_percent INT DEFAULT 30,      -- Bob's standard markup (30%)
  retail_price DECIMAL(10, 2),               -- Auto-calculated ($54.60)
  
  -- Specifications
  size VARCHAR(50),                          -- "3/4 inch", "10 feet", etc.
  length_ft DECIMAL(10, 2),                  -- For pipes: 10
  material VARCHAR(100),                     -- "PVC", "Copper", "Brass"
  fitting_type VARCHAR(100),                 -- "Elbow", "Tee", "Coupling"
  thread_type VARCHAR(50),                   -- "NPT", "Slip", etc.
  
  -- Supplier info
  supplier_id INT REFERENCES suppliers(id),  -- Which supplier to order from
  supplier_sku VARCHAR(50),                  -- Supplier's catalog number
  supplier_name VARCHAR(200),                -- "Home Depot", "Rona", "Local"
  
  -- Service categorization
  service_type VARCHAR(50),                  -- "Plumbing", "HVAC", "Electrical"
  common_use VARCHAR(200),                   -- "Emergency pipe burst", etc.
  
  -- Metadata
  stock_status VARCHAR(50),                  -- "In Stock", "Special Order"
  lead_time_days INT,                        -- How long to get it
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Pre-Populated Parts (Sample Data)

### PLUMBING SECTION

#### Pipes & Tubes

```sql
INSERT INTO parts VALUES
  (1, 'PVC-3/4-10FT', 'PVC Pipe 3/4" x 10ft', 'Pipe', 'PVC', 
   42.00, 30, 54.60, '3/4 inch', 10.0, 'PVC', NULL, NULL, 1, 'PVC-750-10', 
   'Home Depot', 'Plumbing', 'Standard supply line', 'In Stock', 0, NOW(), NOW()),
   
  (2, 'PVC-1-10FT', 'PVC Pipe 1" x 10ft', 'Pipe', 'PVC', 
   52.00, 30, 67.60, '1 inch', 10.0, 'PVC', NULL, NULL, 1, 'PVC-100-10', 
   'Home Depot', 'Plumbing', 'Larger supply line', 'In Stock', 0, NOW(), NOW()),
   
  (3, 'COPPER-1/2-10FT', 'Copper Pipe 1/2" x 10ft', 'Pipe', 'Copper', 
   65.00, 30, 84.50, '1/2 inch', 10.0, 'Copper', NULL, NULL, 2, 'COP-50-10', 
   'Rona', 'Plumbing', 'Premium supply line', 'In Stock', 0, NOW(), NOW()),
   
  (4, 'PEX-1/2-100FT', 'PEX Tubing 1/2" x 100ft', 'Pipe', 'PEX', 
   85.00, 30, 110.50, '1/2 inch', 100.0, 'PEX', NULL, NULL, 1, 'PEX-50-100', 
   'Home Depot', 'Plumbing', 'Radiant heating, hot water', 'In Stock', 0, NOW(), NOW());
```

#### Fittings

```sql
INSERT INTO parts VALUES
  (5, 'ELBOW-PVC-3/4', 'PVC Elbow 3/4" 90°', 'Fitting', 'PVC', 
   3.50, 30, 4.55, '3/4 inch', NULL, 'PVC', 'Elbow', 'NPT', 1, 'PVC-EL-750', 
   'Home Depot', 'Plumbing', 'Basic direction change', 'In Stock', 0, NOW(), NOW()),
   
  (6, 'TEE-PVC-3/4', 'PVC Tee 3/4" 3-way', 'Fitting', 'PVC', 
   4.50, 30, 5.85, '3/4 inch', NULL, 'PVC', 'Tee', 'NPT', 1, 'PVC-TEE-750', 
   'Home Depot', 'Plumbing', 'Three-way split', 'In Stock', 0, NOW(), NOW()),
   
  (7, 'COUPLING-PVC-3/4', 'PVC Coupling 3/4"', 'Fitting', 'PVC', 
   2.50, 30, 3.25, '3/4 inch', NULL, 'PVC', 'Coupling', 'NPT', 1, 'PVC-COUP-750', 
   'Home Depot', 'Plumbing', 'Join two pipes', 'In Stock', 0, NOW(), NOW()),
   
  (8, 'BALL-VALVE-3/4', 'Brass Ball Valve 3/4"', 'Valve', 'Brass', 
   12.00, 30, 15.60, '3/4 inch', NULL, 'Brass', 'Ball Valve', 'NPT', 2, 'VALVE-BRZ-750', 
   'Rona', 'Plumbing', 'Shut-off valve, emergency', 'In Stock', 0, NOW(), NOW());
```

#### Supplies

```sql
INSERT INTO parts VALUES
  (9, 'PRIMER-PVC', 'PVC Primer (16 oz)', 'Supply', 'Chemical', 
   8.00, 30, 10.40, 'Standard', NULL, 'Chemical', NULL, NULL, 1, 'PRIM-16', 
   'Home Depot', 'Plumbing', 'Required for PVC joints', 'In Stock', 0, NOW(), NOW()),
   
  (10, 'CEMENT-PVC', 'PVC Cement (16 oz)', 'Supply', 'Chemical', 
   8.50, 30, 11.05, 'Standard', NULL, 'Chemical', NULL, NULL, 1, 'CEM-16', 
   'Home Depot', 'Plumbing', 'Required for PVC joints', 'In Stock', 0, NOW(), NOW()),
   
  (11, 'THREAD-SEAL', 'Thread Seal Tape (PTFE)', 'Supply', 'Chemical', 
   6.00, 30, 7.80, 'Standard', NULL, 'Chemical', NULL, NULL, 1, 'SEAL-TAPE', 
   'Home Depot', 'Plumbing', 'Prevents leaks at threads', 'In Stock', 0, NOW(), NOW()),
   
  (12, 'SOLDER-COPPER', 'Lead-Free Solder Spool', 'Supply', 'Chemical', 
   15.00, 30, 19.50, '1 lb', 1.0, 'Chemical', NULL, NULL, 2, 'SOLD-LF-1LB', 
   'Rona', 'Plumbing', 'For copper joints', 'In Stock', 0, NOW(), NOW());
```

### HVAC SECTION

#### Common Replacements

```sql
INSERT INTO parts VALUES
  (13, 'AC-FILTER-16x25', 'AC Filter 16x25x1 MERV13', 'Filter', 'HVAC', 
   18.00, 30, 23.40, '16x25x1', NULL, 'Fiberglass', NULL, NULL, 1, 'FILT-16X25', 
   'Home Depot', 'HVAC', 'Monthly replacement', 'In Stock', 0, NOW(), NOW()),
   
  (14, 'AC-CAPACITOR-5MFD', 'AC Capacitor 5 MFD', 'Component', 'HVAC', 
   25.00, 30, 32.50, '5 MFD', NULL, 'Electric', NULL, NULL, 1, 'CAP-5MFD', 
   'Home Depot', 'HVAC', 'AC emergency repair', 'In Stock', 0, NOW(), NOW()),
   
  (15, 'REFRIGERANT-R410A', 'Refrigerant R-410A (2 lbs)', 'Refrigerant', 'HVAC', 
   80.00, 30, 104.00, '2 lbs', 2.0, 'Gas', NULL, NULL, 3, 'REF-R410A-2LB', 
   'Supplier', 'HVAC', 'AC recharge', 'In Stock', 0, NOW(), NOW()),
   
  (16, 'FURNACE-BLOWER', 'Furnace Blower Motor', 'Component', 'HVAC', 
   180.00, 30, 234.00, 'Standard', NULL, 'Electric', NULL, NULL, 1, 'BLOWER-STD', 
   'Home Depot', 'HVAC', 'Furnace replacement', 'Special Order', 2, NOW(), NOW());
```

### ELECTRICAL SECTION

#### Common Replacements

```sql
INSERT INTO parts VALUES
  (17, 'OUTLET-15A', '15A Outlet Receptacle', 'Outlet', 'Electrical', 
   3.50, 30, 4.55, 'Standard', NULL, 'Plastic', NULL, NULL, 1, 'OUT-15A', 
   'Home Depot', 'Electrical', 'Outlet replacement', 'In Stock', 0, NOW(), NOW()),
   
  (18, 'GFCI-OUTLET', 'GFCI Outlet 15A', 'Outlet', 'Electrical', 
   12.00, 30, 15.60, 'Standard', NULL, 'Plastic', NULL, NULL, 1, 'GFCI-15A', 
   'Home Depot', 'Electrical', 'Bathroom/kitchen safety', 'In Stock', 0, NOW(), NOW()),
   
  (19, 'LIGHT-SWITCH', 'Light Switch Toggle 15A', 'Switch', 'Electrical', 
   2.50, 30, 3.25, 'Standard', NULL, 'Plastic', NULL, NULL, 1, 'SWITCH-15A', 
   'Home Depot', 'Electrical', 'Standard light switch', 'In Stock', 0, NOW(), NOW()),
   
  (20, 'BREAKER-20A', 'Circuit Breaker 20A', 'Breaker', 'Electrical', 
   8.00, 30, 10.40, '20A', NULL, 'Plastic', NULL, NULL, 1, 'BREAK-20A', 
   'Home Depot', 'Electrical', 'Panel replacement', 'In Stock', 0, NOW(), NOW());
```

---

## How Billing Uses This Database

### Quote Generation (Tech on Site)

```
Tech: Opens Hermes app
      "New Job: Emergency pipe burst at 123 Main"
      
Tech: "Select parts needed"
      [Search box appears]
      
Tech types: "pvc 3/4"
      [Auto-complete suggestions:]
        - PVC Pipe 3/4" x 10ft ($54.60 retail)
        - PVC Elbow 3/4" 90° ($4.55 retail)
        - PVC Tee 3/4" ($5.85 retail)
        - PVC Cement 16oz ($11.05 retail)
        
Tech: Taps "PVC Pipe 3/4" x 10ft"
      [Adds to quote]
      
Tech taps: "PVC Elbow 3/4""
Tech taps: "PVC Cement 16oz"

System auto-calculates:
  Parts subtotal: $54.60 + $4.55 + $11.05 = $70.20
  Labor: 2 hours @ $120/hr = $240.00
  Total: $310.20
  Tax: $21.71 (7%)
  GRAND TOTAL: $331.91

Professional invoice generated instantly
Customer approves on iPad
Payment collected
Done in 2 minutes (vs 2-3 hours manually)
```

---

## Database Features

### Search & Auto-Complete

```
Tech types: "coupling"
  Results:
    - PVC Coupling 3/4" ($3.25)
    - PVC Coupling 1" ($4.10)
    - Coupling with valve ($18.50)

Tech types: "ac"
  Results:
    - AC Filter 16x25 ($23.40)
    - AC Capacitor 5 MFD ($32.50)
    - AC Refrigerant R-410A ($104.00)

Tech types: "emergency"
  Results:
    - All parts marked "Emergency use"
```

### Dynamic Pricing

```
Problem: Contractor's markup changes by service type

Solution: Multiple markup options in database

Normal job (30% markup):
  Part cost $50 → Retail $65

Emergency job (50% markup):
  Part cost $50 → Retail $75

Wholesale (0% markup):
  Part cost $50 → Retail $50

Database stores: wholesale cost only
Quote system applies markup based on job type
Result: Accurate, consistent pricing
```

---

## Categories & Organization

### Plumbing

```
Parts (Pipes):
  - PVC (3/4", 1", 1.5", 2")
  - Copper (1/2", 3/4", 1")
  - PEX (1/2", 3/4", 1")
  - Galvanized (legacy)

Fittings:
  - Elbows (90°, 45°)
  - Tees (3-way)
  - Couplings (straight, reducer)
  - Valves (ball, gate, check)

Supplies:
  - Primer, cement (PVC)
  - Solder (copper)
  - Thread seal tape
  - Flux (copper)

Fixtures:
  - Faucets
  - Toilets
  - Sinks
  - Showerheads
```

### HVAC

```
Filters:
  - Air filters (various sizes)
  - Furnace filters

Components:
  - Capacitors (AC, furnace)
  - Blower motors
  - Thermostats
  - Ductwork

Refrigerant:
  - R-410A (modern)
  - R-22 (legacy)

Supplies:
  - Refrigerant oil
  - Sealant
  - Lubricant
```

### Electrical

```
Outlets & Switches:
  - Standard outlets
  - GFCI outlets
  - Switches (toggle, dimmer)
  - USB outlets

Breakers:
  - 15A, 20A, 30A, etc.
  - Various amp ratings

Wiring:
  - 14/2, 12/2, 10/2 (various gauges)
  - Ground wire
  - Conduit

Fixtures:
  - Light switches
  - Dimmers
  - Outlets
```

---

## Pricing Logic

### How Retail Price Calculates

```
Formula:
  Retail Price = Wholesale Cost × (1 + Markup%)
  
Example:
  Wholesale: $50.00
  Markup: 30%
  Retail: $50.00 × 1.30 = $65.00
  
  So invoice shows: $65.00 (customer sees this)
  Bob's cost: $50.00 (Bob knows this)
  Bob's margin: $15.00 (profit per part)
```

### Bulk Adjustments

```
If Bob buys in bulk, wholesale cost drops:
  Single unit: $50
  Bulk 10+: $45 per unit
  
Database can track volume pricing:
  price_tier_1: 1-10 units @ $50
  price_tier_2: 11-50 units @ $45
  price_tier_3: 50+ units @ $42
```

---

## Supplier Management

### Multiple Suppliers

```
Database tracks which suppliers carry each part:

PVC Pipe 3/4":
  Supplier A: Home Depot, $42 cost, in stock
  Supplier B: Rona, $44 cost, in stock
  Supplier C: Local, $40 cost, 2-day delivery

Bob configures: Use lowest cost supplier (Supplier C)
Hermes auto-selects for quotes
If Supplier C out, auto-switches to Supplier A
```

### Auto-Reordering

```
Threshold: When stock low, auto-order from supplier
  Set for each part:
    - Reorder point: 5 units
    - Order quantity: 20 units
    - Auto-order: Yes/No

When inventory hits 5:
  System auto-orders 20 more from configured supplier
  Email sent to Bob: "PVC Pipe 3/4 reordered"
  
Result: Never runs out, always has stock
```

---

## Real-World Example: Bob's First Quote with Database

### Scenario: Emergency Burst Pipe

```
7:15 AM - Bob's tech Sarah arrives at 456 Oak Rd

Sarah: Opens Hermes app
       "New emergency job"
       
Sees: Database populated with 100+ common parts

Sarah: Assesses damage
       "Burst PVC pipe, 3/4 inch, need 20 feet total"
       
Sarah: Taps "Add Parts"
       Searches: "pvc 3/4"
       
[Auto-complete shows:]
  ✓ PVC Pipe 3/4" x 10ft ($54.60) ← clicks this twice (20 ft total)
  ✓ PVC Elbow 3/4" 90° ($4.55) ← clicks this once
  ✓ PVC Coupling 3/4" ($3.25) ← clicks this twice
  ✓ PVC Cement 16oz ($11.05) ← clicks this once
  ✓ PVC Primer 16oz ($10.40) ← clicks this once
  
Subtotal: $54.60 × 2 + $4.55 + $3.25 × 2 + $11.05 + $10.40
        = $109.20 + $4.55 + $6.50 + $11.05 + $10.40
        = $141.70

System adds labor:
  Emergency surcharge: +$50
  Labor 3 hours @ $120/hr = $360
  Total labor: $410

Invoice Total: $141.70 + $410 = $551.70
Tax (7%): $38.62
GRAND TOTAL: $590.32

Professional PDF generated instantly with:
  - Bob's Plumbing logo
  - Address and contact
  - Itemized parts
  - Labor breakdown
  - Total price
  - Terms & conditions

Sarah shows customer on iPad: "Here's what we need to fix this."
Customer: "That's fair. Let's do it."
Sarah: Taps "Customer Approved"
       
Hermes automatically:
  ✅ Sends quote to Bob's email
  ✅ Updates dashboard
  ✅ Reserves parts from inventory
  ✅ Schedules job completion time
  ✅ Notifies Bob

Bob sees SMS: "Quote approved: $590.32"

Sarah does work (3 hours)
Sarah: Taps "Job Complete"

Hermes auto-generates invoice:
  Parts: $141.70
  Labor: 3 × $120 = $360
  Emergency surcharge: $50
  Subtotal: $551.70
  Tax: $38.62
  TOTAL: $590.32
  
Customer taps "Pay Now"
Pays via credit card
Invoice marked PAID

Bob's account: +$590.32
Bob's profit on parts: $141.70 - $70 (actual cost) = $71.70
Bob's profit on labor: $360
Total profit on job: $431.70

All in under 5 minutes of Bob's time (just approvals)
Before: Would have taken 2-3 hours of manual work
```

---

## Database Maintenance

### Who Updates Pricing?

```
Option 1: Bob manually updates
  Bob: Logs into dashboard
       "Manage Parts"
       Adjusts wholesale cost if he negotiates with supplier
       Adjusts markup if he changes business model

Option 2: Automatic from supplier API
  Hermes integrates with supplier (Home Depot, Rona, etc.)
  Pricing syncs automatically weekly
  Bob gets alert if price changes >5%
  
Option 3: Hybrid
  Bob sets wholesale cost
  System auto-calculates retail from markup
  Alerts if supplier price changed significantly
```

### Adding New Parts

```
Bob: "I need a new part type"
     Opens dashboard
     "Add Part"
     
Enters:
  - Name: "Thermostatic Mixing Valve 3/4""
  - Category: "Valve"
  - Wholesale cost: $85
  - Service type: "HVAC"
  - Supplier: "Home Depot"
  - Supplier SKU: "HD-MIXER-3/4"
  
System auto-calculates:
  Retail price (30% markup): $110.50
  
Part immediately available for quotes
No code changes needed
```

---

## Performance Optimization

### Query Speed

```
Database indexed on:
  - Part name (fast search)
  - Category (fast filtering)
  - Service type (fast filtering by trade)
  - SKU (fast lookup)
  
Tech types "pvc": <100ms response (instant)
Tech types "coupling": <100ms response (instant)
Full parts list loads: <500ms (seamless)
```

### Caching

```
Frequently used parts cached in memory:
  - Top 50 plumbing parts (cached)
  - Top 50 HVAC parts (cached)
  - Top 50 electrical parts (cached)
  
Result: Sub-50ms response for common parts
Tech doesn't wait for database
Experience: Instant auto-complete
```

---

## Data Security

### Contractor Pricing Privacy

```
Bob's wholesale costs are PRIVATE:
  - Only Bob sees his costs
  - Techs see retail price only
  - Customers see retail price only
  - Other contractors can't see Bob's costs
  
This protects Bob's margins
Different contractors can have different costs
```

### Audit Trail

```
Every price change tracked:
  2024-09-05 10:30: Bob changed PVC Pipe wholesale from $42 → $40
  2024-09-05 10:30: New retail price: $52 (30% markup)
  
Can see who changed what, when
Protects against accidental changes
Helps troubleshoot billing issues
```

---

## Export & Integration

### QuickBooks Integration

```
When job marked complete:
  System exports to QuickBooks:
    - Parts as inventory items (COGS)
    - Labor as service item
    - Markup as revenue
    - Tax calculated correctly
    
QuickBooks auto-reconciles
Bob's accounting is done automatically
No manual entry needed
```

### Excel Export

```
Bob wants to analyze:
  "Show me all jobs from Sept with plumbing parts"
  
System exports to Excel:
  - Job date
  - Customer name
  - Parts used (with costs)
  - Markup applied
  - Profit margin
  
Bob analyzes trends
Can see which parts are most profitable
Adjusts pricing accordingly
```

---

## What This Means for Bob

### Before Database
```
Customer: "I need new pipes"
Bob: 45 minutes researching prices
Bob: Manual calculations
Bob: Inconsistent quotes
Bob: Lost margin on some jobs
Result: 2-3 hours per quote, stressed
```

### After Database
```
Customer: "I need new pipes"
Tech: 30 seconds selecting parts
System: Auto-calculates
System: Consistent quotes
System: Accurate margin every time
Result: 30 seconds per quote, relaxed
```

### Financial Impact

```
Scenario: Bob does 8 quotes per week

Before database:
  8 quotes × 2.5 hours each = 20 hours
  At $120/hr = $2,400 in labor

After database:
  8 quotes × 0.5 minutes each = 4 minutes
  At $120/hr = $8 in labor
  
Time saved: 19.93 hours per week
Value saved: $2,392 per week
Annual value: $124,384

Plus: Better pricing accuracy means higher margins
      = Additional $5K-10K per year in profit

ROI on Hermes ($500/mo): 300-600x in time savings alone
```

---

## Data We'll Pre-Load

### Initial Database (Launch)

```
~500 common parts:
  - 200 plumbing parts
  - 150 HVAC parts
  - 150 electrical parts
  
All with:
  - Wholesale cost
  - Retail markup
  - Supplier info
  - Specifications
  - Common uses
```

### Growth

```
Bob submits feedback:
  "I need PEX tubing, it's not in database"
  
Hermes adds it:
  - Week 1: 500 parts
  - Month 1: 750 parts (based on customer feedback)
  - Month 3: 1,000+ parts (comprehensive)
  - Year 1: 2,000+ parts (full market coverage)
```

---

## Summary: Why This Changes Everything

| Before Database | After Database |
|---|---|
| 45 min to get parts pricing | 30 sec to select parts |
| Manual calculations | Auto-calculated |
| Inconsistent quotes | Consistent pricing |
| Lost margins | Protected margins |
| Customer confusion | Professional invoice |
| 2-3 hours per quote | 30 seconds per quote |

**Database transforms quoting from a bottleneck into a competitive advantage.**

**Bob goes from hours per quote to seconds per quote.**

**That's a 300-600x productivity gain.**

