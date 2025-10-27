-- Oracle Database Initialization Script
-- Sets up test schema in FREEPDB1, creates tables, sample data, sequences, and triggers

-- Connect to FREEPDB1 pluggable database
ALTER SESSION SET CONTAINER = FREEPDB1;

-- Create test user if not exists
DECLARE
    user_exists NUMBER;
BEGIN
    SELECT COUNT(*) INTO user_exists FROM all_users WHERE username = 'TESTUSER';
    IF user_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE USER testuser IDENTIFIED BY testpass123';
        EXECUTE IMMEDIATE 'GRANT CONNECT, RESOURCE, DBA TO testuser';
        EXECUTE IMMEDIATE 'GRANT UNLIMITED TABLESPACE TO testuser';
    END IF;
END;
/

-- Connect as test user
CONNECT testuser/testpass123@localhost:1521/FREEPDB1;

-- Drop existing tables
BEGIN
    FOR cur_rec IN (SELECT object_name FROM user_objects WHERE object_type = 'TABLE' AND object_name IN ('INVOICE_ITEMS', 'INVOICES', 'ITEMS', 'CUSTOMERS')) LOOP
        EXECUTE IMMEDIATE 'DROP TABLE ' || cur_rec.object_name || ' CASCADE CONSTRAINTS PURGE';
    END LOOP;

    FOR cur_rec IN (SELECT sequence_name FROM user_sequences WHERE sequence_name LIKE '%_SEQ') LOOP
        EXECUTE IMMEDIATE 'DROP SEQUENCE ' || cur_rec.sequence_name;
    END LOOP;
END;
/

-- ====================================
-- CUSTOMERS Table
-- ====================================
CREATE TABLE customers (
    customer_id NUMBER(10) PRIMARY KEY,
    customer_number VARCHAR2(20) UNIQUE NOT NULL,
    company_name VARCHAR2(200) NOT NULL,
    contact_name VARCHAR2(100),
    email VARCHAR2(100) UNIQUE NOT NULL,
    phone VARCHAR2(20),
    address_line1 VARCHAR2(200),
    address_line2 VARCHAR2(200),
    city VARCHAR2(100),
    state VARCHAR2(50),
    postal_code VARCHAR2(20),
    country VARCHAR2(50) DEFAULT 'USA',
    credit_rating VARCHAR2(1) CHECK (credit_rating IN ('A', 'B', 'C', 'D')),
    credit_limit NUMBER(12, 2) DEFAULT 50000.00,
    account_balance NUMBER(12, 2) DEFAULT 0.00,
    payment_terms NUMBER(3) DEFAULT 30,
    tax_id VARCHAR2(20),
    active CHAR(1) DEFAULT 'Y' CHECK (active IN ('Y', 'N')),
    notes CLOB,
    created_date DATE DEFAULT SYSDATE,
    modified_date DATE DEFAULT SYSDATE,
    created_by VARCHAR2(50) DEFAULT USER,
    modified_by VARCHAR2(50) DEFAULT USER
);

-- Create sequence for customers
CREATE SEQUENCE customers_seq START WITH 1 INCREMENT BY 1 NOCACHE;

-- Create index on customers
CREATE INDEX idx_cust_company ON customers(company_name);
CREATE INDEX idx_cust_email ON customers(email);
CREATE INDEX idx_cust_active ON customers(active);
CREATE INDEX idx_cust_rating ON customers(credit_rating);

