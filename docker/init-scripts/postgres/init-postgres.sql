-- PostgreSQL Initialization Script
-- Sets up test schema, tables, sample data, indexes, and constraints

-- Create test schema
CREATE SCHEMA IF NOT EXISTS testdb;
SET search_path TO testdb;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ====================================
-- USERS Table
-- ====================================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'moderator', 'user')),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Insert sample users
INSERT INTO users (username, email, first_name, last_name, password_hash, role, active, created_at, last_login) VALUES
('admin', 'admin@example.com', 'System', 'Administrator', '$2b$10$abcdefghijklmnopqrstuv', 'admin', true, '2024-01-01', '2025-10-27'),
('jdoe', 'john.doe@example.com', 'John', 'Doe', '$2b$10$xyz123456789abcdefghij', 'user', true, '2024-02-15', '2025-10-26'),
('jsmith', 'jane.smith@example.com', 'Jane', 'Smith', '$2b$10$lmnopqrstuvwxyz1234567', 'moderator', true, '2024-03-20', '2025-10-25'),
('bwilson', 'bob.wilson@example.com', 'Bob', 'Wilson', '$2b$10$qwertyuiop1234567890ab', 'user', true, '2024-04-10', '2025-10-24'),
('ajohnson', 'alice.johnson@example.com', 'Alice', 'Johnson', '$2b$10$asdfghjkl0987654321zxc', 'user', false, '2024-05-05', '2025-08-15'),
('cbrown', 'charlie.brown@example.com', 'Charlie', 'Brown', '$2b$10$mnbvcxz0987654321qwert', 'user', true, '2024-06-12', '2025-10-27'),
('ewhite', 'emma.white@example.com', 'Emma', 'White', '$2b$10$poiuytrewq0987654321as', 'moderator', true, '2024-07-18', '2025-10-23'),
('dgarcia', 'david.garcia@example.com', 'David', 'Garcia', '$2b$10$lkjhgfdsa0987654321zxc', 'user', true, '2024-08-22', '2025-10-22');

-- ====================================
-- CUSTOMERS Table
-- ====================================
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    company_name VARCHAR(100),
    phone VARCHAR(20),
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    credit_limit DECIMAL(10, 2) DEFAULT 5000.00,
    account_balance DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample customers
INSERT INTO customers (user_id, company_name, phone, address_line1, city, state, postal_code, country, credit_limit, account_balance) VALUES
(2, 'Tech Solutions Inc', '+1-415-555-0101', '123 Market St', 'San Francisco', 'CA', '94102', 'USA', 25000.00, 5420.50),
(3, 'Design Studio LLC', '+1-212-555-0202', '456 Broadway', 'New York', 'NY', '10013', 'USA', 15000.00, 2150.00),
(4, NULL, '+1-512-555-0303', '789 Congress Ave', 'Austin', 'TX', '78701', 'USA', 10000.00, 850.25),
(6, 'Development Corp', '+1-206-555-0404', '321 Pine St', 'Seattle', 'WA', '98101', 'USA', 20000.00, 12500.75),
(8, NULL, '+1-303-555-0505', '654 Larimer St', 'Denver', 'CO', '80202', 'USA', 8000.00, 325.00),
(NULL, 'Retail Partners', '+1-305-555-0606', '987 Ocean Dr', 'Miami', 'FL', '33139', 'USA', 30000.00, 18750.00);

-- ====================================
-- PRODUCTS Table
-- ====================================
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    cost DECIMAL(10, 2) CHECK (cost >= 0),
    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_level INTEGER DEFAULT 10,
    weight_kg DECIMAL(8, 2),
    dimensions_cm VARCHAR(50),
    manufacturer VARCHAR(100),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample products
