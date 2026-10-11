-- ============================================================================
-- SUPPLIER INVOICE MANAGEMENT SYSTEM - PostgreSQL Schema
-- ============================================================================
-- Complete database schema for invoice scanning, OCR, QB sync, and reminders
-- Status: Ready to implement Week 2-4
-- Author: Hermes Backend Team
-- Date: September 5, 2026

-- ============================================================================
-- SUPPLIER INVOICES TABLE: Track all incoming invoices from suppliers
-- ============================================================================
CREATE TABLE supplier_invoices (
  id SERIAL PRIMARY KEY,
  
  -- Ownership & Source
  contractor_id INT NOT NULL REFERENCES contractors(id) ON DELETE CASCADE,
  source_type VARCHAR(50),              -- "Photo", "PDF", "Email", "Manual"
  source_file_path VARCHAR(500),        -- S3 path to original image/PDF
  uploaded_at TIMESTAMP DEFAULT NOW(),
  uploaded_by VARCHAR(100),             -- Bob's email or tech name
  
  -- OCR Processing
  ocr_raw_text TEXT,                    -- Raw text from OCR (audit trail)
  ocr_confidence DECIMAL(5, 2),         -- 0-100% confidence of extraction
  extraction_method VARCHAR(100),       -- "AWS_Textract", "Tesseract", "Manual"
  
  -- Invoice Details (Extracted or Manual)
  supplier_id INT REFERENCES suppliers(id),
  supplier_name VARCHAR(200) NOT NULL, -- "Home Depot", "Rona", "Local Supply"
  supplier_address TEXT,                -- Extracted from invoice
  supplier_phone VARCHAR(20),
  supplier_email VARCHAR(100),
  
  -- Invoice Identifiers
  invoice_number VARCHAR(100),          -- Supplier's invoice number
  invoice_date DATE,                    -- When supplier issued invoice
  due_date DATE NOT NULL,               -- Payment due date (CRITICAL)
  received_date DATE,                   -- When Bob received it
  
  -- Financial Data
  subtotal DECIMAL(10, 2),              -- Before tax
  tax_amount DECIMAL(10, 2),            -- Sales tax/HST
  tax_rate DECIMAL(5, 2),               -- Tax percentage (5%, 13%, etc.)
  total_amount DECIMAL(10, 2) NOT NULL, -- Final amount due
  
  -- Payment Tracking
  payment_status VARCHAR(50) DEFAULT 'Unpaid', -- "Unpaid", "Partial", "Paid", "Overdue"
  payment_method VARCHAR(50),           -- "Check", "Credit Card", "Online Transfer"
  paid_date DATE,                       -- When Bob paid it
  paid_amount DECIMAL(10, 2),           -- Amount actually paid (if partial)
  
  -- QuickBooks Integration
  quickbooks_bill_id VARCHAR(100),      -- QB Bill ID (once created)
  quickbooks_sync_status VARCHAR(50) DEFAULT 'Pending', -- "Pending", "Synced", "Error"
  quickbooks_sync_error TEXT,           -- Error message if sync failed
  quickbooks_synced_at TIMESTAMP,       -- When synced to QB
  
  -- Reminder Tracking
  reminder_sent_days_before BOOLEAN DEFAULT FALSE,  -- 3 days before
  reminder_sent_due_date BOOLEAN DEFAULT FALSE,     -- On due date
  reminder_sent_overdue BOOLEAN DEFAULT FALSE,      -- When overdue
  
  -- Organization & Notes
  notes TEXT,                           -- Bob's notes ("Pay with credit card", etc.)
  category VARCHAR(100),                -- "Parts", "Labor", "Equipment", "Services"
  is_recurring BOOLEAN DEFAULT FALSE,   -- Is this a recurring bill (e.g., monthly)?
  
  -- Status & Review
  status VARCHAR(50) DEFAULT 'Pending', -- "Pending", "Approved", "Rejected", "Paid", "Archived"
  reviewed_by VARCHAR(100),             -- Who approved it (Bob's email)
  reviewed_at TIMESTAMP,                -- When approved
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT positive_total CHECK (total_amount > 0),
  CONSTRAINT valid_dates CHECK (invoice_date <= due_date)
);

-- Indexes for fast queries
CREATE INDEX idx_invoices_contractor_id ON supplier_invoices(contractor_id);
CREATE INDEX idx_invoices_supplier_id ON supplier_invoices(supplier_id);
CREATE INDEX idx_invoices_due_date ON supplier_invoices(due_date);
CREATE INDEX idx_invoices_payment_status ON supplier_invoices(payment_status);
CREATE INDEX idx_invoices_invoice_date ON supplier_invoices(invoice_date);
CREATE INDEX idx_invoices_qb_sync_status ON supplier_invoices(quickbooks_sync_status);


-- ============================================================================
-- SUPPLIER INVOICE ITEMS TABLE: Line items from each invoice
-- ============================================================================
CREATE TABLE supplier_invoice_items (
  id SERIAL PRIMARY KEY,
  invoice_id INT NOT NULL REFERENCES supplier_invoices(id) ON DELETE CASCADE,
  
  -- Item Details
  description VARCHAR(500) NOT NULL,   -- "PVC Pipe 3/4\" x 10ft"
  quantity DECIMAL(10, 2) NOT NULL,    -- How many units
  unit_price DECIMAL(10, 2) NOT NULL,  -- Price per unit
  line_total DECIMAL(10, 2) NOT NULL,  -- Qty × Unit Price
  
  -- Categorization (for QB expense accounts)
  expense_category VARCHAR(100),       -- "Parts", "Equipment", "Labor", "Supplies"
  part_id INT REFERENCES parts(id),    -- Link to Hermes parts database (if known)
  
  -- QB Integration
  quickbooks_item_id VARCHAR(100),     -- QB expense account ID
  
  -- OCR Confidence Scores
  description_confidence DECIMAL(5, 2), -- 0-100% confidence
  quantity_confidence DECIMAL(5, 2),
  price_confidence DECIMAL(5, 2),
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT positive_qty CHECK (quantity > 0),
  CONSTRAINT positive_price CHECK (unit_price > 0),
  CONSTRAINT positive_line_total CHECK (line_total > 0)
);

-- Indexes
CREATE INDEX idx_invoice_items_invoice_id ON supplier_invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_part_id ON supplier_invoice_items(part_id);


-- ============================================================================
-- INVOICE PAYMENT REMINDERS TABLE: Scheduled payment reminders
-- ============================================================================
CREATE TABLE invoice_payment_reminders (
  id SERIAL PRIMARY KEY,
  invoice_id INT NOT NULL REFERENCES supplier_invoices(id) ON DELETE CASCADE,
  contractor_id INT NOT NULL REFERENCES contractors(id) ON DELETE CASCADE,
  
  -- Reminder Configuration
  days_before_due INT DEFAULT 3,       -- Remind N days before due date
  reminder_date DATE NOT NULL,          -- Calculated: due_date - days_before_due
  reminder_type VARCHAR(50) NOT NULL,   -- "Before_Due", "On_Due", "Overdue"
  
  -- Reminder Status
  is_sent BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMP,
  sent_via VARCHAR(50),                -- "SMS", "Email", "Push_Notification"
  delivery_status VARCHAR(50),         -- "Delivered", "Failed", "Pending"
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT valid_reminder_type CHECK (reminder_type IN ('Before_Due', 'On_Due', 'Overdue'))
);

-- Indexes
CREATE INDEX idx_reminders_invoice_id ON invoice_payment_reminders(invoice_id);
CREATE INDEX idx_reminders_contractor_id ON invoice_payment_reminders(contractor_id);
CREATE INDEX idx_reminders_reminder_date ON invoice_payment_reminders(reminder_date);
CREATE INDEX idx_reminders_is_sent ON invoice_payment_reminders(is_sent);


-- ============================================================================
-- OCR PROCESSING LOG TABLE: Track all OCR operations
-- ============================================================================
CREATE TABLE ocr_processing_log (
  id SERIAL PRIMARY KEY,
  invoice_id INT REFERENCES supplier_invoices(id) ON DELETE SET NULL,
  
  -- Processing Info
  file_path VARCHAR(500),              -- Original file location
  file_size_kb INT,                    -- File size
  processing_method VARCHAR(100),      -- "AWS_Textract", "Tesseract"
  processing_time_ms INT,              -- How long OCR took (milliseconds)
  
  -- Results
  raw_text_length INT,                 -- Length of extracted text
  confidence_score DECIMAL(5, 2),      -- Overall confidence (0-100%)
  errors_detected TEXT,                -- Any errors during processing
  
  -- Status
  status VARCHAR(50),                  -- "Success", "Partial", "Failed"
  error_message TEXT,                  -- Error details if failed
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_ocr_log_invoice_id ON ocr_processing_log(invoice_id);


-- ============================================================================
-- QB SYNC LOG TABLE: Track all QuickBooks synchronizations
-- ============================================================================
CREATE TABLE qb_sync_log (
  id SERIAL PRIMARY KEY,
  invoice_id INT NOT NULL REFERENCES supplier_invoices(id) ON DELETE CASCADE,
  
  -- Sync Details
  sync_type VARCHAR(50),               -- "Create_Bill", "Update_Bill", "Mark_Paid"
  qb_bill_id VARCHAR(100),             -- QB Bill ID
  
  -- Status
  status VARCHAR(50),                  -- "Success", "Failed", "Retry"
  error_message TEXT,                  -- Error details if failed
  
  -- Request/Response (for debugging)
  request_payload TEXT,                -- JSON request to QB API
  response_payload TEXT,               -- JSON response from QB API
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_qb_sync_log_invoice_id ON qb_sync_log(invoice_id);


-- ============================================================================
-- SAMPLE DATA: Pre-populate with example suppliers
-- ============================================================================

-- Add to existing suppliers table
INSERT INTO suppliers (name, website, default_lead_time_days) VALUES
  ('Home Depot', 'homedepot.com', 1),
  ('Rona', 'rona.ca', 1),
  ('Local Plumbing Supply', NULL, 0),
  ('HVAC Distributor', NULL, 2),
  ('Electrical Supply Co', NULL, 1)
ON CONFLICT DO NOTHING;  -- Skip if already exists


-- ============================================================================
-- VIEW: Upcoming Payments Summary
-- ============================================================================
CREATE OR REPLACE VIEW upcoming_payments AS
SELECT 
  si.id,
  si.contractor_id,
  si.supplier_name,
  si.invoice_number,
  si.total_amount,
  si.due_date,
  (si.due_date - CURRENT_DATE) as days_until_due,
  CASE 
    WHEN si.due_date < CURRENT_DATE THEN 'OVERDUE'
    WHEN si.due_date <= CURRENT_DATE + INTERVAL '3 days' THEN 'DUE_SOON'
    ELSE 'OK'
  END as urgency,
  si.payment_status
FROM supplier_invoices si
WHERE si.payment_status != 'Paid'
  AND si.status = 'Approved'
ORDER BY si.due_date ASC;


-- ============================================================================
-- VIEW: Overdue Invoices
-- ============================================================================
CREATE OR REPLACE VIEW overdue_invoices AS
SELECT 
  si.id,
  si.contractor_id,
  si.supplier_name,
  si.invoice_number,
  si.total_amount,
  si.due_date,
  (CURRENT_DATE - si.due_date) as days_overdue
FROM supplier_invoices si
WHERE si.due_date < CURRENT_DATE
  AND si.payment_status IN ('Unpaid', 'Partial')
  AND si.status = 'Approved'
ORDER BY si.due_date ASC;


-- ============================================================================
-- VIEW: Monthly Invoice Summary
-- ============================================================================
CREATE OR REPLACE VIEW monthly_invoice_summary AS
SELECT 
  si.contractor_id,
  DATE_TRUNC('month', si.invoice_date)::DATE as month,
  COUNT(*) as total_invoices,
  SUM(si.total_amount) as total_spent,
  SUM(CASE WHEN si.payment_status = 'Paid' THEN si.total_amount ELSE 0 END) as amount_paid,
  SUM(CASE WHEN si.payment_status IN ('Unpaid', 'Partial') THEN si.total_amount ELSE 0 END) as amount_unpaid,
  COUNT(CASE WHEN si.payment_status IN ('Unpaid', 'Partial') THEN 1 END) as unpaid_count
FROM supplier_invoices si
WHERE si.status = 'Approved'
GROUP BY si.contractor_id, DATE_TRUNC('month', si.invoice_date)
ORDER BY month DESC;


-- ============================================================================
-- TRIGGER: Auto-create payment reminders when invoice approved
-- ============================================================================
CREATE OR REPLACE FUNCTION create_payment_reminders()
RETURNS TRIGGER AS $$
BEGIN
  -- Only create reminders if status changes to "Approved"
  IF NEW.status = 'Approved' AND OLD.status IS DISTINCT FROM 'Approved' THEN
    
    -- Reminder 1: 3 days before due date
    INSERT INTO invoice_payment_reminders 
    (invoice_id, contractor_id, days_before_due, reminder_date, reminder_type)
    VALUES (NEW.id, NEW.contractor_id, 3, (NEW.due_date - INTERVAL '3 days')::DATE, 'Before_Due');
    
    -- Reminder 2: On due date
    INSERT INTO invoice_payment_reminders 
    (invoice_id, contractor_id, days_before_due, reminder_date, reminder_type)
    VALUES (NEW.id, NEW.contractor_id, 0, NEW.due_date, 'On_Due');
    
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_payment_reminders
AFTER UPDATE ON supplier_invoices
FOR EACH ROW
EXECUTE FUNCTION create_payment_reminders();


-- ============================================================================
-- TRIGGER: Update payment_status when marked paid
-- ============================================================================
CREATE OR REPLACE FUNCTION update_payment_status()
RETURNS TRIGGER AS $$
BEGIN
  -- Auto-update payment_status based on paid_amount
  IF NEW.paid_amount IS NOT NULL THEN
    IF NEW.paid_amount >= NEW.total_amount THEN
      NEW.payment_status = 'Paid';
    ELSE
      NEW.payment_status = 'Partial';
    END IF;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_payment_status
BEFORE UPDATE ON supplier_invoices
FOR EACH ROW
EXECUTE FUNCTION update_payment_status();


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check all tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'supplier_%' OR table_name LIKE '%invoice%' OR table_name LIKE 'qb_%' OR table_name LIKE 'ocr_%'
ORDER BY table_name;

-- Check indexes created
SELECT indexname FROM pg_indexes 
WHERE schemaname = 'public' 
AND (indexname LIKE '%invoice%' OR indexname LIKE '%reminder%')
ORDER BY indexname;

-- Check views created
SELECT viewname FROM pg_views 
WHERE schemaname = 'public' 
AND (viewname LIKE '%invoice%' OR viewname LIKE '%payment%')
ORDER BY viewname;

-- Sample data verification
SELECT COUNT(*) as total_suppliers FROM suppliers;

-- ============================================================================
-- READY FOR PRODUCTION
-- ============================================================================
-- Schema is complete and ready for Week 2 implementation
-- All tables, indexes, triggers, and views are in place
-- Ready to integrate with Python/FastAPI backend
-- Ready to integrate with AWS Textract and QB API
-- Ready to implement reminder scheduling system