-- Insert sample customers
INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-001', 'Acme Corporation', 'John Smith', 'john.smith@acme.com', '+1-555-0101', '100 Main Street', 'New York', 'NY', '10001', 'USA', 'A', 100000.00, 45230.50, 30, '12-3456789', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-002', 'TechStart Inc', 'Sarah Johnson', 'sarah.j@techstart.io', '+1-555-0202', '500 Tech Boulevard', 'San Francisco', 'CA', '94105', 'USA', 'B', 75000.00, 28450.00, 45, '98-7654321', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-003', 'Global Solutions Ltd', 'Michael Chen', 'm.chen@globalsol.com', '+1-555-0303', '250 Business Park', 'Austin', 'TX', '78701', 'USA', 'A', 150000.00, 67890.25, 60, '45-6789012', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-004', 'Enterprise Systems Corp', 'Emily Davis', 'e.davis@entsys.com', '+1-555-0404', '1000 Corporate Drive', 'Chicago', 'IL', '60601', 'USA', 'A', 200000.00, 125600.75, 30, '78-9012345', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-005', 'Digital Innovations LLC', 'Robert Martinez', 'r.martinez@diginno.com', '+1-555-0505', '777 Innovation Way', 'Seattle', 'WA', '98101', 'USA', 'B', 80000.00, 15320.00, 45, '23-4567890', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-006', 'Metro Retail Partners', 'Lisa Anderson', 'l.anderson@metro.com', '+1-555-0606', '333 Retail Plaza', 'Boston', 'MA', '02101', 'USA', 'C', 50000.00, 42850.50, 30, '56-7890123', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-007', 'Cloud Services Group', 'David Lee', 'd.lee@cloudservices.net', '+1-555-0707', '888 Cloud Lane', 'Denver', 'CO', '80202', 'USA', 'A', 175000.00, 89450.00, 60, '89-0123456', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-008', 'Manufacturing Plus Inc', 'Jennifer White', 'j.white@mfgplus.com', '+1-555-0808', '1500 Industrial Parkway', 'Detroit', 'MI', '48201', 'USA', 'B', 120000.00, 58230.25, 45, '34-5678901', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-009', 'Financial Advisors LLC', 'Thomas Brown', 't.brown@finadvisors.com', '+1-555-0909', '2000 Wall Street', 'New York', 'NY', '10005', 'USA', 'A', 250000.00, 156780.00, 30, '67-8901234', 'Y');

INSERT INTO customers (customer_id, customer_number, company_name, contact_name, email, phone, address_line1, city, state, postal_code, country, credit_rating, credit_limit, account_balance, payment_terms, tax_id, active)
VALUES (customers_seq.NEXTVAL, 'CUST-010', 'Healthcare Solutions Corp', 'Amanda Garcia', 'a.garcia@healthsol.com', '+1-555-1010', '3500 Medical Center', 'Phoenix', 'AZ', '85001', 'USA', 'A', 180000.00, 72450.50, 60, '90-1234567', 'Y');

-- ====================================
-- ITEMS Table
-- ====================================
CREATE TABLE items (
    item_id NUMBER(10) PRIMARY KEY,
    item_code VARCHAR2(50) UNIQUE NOT NULL,
    item_name VARCHAR2(200) NOT NULL,
    description VARCHAR2(4000),
    category VARCHAR2(50),
    unit_of_measure VARCHAR2(20) DEFAULT 'EA',
    unit_price NUMBER(10, 2) NOT NULL,
    cost_price NUMBER(10, 2),
    quantity_on_hand NUMBER(10) DEFAULT 0,
    reorder_level NUMBER(10) DEFAULT 10,
    reorder_quantity NUMBER(10) DEFAULT 50,
    weight_kg NUMBER(8, 2),
    is_taxable CHAR(1) DEFAULT 'Y' CHECK (is_taxable IN ('Y', 'N')),
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    manufacturer VARCHAR2(100),
    model_number VARCHAR2(50),
    barcode VARCHAR2(50),
    created_date DATE DEFAULT SYSDATE,
    modified_date DATE DEFAULT SYSDATE
);

-- Create sequence for items
CREATE SEQUENCE items_seq START WITH 1 INCREMENT BY 1 NOCACHE;

-- Create indexes on items
CREATE INDEX idx_item_category ON items(category);
CREATE INDEX idx_item_active ON items(is_active);
CREATE INDEX idx_item_name ON items(item_name);