INSERT INTO products (sku, name, description, category, price, cost, stock_quantity, reorder_level, weight_kg, dimensions_cm, manufacturer, active) VALUES
('LAPTOP-MBP16-001', 'MacBook Pro 16"', 'High-performance laptop with M3 Pro chip, 32GB RAM, 1TB SSD', 'Electronics', 2499.99, 1800.00, 45, 10, 2.15, '35.79x24.81x1.68', 'Apple', true),
('PHONE-IP15PRO-002', 'iPhone 15 Pro', 'Latest flagship smartphone with A17 Pro chip', 'Electronics', 999.99, 650.00, 120, 20, 0.187, '14.67x7.08x0.83', 'Apple', true),
('DESK-STAND-003', 'Standing Desk Pro', 'Electric height-adjustable desk with bamboo top', 'Furniture', 599.99, 350.00, 28, 5, 35.5, '152.4x76.2x110', 'ErgoDesk', true),
('CHAIR-ERGO-004', 'Ergonomic Office Chair', 'Premium mesh chair with lumbar support', 'Furniture', 449.99, 280.00, 0, 15, 18.2, '68x68x120', 'ComfortSeating', true),
('MONITOR-4K-005', '4K UHD Monitor 27"', 'Professional IPS display with USB-C', 'Electronics', 699.99, 450.00, 67, 12, 5.8, '61.3x45.8x20.5', 'Dell', true),
('KEYBOARD-MECH-006', 'Mechanical Keyboard RGB', 'Cherry MX switches with programmable RGB', 'Electronics', 149.99, 75.00, 95, 25, 1.2, '43.5x13.5x3.8', 'Corsair', true),
('MOUSE-WIRELESS-007', 'Wireless Ergonomic Mouse', 'Precision optical mouse with 7 buttons', 'Electronics', 79.99, 35.00, 150, 30, 0.125, '12.6x7.8x4.3', 'Logitech', true),
('LAMP-LED-008', 'LED Desk Lamp', 'Adjustable color temperature desk lamp', 'Furniture', 89.99, 45.00, 72, 20, 1.5, '48x15x15', 'BenQ', true),
('WEBCAM-HD-009', '1080p Webcam', 'Full HD webcam with auto-focus and stereo mic', 'Electronics', 129.99, 70.00, 88, 15, 0.155, '9.4x5.8x7.1', 'Logitech', true),
('HEADSET-NC-010', 'Noise Cancelling Headset', 'Professional headset with active noise cancellation', 'Electronics', 299.99, 180.00, 63, 10, 0.280, '18.5x17.2x8.3', 'Sony', true),
('TABLET-IPAD-011', 'iPad Air 11"', 'Tablet with M2 chip and Apple Pencil support', 'Electronics', 599.99, 400.00, 54, 12, 0.462, '24.76x17.85x0.61', 'Apple', true),
('DOCKING-USB-012', 'USB-C Docking Station', 'Multi-port hub with dual 4K display support', 'Electronics', 199.99, 110.00, 41, 15, 0.520, '20x8x3', 'CalDigit', true),
('SPEAKER-BT-013', 'Bluetooth Speaker', 'Portable speaker with 360° sound', 'Electronics', 149.99, 80.00, 125, 20, 0.680, '10.2x10.2x19.5', 'Bose', true),
('CABLE-USBC-014', 'USB-C Cable 2m', 'Thunderbolt 4 certified cable', 'Electronics', 39.99, 15.00, 280, 50, 0.085, '200x2x1', 'Anker', true),
('STAND-LAPTOP-015', 'Aluminum Laptop Stand', 'Adjustable height laptop stand', 'Furniture', 59.99, 28.00, 156, 25, 1.1, '28x22x6', 'Rain Design', true);

-- ====================================
-- ORDERS Table
-- ====================================
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    shipping_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
    payment_method VARCHAR(30),
    shipping_address TEXT,
    tracking_number VARCHAR(50),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    notes TEXT
);

-- Insert sample orders
INSERT INTO orders (order_number, customer_id, order_date, subtotal, tax_amount, shipping_amount, total_amount, status, payment_method, shipping_address, tracking_number, shipped_at, delivered_at) VALUES
('ORD-2025-0001', 1, '2025-10-01 10:30:00', 2649.98, 212.00, 0.00, 2861.98, 'delivered', 'Credit Card', '123 Market St, San Francisco, CA 94102', 'TRK-1234567890', '2025-10-02 14:00:00', '2025-10-05 16:30:00'),
('ORD-2025-0002', 2, '2025-10-15 14:20:00', 1049.98, 84.00, 49.99, 1183.97, 'delivered', 'PayPal', '456 Broadway, New York, NY 10013', 'TRK-2345678901', '2025-10-16 09:00:00', '2025-10-19 11:45:00'),
('ORD-2025-0003', 4, '2025-10-20 09:15:00', 1399.98, 112.00, 0.00, 1511.98, 'delivered', 'Credit Card', '321 Pine St, Seattle, WA 98101', 'TRK-3456789012', '2025-10-21 10:30:00', '2025-10-24 14:20:00'),
('ORD-2025-0004', 1, '2025-10-22 16:45:00', 4598.93, 367.91, 0.00, 4966.84, 'shipped', 'Wire Transfer', '123 Market St, San Francisco, CA 94102', 'TRK-4567890123', '2025-10-23 08:00:00', NULL),
('ORD-2025-0005', 3, '2025-10-25 11:30:00', 689.95, 55.20, 29.99, 775.14, 'processing', 'Credit Card', '789 Congress Ave, Austin, TX 78701', NULL, NULL, NULL),
('ORD-2025-0006', 2, '2025-10-26 13:10:00', 1549.96, 124.00, 0.00, 1673.96, 'pending', 'PayPal', '456 Broadway, New York, NY 10013', NULL, NULL, NULL);

