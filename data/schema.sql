-- WoodWard Database Schema
-- Segregated from all other project databases
-- Location: WoodWard/data/woodward.db

-- ============================================
-- BUDGET DATA (from F-195 Reports)
-- ============================================

CREATE TABLE IF NOT EXISTS fiscal_years (
    id INTEGER PRIMARY KEY,
    year_label TEXT UNIQUE NOT NULL,  -- e.g., "2024-25"
    start_date DATE,
    end_date DATE
);

CREATE TABLE IF NOT EXISTS budget_objects (
    id INTEGER PRIMARY KEY,
    object_code INTEGER UNIQUE NOT NULL,  -- 1-9
    name TEXT NOT NULL,
    description TEXT
);

-- Pre-populate budget object codes
INSERT OR IGNORE INTO budget_objects (object_code, name, description) VALUES
(1, 'Certificated Salaries', 'Teacher and certificated staff salaries'),
(2, 'Classified Salaries', 'Support staff and classified employee salaries'),
(3, 'Employee Benefits', 'Benefits and payroll taxes'),
(4, 'Supplies', 'Supplies, instructional resources, noncapitalized items'),
(5, 'Purchased Services', 'Contracted services from external vendors'),
(6, 'Travel', 'Travel and conference expenses'),
(7, 'Capital Outlay', 'Equipment and capital purchases'),
(8, 'Other', 'Miscellaneous expenditures'),
(9, 'Transfers', 'Inter-fund transfers');

CREATE TABLE IF NOT EXISTS budget_items (
    id INTEGER PRIMARY KEY,
    fiscal_year_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    percent_of_total REAL,
    source_document TEXT,  -- e.g., "VPS_2024-25_F-195.pdf"
    source_page INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fiscal_year_id) REFERENCES fiscal_years(id),
    FOREIGN KEY (object_id) REFERENCES budget_objects(id)
);

-- ============================================
-- VENDOR DATA
-- ============================================

CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    dba_name TEXT,  -- "Doing Business As"
    wa_ubi TEXT,    -- WA State UBI number
    address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendor_contracts (
    id INTEGER PRIMARY KEY,
    vendor_id INTEGER NOT NULL,
    contract_number TEXT,
    description TEXT,
    start_date DATE,
    end_date DATE,
    total_value REAL,
    source_document TEXT,
    board_approval_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

CREATE TABLE IF NOT EXISTS vendor_payments (
    id INTEGER PRIMARY KEY,
    vendor_id INTEGER NOT NULL,
    contract_id INTEGER,
    fiscal_year_id INTEGER,
    amount REAL NOT NULL,
    payment_date DATE,
    description TEXT,
    source_document TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id),
    FOREIGN KEY (contract_id) REFERENCES vendor_contracts(id),
    FOREIGN KEY (fiscal_year_id) REFERENCES fiscal_years(id)
);

-- ============================================
-- PEOPLE & ORGANIZATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,  -- e.g., "Board Member", "Director", "Superintendent"
    organization TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS board_votes (
    id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL,
    contract_id INTEGER,
    vote TEXT CHECK(vote IN ('YES', 'NO', 'ABSTAIN', 'ABSENT')),
    meeting_date DATE,
    source_document TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES people(id),
    FOREIGN KEY (contract_id) REFERENCES vendor_contracts(id)
);

-- ============================================
-- EVIDENCE TRACKING
-- ============================================

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,
    filepath TEXT NOT NULL,
    document_type TEXT,  -- 'F-195', 'Contract', 'Board Minutes', etc.
    source_url TEXT,
    download_date DATE,
    file_hash TEXT,  -- SHA-256 for integrity
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_budget_items_year ON budget_items(fiscal_year_id);
CREATE INDEX IF NOT EXISTS idx_budget_items_object ON budget_items(object_id);
CREATE INDEX IF NOT EXISTS idx_vendor_payments_vendor ON vendor_payments(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_payments_year ON vendor_payments(fiscal_year_id);