-- Insert sample items
INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-001', 'Professional Software License', 'Annual license for professional software suite', 'Software', 'EA', 1299.99, 650.00, 500, 50, 0, 'Y', 'Y', 'Microsoft');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-002', 'Cloud Storage 1TB', 'Monthly subscription for 1TB cloud storage', 'Services', 'MO', 99.99, 35.00, 9999, 100, 0, 'Y', 'Y', 'Amazon Web Services');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-003', 'Network Switch 48-Port', 'Gigabit ethernet switch with 48 ports', 'Hardware', 'EA', 2499.99, 1500.00, 45, 10, 4.5, 'Y', 'Y', 'Cisco');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-004', 'Wireless Access Point', 'Enterprise-grade dual-band wireless AP', 'Hardware', 'EA', 899.99, 550.00, 78, 15, 1.2, 'Y', 'Y', 'Ubiquiti');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-005', 'Database Server License', 'Enterprise database server license (per core)', 'Software', 'EA', 4999.99, 2800.00, 120, 20, 0, 'Y', 'Y', 'Oracle');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-006', 'Managed Security Service', 'Monthly managed security and monitoring service', 'Services', 'MO', 2499.99, 1200.00, 9999, 50, 0, 'Y', 'Y', 'CrowdStrike');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-007', 'Workstation Desktop', 'High-performance desktop workstation', 'Hardware', 'EA', 3499.99, 2100.00, 32, 8, 12.5, 'Y', 'Y', 'Dell');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-008', 'Backup Solution Enterprise', 'Enterprise backup and disaster recovery solution', 'Software', 'EA', 8999.99, 5200.00, 65, 10, 0, 'Y', 'Y', 'Veeam');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-009', 'Professional Monitor 27"', '4K professional display monitor', 'Hardware', 'EA', 899.99, 520.00, 95, 15, 6.8, 'Y', 'Y', 'LG');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-010', 'Collaboration Suite License', 'Annual license for team collaboration platform', 'Software', 'EA', 199.99, 85.00, 850, 100, 0, 'Y', 'Y', 'Slack');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-011', 'SSD Storage 2TB', 'Enterprise-grade solid state drive 2TB', 'Hardware', 'EA', 599.99, 350.00, 125, 25, 0.18, 'Y', 'Y', 'Samsung');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-012', 'VPN Service Enterprise', 'Monthly enterprise VPN service subscription', 'Services', 'MO', 499.99, 200.00, 9999, 50, 0, 'Y', 'Y', 'NordVPN');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-013', 'Firewall Appliance', 'Next-generation firewall appliance', 'Hardware', 'EA', 5999.99, 3800.00, 28, 8, 8.2, 'Y', 'Y', 'Fortinet');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-014', 'Professional Consulting', 'Hourly rate for professional IT consulting', 'Services', 'HR', 199.99, 90.00, 9999, 100, 0, 'Y', 'Y', 'Internal');

INSERT INTO items (item_id, item_code, item_name, description, category, unit_of_measure, unit_price, cost_price, quantity_on_hand, reorder_level, weight_kg, is_taxable, is_active, manufacturer)
VALUES (items_seq.NEXTVAL, 'ITM-015', 'UPS Battery Backup', 'Uninterruptible power supply 1500VA', 'Hardware', 'EA', 299.99, 180.00, 67, 15, 15.5, 'Y', 'Y', 'APC');

-- ====================================
-- INVOICES Table
-- ====================================
CREATE TABLE invoices (
    invoice_id NUMBER(10) PRIMARY KEY,
    invoice_number VARCHAR2(50) UNIQUE NOT NULL,
    customer_id NUMBER(10) NOT NULL,
    invoice_date DATE DEFAULT SYSDATE,
    due_date DATE,
    subtotal NUMBER(12, 2) NOT NULL,
    tax_amount NUMBER(12, 2) DEFAULT 0.00,
    shipping_amount NUMBER(12, 2) DEFAULT 0.00,
    total_amount NUMBER(12, 2) NOT NULL,
    amount_paid NUMBER(12, 2) DEFAULT 0.00,
    balance_due NUMBER(12, 2),
    status VARCHAR2(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'SENT', 'PAID', 'PARTIAL', 'OVERDUE', 'CANCELLED')),
    payment_method VARCHAR2(30),
    payment_terms NUMBER(3) DEFAULT 30,
    reference_number VARCHAR2(50),
    notes CLOB,
    created_date DATE DEFAULT SYSDATE,
    modified_date DATE DEFAULT SYSDATE,
    created_by VARCHAR2(50) DEFAULT USER,
    modified_by VARCHAR2(50) DEFAULT USER,
    CONSTRAINT fk_inv_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Create sequence for invoices