-- ====================================
-- ORDER_ITEMS Table
-- ====================================
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0.00,
    line_total DECIMAL(10, 2) NOT NULL
);

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percent, line_total) VALUES
-- Order 1
(1, 1, 1, 2499.99, 0.00, 2499.99),
(1, 6, 1, 149.99, 0.00, 149.99),
-- Order 2
(2, 3, 1, 599.99, 0.00, 599.99),
(2, 4, 1, 449.99, 0.00, 449.99),
-- Order 3
(3, 5, 2, 699.99, 0.00, 1399.98),
-- Order 4
(4, 1, 1, 2499.99, 0.00, 2499.99),
(4, 11, 1, 599.99, 0.00, 599.99),
(4, 5, 1, 699.99, 0.00, 699.99),
(4, 10, 2, 299.99, 10.00, 539.98),
(4, 7, 3, 79.99, 5.00, 227.97),
-- Order 5
(5, 7, 2, 79.99, 0.00, 159.98),
(5, 13, 1, 149.99, 0.00, 149.99),
(5, 14, 10, 39.99, 5.00, 379.98),
-- Order 6
(6, 9, 2, 129.99, 0.00, 259.98),
(6, 12, 1, 199.99, 0.00, 199.99),
(6, 15, 3, 59.99, 15.00, 152.97),
(6, 8, 2, 89.99, 10.00, 161.98),
(6, 6, 5, 149.99, 0.00, 749.95);

-- ====================================
-- CREATE INDEXES
-- ====================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(active);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Customers indexes
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_company ON customers(company_name);
CREATE INDEX idx_customers_city_state ON customers(city, state);

-- Products indexes
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_stock ON products(stock_quantity);
CREATE INDEX idx_products_active ON products(active);
CREATE INDEX idx_products_name ON products(name);

-- Orders indexes
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_order_date ON orders(order_date DESC);
CREATE INDEX idx_orders_total ON orders(total_amount);

-- Order Items indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- ====================================
-- CREATE VIEWS
-- ====================================

-- Customer order summary view
CREATE OR REPLACE VIEW customer_order_summary AS
SELECT
    c.customer_id,
    c.company_name,
    u.username,
    COUNT(o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_spent,
    MAX(o.order_date) AS last_order_date,
    c.account_balance,
    c.credit_limit
FROM customers c
LEFT JOIN users u ON c.user_id = u.user_id
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name, u.username, c.account_balance, c.credit_limit;

-- Product sales summary view
CREATE OR REPLACE VIEW product_sales_summary AS
SELECT
    p.product_id,
    p.sku,
    p.name,
    p.category,
    p.price,
    p.stock_quantity,
    COALESCE(SUM(oi.quantity), 0) AS total_sold,
    COALESCE(SUM(oi.line_total), 0) AS total_revenue,
    COUNT(DISTINCT oi.order_id) AS number_of_orders
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.sku, p.name, p.category, p.price, p.stock_quantity;

-- ====================================
-- CREATE FUNCTIONS
-- ====================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ====================================
-- GRANT PERMISSIONS
-- ====================================
GRANT ALL PRIVILEGES ON SCHEMA testdb TO testuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA testdb TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA testdb TO testuser;

-- Summary
SELECT 'PostgreSQL initialization complete!' AS status;
SELECT 'Schema: testdb' AS info;
SELECT COUNT(*) || ' users created' AS users FROM users;
SELECT COUNT(*) || ' customers created' AS customers FROM customers;
SELECT COUNT(*) || ' products created' AS products FROM products;
SELECT COUNT(*) || ' orders created' AS orders FROM orders;
SELECT COUNT(*) || ' order items created' AS order_items FROM order_items;
