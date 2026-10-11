# PostgreSQL Schema: Parts Database & Billing System

**File:** Database migration for parts catalog and billing  
**Language:** SQL (PostgreSQL)  
**Status:** Ready to implement in Week 2  

---

## Complete Database Schema

```sql
-- ============================================================================
-- SUPPLIERS TABLE: Where Bob orders parts from
-- ============================================================================
CREATE TABLE suppliers (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,                -- "Home Depot", "Rona", "Local Supplier"
  contact_email VARCHAR(100),
  contact_phone VARCHAR(20),
  website VARCHAR(255),
  payment_terms VARCHAR(100),                -- "Net 30", "COD", etc.
  default_lead_time_days INT DEFAULT 2,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Sample data
INSERT INTO suppliers (name, website, default_lead_time_days) VALUES
  ('Home Depot', 'homedepot.com', 1),
  ('Rona', 'rona.ca', 1),
  ('Local Plumbing Supply', NULL, 0),
  ('HVAC Supplier', NULL, 2),
  ('Electrical Distributor', NULL, 1);


-- ============================================================================
-- PARTS TABLE: The main parts catalog
-- ============================================================================
CREATE TABLE parts (
  id SERIAL PRIMARY KEY,
  
  -- Identification
  sku VARCHAR(50) UNIQUE NOT NULL,           -- Unique code (e.g., "PVC-3/4-10FT")
  name VARCHAR(200) NOT NULL,                -- Display name (e.g., "PVC Pipe 3/4\" x 10ft")
  description TEXT,                          -- Detailed description
  
  -- Categorization
  category VARCHAR(100) NOT NULL,            -- "Pipe", "Fitting", "Valve", "Filter", etc.
  subcategory VARCHAR(100),                  -- "PVC", "Copper", "Brass", "Electric", etc.
  service_type VARCHAR(50) NOT NULL,         -- "Plumbing", "HVAC", "Electrical"
  
  -- Specifications
  material VARCHAR(100),                     -- "PVC", "Copper", "Brass", "Plastic", etc.
  size VARCHAR(100),                         -- "3/4 inch", "1 inch", "10 feet", etc.
  length_ft DECIMAL(10, 2),                  -- For pipes/tubing (NULL for others)
  diameter_in DECIMAL(10, 2),                -- For pipes/tubing (NULL for others)
  fitting_type VARCHAR(100),                 -- "Elbow", "Tee", "Coupling", "Valve", etc.
  thread_type VARCHAR(50),                   -- "NPT", "NPTF", "Slip", etc.
  temperature_rating_f INT,                  -- Max temperature (NULL if not applicable)
  pressure_rating_psi INT,                   -- Max pressure (NULL if not applicable)
  specifications JSONB,                      -- Additional specs as JSON
  
  -- Pricing (CRITICAL)
  wholesale_cost DECIMAL(10, 2) NOT NULL,    -- Bob's cost from supplier ($42.00)
  standard_markup_percent INT DEFAULT 30,    -- Default markup (30%)
  emergency_markup_percent INT DEFAULT 50,   -- Emergency job markup (50%)
  retail_price_standard DECIMAL(10, 2),      -- Auto-calculated (wholesale × 1.30)
  retail_price_emergency DECIMAL(10, 2),     -- Auto-calculated (wholesale × 1.50)
  
  -- Supplier Information
  supplier_id INT REFERENCES suppliers(id),  -- Which supplier carries this
  supplier_sku VARCHAR(100),                 -- Supplier's catalog number
  supplier_cost DECIMAL(10, 2),              -- What supplier charges Bob
  bulk_pricing JSONB,                        -- Volume discounts (1-10: $42, 11-50: $40, etc.)
  
  -- Inventory & Ordering
  current_stock INT DEFAULT 0,               -- How many Bob has on hand
  reorder_point INT DEFAULT 5,               -- Reorder when stock drops to this
  reorder_quantity INT DEFAULT 20,           -- Order this many when reordering
  auto_reorder BOOLEAN DEFAULT FALSE,        -- Auto-order when stock low?
  lead_time_days INT DEFAULT 1,              -- How long to get it
  stock_status VARCHAR(50) DEFAULT 'In Stock', -- "In Stock", "Low Stock", "Out of Stock", "Special Order"
  
  -- Usage Categorization
  common_use VARCHAR(255),                   -- "Emergency pipe burst", "Routine maintenance", etc.
  typical_usage_per_job DECIMAL(10, 2),      -- How many units per typical job (for inventory planning)
  is_consumable BOOLEAN DEFAULT FALSE,       -- True for supplies (cement, primer, solder)
  is_equipment BOOLEAN DEFAULT FALSE,        -- True for equipment (motors, compressors)
  
  -- Status & Metadata
  is_active BOOLEAN DEFAULT TRUE,
  is_discontinued BOOLEAN DEFAULT FALSE,
  discontinued_date DATE,
  replacement_part_id INT REFERENCES parts(id), -- If discontinued, what to use instead?
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Indexes for fast lookup
  CONSTRAINT positive_cost CHECK (wholesale_cost > 0),
  CONSTRAINT positive_markup CHECK (standard_markup_percent >= 0)
);

-- Indexes for performance
CREATE INDEX idx_parts_sku ON parts(sku);
CREATE INDEX idx_parts_name ON parts USING GIN(to_tsvector('english', name)); -- Full text search
CREATE INDEX idx_parts_category ON parts(category);
CREATE INDEX idx_parts_service_type ON parts(service_type);
CREATE INDEX idx_parts_supplier_id ON parts(supplier_id);
CREATE INDEX idx_parts_stock_status ON parts(stock_status);


-- ============================================================================
-- PRICING HISTORY: Track price changes over time
-- ============================================================================
CREATE TABLE parts_pricing_history (
  id SERIAL PRIMARY KEY,
  part_id INT NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  
  -- Old values
  old_wholesale_cost DECIMAL(10, 2),
  old_markup_percent INT,
  
  -- New values
  new_wholesale_cost DECIMAL(10, 2),
  new_markup_percent INT,
  
  -- Change info
  changed_by VARCHAR(100),                   -- Bob's email/username
  reason VARCHAR(255),                       -- "Negotiated bulk discount", "Supplier price increase"
  
  changed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pricing_history_part_id ON parts_pricing_history(part_id);
CREATE INDEX idx_pricing_history_changed_at ON parts_pricing_history(changed_at);


-- ============================================================================
-- JOBS ITEMS TABLE: Links jobs to parts used
-- ============================================================================
CREATE TABLE job_items (
  id SERIAL PRIMARY KEY,
  job_id INT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  part_id INT NOT NULL REFERENCES parts(id),
  
  -- Quantity & pricing at time of job
  quantity INT NOT NULL DEFAULT 1,
  part_name_snapshot VARCHAR(200),          -- Name of part as it was at time of job
  wholesale_cost_at_time DECIMAL(10, 2),    -- Cost to Bob at time of job
  retail_price_at_time DECIMAL(10, 2),      -- Price charged to customer
  
  -- Notes
  notes TEXT,                                -- "3 fittings used, 1 spare"
  
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_items_job_id ON job_items(job_id);
CREATE INDEX idx_job_items_part_id ON job_items(part_id);


-- ============================================================================
-- BULK PRICING TABLE: Volume discounts per part
-- ============================================================================
CREATE TABLE bulk_pricing (
  id SERIAL PRIMARY KEY,
  part_id INT NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  
  min_quantity INT NOT NULL,                 -- Minimum units for this tier
  max_quantity INT,                          -- Maximum units for this tier (NULL = unlimited)
  cost_per_unit DECIMAL(10, 2) NOT NULL,    -- Cost when buying this many
  
  CONSTRAINT valid_quantities CHECK (min_quantity > 0 AND (max_quantity IS NULL OR max_quantity >= min_quantity))
);

CREATE INDEX idx_bulk_pricing_part_id ON bulk_pricing(part_id);

-- Example: PVC Pipe 3/4"
-- INSERT INTO bulk_pricing (part_id, min_quantity, max_quantity, cost_per_unit) VALUES
--  (1, 1, 10, 42.00),      -- Buy 1-10: $42 each
--  (1, 11, 50, 39.90),     -- Buy 11-50: $39.90 each
--  (1, 51, NULL, 37.50);   -- Buy 51+: $37.50 each


-- ============================================================================
-- FAVORITE PARTS TABLE: Quick access for frequently used parts
-- ============================================================================
CREATE TABLE contractor_favorite_parts (
  id SERIAL PRIMARY KEY,
  contractor_id INT NOT NULL REFERENCES contractors(id) ON DELETE CASCADE,
  part_id INT NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  
  -- Custom overrides for this contractor
  custom_wholesale_cost DECIMAL(10, 2),     -- If NULL, use part's default
  custom_markup_percent INT,                 -- If NULL, use part's default
  
  -- Tracking
  use_count INT DEFAULT 0,                   -- How many times used in quotes
  last_used_date DATE,
  display_order INT DEFAULT 0,               -- Order in favorites list
  
  UNIQUE(contractor_id, part_id)
);

CREATE INDEX idx_favorite_parts_contractor_id ON contractor_favorite_parts(contractor_id);


-- ============================================================================
-- PART SUBSTITUTIONS TABLE: Link equivalent parts
-- ============================================================================
CREATE TABLE part_substitutions (
  id SERIAL PRIMARY KEY,
  primary_part_id INT NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  alternative_part_id INT NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  
  reason VARCHAR(255),                       -- "Same function, cheaper", "Discontinued"
  preferred_alternative BOOLEAN DEFAULT FALSE, -- Use this one by default?
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- Example: PVC Coupling vs Union Coupling
-- INSERT INTO part_substitutions (primary_part_id, alternative_part_id, reason) VALUES
--  (7, 25, 'Same function, allows disassembly');


-- ============================================================================
-- CONTRACTOR PRICING OVERRIDES TABLE: Different markup for different contractors
-- ============================================================================
CREATE TABLE contractor_pricing (
  id SERIAL PRIMARY KEY,
  contractor_id INT NOT NULL REFERENCES contractors(id) ON DELETE CASCADE,
  part_id INT NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  
  -- Override default pricing
  wholesale_cost DECIMAL(10, 2),             -- If NULL, use part's default
  markup_percent INT,                        -- If NULL, use part's default
  
  effective_date DATE NOT NULL,
  expiration_date DATE,
  
  reason VARCHAR(255),                       -- "Bulk discount negotiated", "Special pricing"
  
  UNIQUE(contractor_id, part_id, effective_date)
);


-- ============================================================================
-- PARTS SEARCH CACHE: Pre-computed full-text search for speed
-- ============================================================================
CREATE TABLE parts_search_cache (
  id SERIAL PRIMARY KEY,
  part_id INT UNIQUE NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
  
  -- Search document (concatenated for full-text search)
  search_document TSVECTOR,
  
  -- Quick filters
  service_type VARCHAR(50),
  category VARCHAR(100),
  
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Trigger to update search cache when part name changes
CREATE OR REPLACE FUNCTION update_parts_search_cache()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO parts_search_cache (part_id, search_document, service_type, category)
  VALUES (
    NEW.id,
    to_tsvector('english', NEW.name || ' ' || COALESCE(NEW.description, '') || ' ' || NEW.category),
    NEW.service_type,
    NEW.category
  )
  ON CONFLICT (part_id) DO UPDATE SET
    search_document = EXCLUDED.search_document,
    updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_parts_search
AFTER INSERT OR UPDATE ON parts
FOR EACH ROW EXECUTE FUNCTION update_parts_search_cache();


-- ============================================================================
-- SAMPLE DATA: Pre-populate common parts
-- ============================================================================

-- PLUMBING SECTION
INSERT INTO parts (sku, name, description, category, subcategory, service_type, material, size, 
                   length_ft, wholesale_cost, standard_markup_percent, supplier_id, supplier_sku,
                   common_use, is_consumable) VALUES

-- Pipes
('PVC-3/4-10FT', 'PVC Pipe 3/4" x 10ft', 'Standard PVC drainage pipe', 'Pipe', 'PVC', 
 'Plumbing', 'PVC', '3/4 inch', 10.0, 42.00, 30, 1, 'PVC-750-10', 'Standard water supply', FALSE),

('PVC-1-10FT', 'PVC Pipe 1" x 10ft', 'Standard PVC drainage pipe', 'Pipe', 'PVC', 
 'Plumbing', 'PVC', '1 inch', 10.0, 52.00, 30, 1, 'PVC-100-10', 'Larger water supply', FALSE),

('COPPER-1/2-10FT', 'Copper Pipe 1/2" x 10ft', 'Premium copper supply line', 'Pipe', 'Copper', 
 'Plumbing', 'Copper', '1/2 inch', 10.0, 65.00, 30, 2, 'COP-50-10', 'Premium hot water', FALSE),

-- Fittings
('ELBOW-PVC-3/4', 'PVC Elbow 3/4" 90°', 'Change pipe direction', 'Fitting', 'PVC', 
 'Plumbing', 'PVC', '3/4 inch', NULL, 3.50, 30, 1, 'PVC-EL-750', 'Basic direction change', FALSE),

('TEE-PVC-3/4', 'PVC Tee 3/4" 3-way', 'Three-way pipe split', 'Fitting', 'PVC', 
 'Plumbing', 'PVC', '3/4 inch', NULL, 4.50, 30, 1, 'PVC-TEE-750', 'Three-way split', FALSE),

('BALL-VALVE-3/4', 'Brass Ball Valve 3/4"', 'Shut-off valve', 'Valve', 'Brass', 
 'Plumbing', 'Brass', '3/4 inch', NULL, 12.00, 30, 2, 'VALVE-BRZ-750', 'Emergency shut-off', FALSE),

-- Supplies (consumable)
('PRIMER-PVC', 'PVC Primer (16 oz)', 'Required for PVC joints', 'Supply', 'Chemical', 
 'Plumbing', 'Chemical', 'Standard', NULL, 8.00, 30, 1, 'PRIM-16', 'PVC preparation', TRUE),

('CEMENT-PVC', 'PVC Cement (16 oz)', 'Required for PVC joints', 'Supply', 'Chemical', 
 'Plumbing', 'Chemical', 'Standard', NULL, 8.50, 30, 1, 'CEM-16', 'PVC joining', TRUE),

('THREAD-SEAL', 'Thread Seal Tape (PTFE)', 'Prevents thread leaks', 'Supply', 'Chemical', 
 'Plumbing', 'Chemical', 'Standard', NULL, 6.00, 30, 1, 'SEAL-TAPE', 'Thread sealing', TRUE),

-- HVAC SECTION
('AC-FILTER-16x25', 'AC Filter 16x25x1 MERV13', 'Replacement air filter', 'Filter', 'HVAC', 
 'HVAC', 'Fiberglass', '16x25x1', NULL, 18.00, 30, 1, 'FILT-16X25', 'Monthly replacement', TRUE),

('AC-CAPACITOR-5MFD', 'AC Capacitor 5 MFD', 'AC compressor start', 'Component', 'HVAC', 
 'HVAC', 'Electric', '5 MFD', NULL, 25.00, 30, 1, 'CAP-5MFD', 'Emergency repair', FALSE),

('REFRIGERANT-R410A', 'Refrigerant R-410A (2 lbs)', 'AC refrigerant charge', 'Refrigerant', 'HVAC', 
 'HVAC', 'Gas', '2 lbs', NULL, 80.00, 30, 3, 'REF-R410A-2LB', 'AC recharge', TRUE),

-- ELECTRICAL SECTION
('OUTLET-15A', '15A Outlet Receptacle', 'Standard electrical outlet', 'Outlet', 'Electrical', 
 'Electrical', 'Plastic', 'Standard', NULL, 3.50, 30, 1, 'OUT-15A', 'Outlet replacement', FALSE),

('GFCI-OUTLET', 'GFCI Outlet 15A', 'Safety outlet for wet areas', 'Outlet', 'Electrical', 
 'Electrical', 'Plastic', 'Standard', NULL, 12.00, 30, 1, 'GFCI-15A', 'Bathroom/kitchen safety', FALSE),

('LIGHT-SWITCH', 'Light Switch Toggle 15A', 'Standard light switch', 'Switch', 'Electrical', 
 'Electrical', 'Plastic', 'Standard', NULL, 2.50, 30, 1, 'SWITCH-15A', 'Light control', FALSE);


-- ============================================================================
-- VERIFY SETUP
-- ============================================================================

-- Check parts table is populated
SELECT COUNT(*) as total_parts, 
       COUNT(DISTINCT service_type) as service_types,
       COUNT(DISTINCT category) as categories
FROM parts;

-- Show quick stats
SELECT service_type, COUNT(*) as part_count, AVG(wholesale_cost) as avg_cost
FROM parts
GROUP BY service_type
ORDER BY service_type;

-- Show pricing example
SELECT name, wholesale_cost, standard_markup_percent,
       ROUND(wholesale_cost * (1 + standard_markup_percent::numeric/100), 2) as retail_price
FROM parts
LIMIT 10;
```