CREATE SEQUENCE invoices_seq START WITH 1 INCREMENT BY 1 NOCACHE;

-- Create indexes on invoices
CREATE INDEX idx_inv_customer ON invoices(customer_id);
CREATE INDEX idx_inv_status ON invoices(status);
CREATE INDEX idx_inv_date ON invoices(invoice_date);
CREATE INDEX idx_inv_due_date ON invoices(due_date);

-- Insert sample invoices
INSERT INTO invoices (invoice_id, invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, shipping_amount, total_amount, amount_paid, balance_due, status, payment_method, payment_terms)
VALUES (invoices_seq.NEXTVAL, 'INV-2025-0001', 1, TO_DATE('2025-10-01', 'YYYY-MM-DD'), TO_DATE('2025-10-31', 'YYYY-MM-DD'), 12999.90, 1040.00, 0.00, 14039.90, 14039.90, 0.00, 'PAID', 'Wire Transfer', 30);

INSERT INTO invoices (invoice_id, invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, shipping_amount, total_amount, amount_paid, balance_due, status, payment_method, payment_terms)
VALUES (invoices_seq.NEXTVAL, 'INV-2025-0002', 2, TO_DATE('2025-10-05', 'YYYY-MM-DD'), TO_DATE('2025-11-19', 'YYYY-MM-DD'), 4599.94, 368.00, 150.00, 5117.94, 2500.00, 2617.94, 'PARTIAL', 'Check', 45);

INSERT INTO invoices (invoice_id, invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, shipping_amount, total_amount, amount_paid, balance_due, status, payment_method, payment_terms)
VALUES (invoices_seq.NEXTVAL, 'INV-2025-0003', 3, TO_DATE('2025-10-10', 'YYYY-MM-DD'), TO_DATE('2025-12-09', 'YYYY-MM-DD'), 27999.85, 2240.00, 0.00, 30239.85, 0.00, 30239.85, 'SENT', NULL, 60);

INSERT INTO invoices (invoice_id, invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, shipping_amount, total_amount, amount_paid, balance_due, status, payment_method, payment_terms)
VALUES (invoices_seq.NEXTVAL, 'INV-2025-0004', 4, TO_DATE('2025-09-15', 'YYYY-MM-DD'), TO_DATE('2025-10-15', 'YYYY-MM-DD'), 45678.50, 3654.28, 0.00, 49332.78, 0.00, 49332.78, 'OVERDUE', NULL, 30);

INSERT INTO invoices (invoice_id, invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, shipping_amount, total_amount, amount_paid, balance_due, status, payment_method, payment_terms)
VALUES (invoices_seq.NEXTVAL, 'INV-2025-0005', 7, TO_DATE('2025-10-20', 'YYYY-MM-DD'), TO_DATE('2025-12-19', 'YYYY-MM-DD'), 18499.90, 1480.00, 0.00, 19979.90, 19979.90, 0.00, 'PAID', 'Credit Card', 60);

INSERT INTO invoices (invoice_id, invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, shipping_amount, total_amount, amount_paid, balance_due, status, payment_method, payment_terms)
VALUES (invoices_seq.NEXTVAL, 'INV-2025-0006', 9, TO_DATE('2025-10-25', 'YYYY-MM-DD'), TO_DATE('2025-11-24', 'YYYY-MM-DD'), 32450.75, 2596.06, 0.00, 35046.81, 0.00, 35046.81, 'SENT', NULL, 30);

-- ====================================
-- INVOICE_ITEMS Table
-- ====================================
CREATE TABLE invoice_items (
    invoice_item_id NUMBER(10) PRIMARY KEY,
    invoice_id NUMBER(10) NOT NULL,
    item_id NUMBER(10) NOT NULL,
    line_number NUMBER(3) NOT NULL,
    quantity NUMBER(10, 2) NOT NULL,
    unit_price NUMBER(10, 2) NOT NULL,
    discount_percent NUMBER(5, 2) DEFAULT 0.00,
    discount_amount NUMBER(10, 2) DEFAULT 0.00,
    line_total NUMBER(12, 2) NOT NULL,
    description VARCHAR2(4000),
    CONSTRAINT fk_invitem_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    CONSTRAINT fk_invitem_item FOREIGN KEY (item_id) REFERENCES items(item_id),
    CONSTRAINT uq_inv_line UNIQUE (invoice_id, line_number)
);

-- Create sequence for invoice items
CREATE SEQUENCE invoice_items_seq START WITH 1 INCREMENT BY 1 NOCACHE;

-- Create indexes on invoice_items
CREATE INDEX idx_invitem_invoice ON invoice_items(invoice_id);
CREATE INDEX idx_invitem_item ON invoice_items(item_id);

-- Insert sample invoice items
-- Invoice 1 items
INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 1, 1, 1, 10, 1299.99, 0, 0, 12999.90);

-- Invoice 2 items
INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 2, 3, 1, 1, 2499.99, 0, 0, 2499.99);

INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 2, 4, 2, 2, 899.99, 5, 90.00, 1709.98);

INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 2, 9, 3, 1, 899.99, 10, 90.00, 809.99);

-- Invoice 3 items
INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 3, 5, 1, 5, 4999.99, 0, 0, 24999.95);

INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 3, 7, 2, 1, 3499.99, 0, 0, 3499.99);

-- Invoice 4 items
INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 4, 8, 1, 3, 8999.99, 0, 0, 26999.97);

INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 4, 13, 2, 2, 5999.99, 0, 0, 11999.98);

INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 4, 3, 3, 3, 2499.99, 10, 750.00, 6749.97);

-- Invoice 5 items
INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 5, 7, 1, 5, 3499.99, 0, 0, 17499.95);

INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 5, 15, 2, 2, 299.99, 0, 0, 599.98);

-- Invoice 6 items
INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 6, 14, 1, 150, 199.99, 0, 0, 29998.50);

INSERT INTO invoice_items (invoice_item_id, invoice_id, item_id, line_number, quantity, unit_price, discount_percent, discount_amount, line_total)
VALUES (invoice_items_seq.NEXTVAL, 6, 11, 2, 4, 599.99, 0, 0, 2399.96);

-- ====================================
-- CREATE TRIGGERS
-- ====================================

-- Trigger to update modified_date on customers
CREATE OR REPLACE TRIGGER trg_customers_update
BEFORE UPDATE ON customers
FOR EACH ROW
BEGIN
    :NEW.modified_date := SYSDATE;
    :NEW.modified_by := USER;
END;
/

-- Trigger to update modified_date on items
CREATE OR REPLACE TRIGGER trg_items_update
BEFORE UPDATE ON items
FOR EACH ROW
BEGIN
    :NEW.modified_date := SYSDATE;
END;
/

-- Trigger to update modified_date on invoices
CREATE OR REPLACE TRIGGER trg_invoices_update
BEFORE UPDATE ON invoices
FOR EACH ROW
BEGIN
    :NEW.modified_date := SYSDATE;
    :NEW.modified_by := USER;
END;
/

-- Trigger to calculate balance_due automatically
CREATE OR REPLACE TRIGGER trg_invoices_balance
BEFORE INSERT OR UPDATE ON invoices
FOR EACH ROW
BEGIN
    :NEW.balance_due := :NEW.total_amount - NVL(:NEW.amount_paid, 0);

    -- Update status based on payment
    IF :NEW.balance_due = 0 AND :NEW.total_amount > 0 THEN
        :NEW.status := 'PAID';
    ELSIF :NEW.balance_due > 0 AND :NEW.amount_paid > 0 THEN
        :NEW.status := 'PARTIAL';
    ELSIF :NEW.due_date < SYSDATE AND :NEW.balance_due > 0 THEN
        :NEW.status := 'OVERDUE';
    END IF;