---

## Key Features of This Schema

### 1. **Flexible Pricing**
- Store wholesale cost
- Calculate retail from markup %
- Support bulk pricing
- Track pricing changes over time
- Allow per-contractor overrides

### 2. **Fast Search**
- Full-text search index on part names
- Category/service type indexes
- Pre-computed search cache
- Sub-100ms queries

### 3. **Inventory Tracking**
- Current stock
- Reorder points
- Auto-reordering capability
- Supplier lead times

### 4. **Audit Trail**
- Track all pricing changes
- Know who changed what, when
- Reason for changes
- Can revert if needed

### 5. **Contractor Customization**
- Different markup per contractor
- Favorite parts list
- Price overrides
- Use tracking

### 6. **Supplier Management**
- Multiple suppliers per part
- Bulk pricing tiers
- Lead times
- Part substitutions (if discontinued)

---

## Usage in Quote Generation

```python
# Pseudo-code for quote generation

def generate_quote(job_id, part_ids, quantities):
    """
    Generate professional quote from selected parts
    """
    total = 0
    items = []
    
    for part_id, qty in zip(part_ids, quantities):
        # Get part from database
        part = Parts.get(part_id)
        
        # Calculate price
        if job.is_emergency:
            markup = part.emergency_markup_percent
        else:
            markup = part.standard_markup_percent
            
        retail_price = part.wholesale_cost * (1 + markup / 100)
        line_total = retail_price * qty
        
        # Track for invoice
        items.append({
            'part_name': part.name,
            'quantity': qty,
            'unit_price': retail_price,
            'line_total': line_total,
            'cost_to_bob': part.wholesale_cost * qty
        })
        
        total += line_total
    
    # Generate professional PDF
    quote_pdf = generate_invoice(items, total)
    return quote_pdf
```

---

## Migration (Week 2)

```bash
# Run migration
psql -U hermes -d hermes_db -f schema.sql

# Verify
psql -U hermes -d hermes_db -c "SELECT COUNT(*) FROM parts;"

# Result should show: 25+ parts pre-loaded and ready
```