END;
/

-- ====================================
-- CREATE VIEWS
-- ====================================

-- Customer account summary view
CREATE OR REPLACE VIEW customer_account_summary AS
SELECT
    c.customer_id,
    c.customer_number,
    c.company_name,
    c.credit_rating,
    c.credit_limit,
    c.account_balance,
    COUNT(i.invoice_id) AS total_invoices,
    SUM(CASE WHEN i.status = 'PAID' THEN i.total_amount ELSE 0 END) AS total_paid,
    SUM(CASE WHEN i.status IN ('SENT', 'PARTIAL', 'OVERDUE') THEN i.balance_due ELSE 0 END) AS total_outstanding,
    SUM(CASE WHEN i.status = 'OVERDUE' THEN i.balance_due ELSE 0 END) AS overdue_amount
FROM customers c
LEFT JOIN invoices i ON c.customer_id = i.customer_id
GROUP BY c.customer_id, c.customer_number, c.company_name, c.credit_rating, c.credit_limit, c.account_balance;

-- Invoice details view
CREATE OR REPLACE VIEW invoice_details AS
SELECT
    i.invoice_id,
    i.invoice_number,
    i.invoice_date,
    i.due_date,
    c.customer_number,
    c.company_name,
    i.subtotal,
    i.tax_amount,
    i.shipping_amount,
    i.total_amount,
    i.amount_paid,
    i.balance_due,
    i.status,
    CASE
        WHEN i.status = 'OVERDUE' THEN TRUNC(SYSDATE - i.due_date)
        ELSE 0
    END AS days_overdue
FROM invoices i
JOIN customers c ON i.customer_id = c.customer_id;

-- Item sales summary view
CREATE OR REPLACE VIEW item_sales_summary AS
SELECT
    itm.item_id,
    itm.item_code,
    itm.item_name,
    itm.category,
    itm.unit_price,
    itm.quantity_on_hand,
    COUNT(DISTINCT ii.invoice_id) AS times_sold,
    NVL(SUM(ii.quantity), 0) AS total_quantity_sold,
    NVL(SUM(ii.line_total), 0) AS total_revenue
FROM items itm
LEFT JOIN invoice_items ii ON itm.item_id = ii.item_id
LEFT JOIN invoices i ON ii.invoice_id = i.invoice_id AND i.status != 'CANCELLED'
GROUP BY itm.item_id, itm.item_code, itm.item_name, itm.category, itm.unit_price, itm.quantity_on_hand;

-- ====================================
-- Summary Output
-- ====================================
DECLARE
    v_customer_count NUMBER;
    v_item_count NUMBER;
    v_invoice_count NUMBER;
    v_invoice_item_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_customer_count FROM customers;
    SELECT COUNT(*) INTO v_item_count FROM items;
    SELECT COUNT(*) INTO v_invoice_count FROM invoices;
    SELECT COUNT(*) INTO v_invoice_item_count FROM invoice_items;

    DBMS_OUTPUT.PUT_LINE('Oracle Database initialization complete!');
    DBMS_OUTPUT.PUT_LINE('Database: FREEPDB1');
    DBMS_OUTPUT.PUT_LINE('Schema: TESTUSER');
    DBMS_OUTPUT.PUT_LINE(v_customer_count || ' customers created');
    DBMS_OUTPUT.PUT_LINE(v_item_count || ' items created');
    DBMS_OUTPUT.PUT_LINE(v_invoice_count || ' invoices created');
    DBMS_OUTPUT.PUT_LINE(v_invoice_item_count || ' invoice items created');
    DBMS_OUTPUT.PUT_LINE('Sequences, indexes, triggers, and views created successfully');
END;
/

COMMIT;
