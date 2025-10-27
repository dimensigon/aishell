-- PostgreSQL Test Database Initialization Script
-- This script sets up test tables and seed data for integration tests

-- Drop existing tables
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS search_documents CASCADE;
DROP TABLE IF EXISTS analytics CASCADE;

-- Users table with array and JSON types
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles TEXT[] DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table with full-text search
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    category VARCHAR(50),
    tags TEXT[],
    metadata JSONB,
    search_vector TSVECTOR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address JSONB,
    notes TEXT
);

-- Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(10, 2) NOT NULL
);

-- Search documents table for full-text search testing
CREATE TABLE search_documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(100),
    search_vector TSVECTOR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics table for window functions
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    event_value NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_roles ON users USING GIN(roles);
CREATE INDEX idx_users_preferences ON users USING GIN(preferences);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_tags ON products USING GIN(tags);
CREATE INDEX idx_products_metadata ON products USING GIN(metadata);
CREATE INDEX idx_products_search ON products USING GIN(search_vector);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_order_date ON orders(order_date);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

CREATE INDEX idx_search_documents_search ON search_documents USING GIN(search_vector);

CREATE INDEX idx_analytics_user_id ON analytics(user_id);
CREATE INDEX idx_analytics_event_type ON analytics(event_type);
CREATE INDEX idx_analytics_created_at ON analytics(created_at);

-- Create trigger to update search_vector for products
CREATE OR REPLACE FUNCTION update_product_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.name, '') || ' ' || COALESCE(NEW.description, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_product_search_vector
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_search_vector();

-- Create trigger to update search_vector for search_documents
CREATE OR REPLACE FUNCTION update_document_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_document_search_vector
    BEFORE INSERT OR UPDATE ON search_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_document_search_vector();

-- Seed data for users
INSERT INTO users (username, email, password_hash, roles, preferences) VALUES
('john_doe', 'john@example.com', '$2a$10$hashedhashed', ARRAY['user', 'admin'], '{"theme": "dark", "notifications": true}'::jsonb),
('jane_smith', 'jane@example.com', '$2a$10$hashedhashed', ARRAY['user'], '{"theme": "light", "notifications": false}'::jsonb),
('bob_wilson', 'bob@example.com', '$2a$10$hashedhashed', ARRAY['user', 'moderator'], '{"theme": "auto"}'::jsonb),
('alice_brown', 'alice@example.com', '$2a$10$hashedhashed', ARRAY['user'], '{"notifications": true}'::jsonb),
('charlie_davis', 'charlie@example.com', '$2a$10$hashedhashed', ARRAY['user'], '{}'::jsonb);

-- Seed data for customers
INSERT INTO customers (first_name, last_name, email, phone, address) VALUES
('Michael', 'Johnson', 'michael.j@example.com', '555-0101', '{"street": "123 Main St", "city": "New York", "zip": "10001"}'::jsonb),
('Sarah', 'Williams', 'sarah.w@example.com', '555-0102', '{"street": "456 Oak Ave", "city": "Los Angeles", "zip": "90001"}'::jsonb),
('David', 'Martinez', 'david.m@example.com', '555-0103', '{"street": "789 Pine Rd", "city": "Chicago", "zip": "60601"}'::jsonb),
('Emma', 'Garcia', 'emma.g@example.com', '555-0104', '{"street": "321 Elm St", "city": "Houston", "zip": "77001"}'::jsonb),
('James', 'Rodriguez', 'james.r@example.com', '555-0105', '{"street": "654 Maple Dr", "city": "Phoenix", "zip": "85001"}'::jsonb);

-- Seed data for products
INSERT INTO products (name, description, price, stock_quantity, category, tags, metadata) VALUES
('Laptop Pro 15', 'High-performance laptop with 16GB RAM and 512GB SSD', 1299.99, 50, 'Electronics', ARRAY['computer', 'laptop', 'portable'], '{"brand": "TechCorp", "warranty": "2 years"}'::jsonb),
('Wireless Mouse', 'Ergonomic wireless mouse with precision tracking', 29.99, 200, 'Electronics', ARRAY['mouse', 'wireless', 'accessory'], '{"brand": "PeripheralPlus", "warranty": "1 year"}'::jsonb),
('Office Chair', 'Comfortable ergonomic office chair with lumbar support', 249.99, 30, 'Furniture', ARRAY['chair', 'office', 'ergonomic'], '{"brand": "ComfortSeating", "weight_capacity": "300 lbs"}'::jsonb),
('Desk Lamp LED', 'Adjustable LED desk lamp with touch control', 39.99, 100, 'Furniture', ARRAY['lamp', 'lighting', 'led'], '{"brand": "BrightLights", "power": "12W"}'::jsonb),
('Notebook Set', 'Premium notebook set with 3 ruled notebooks', 14.99, 500, 'Stationery', ARRAY['notebook', 'writing', 'paper'], '{"brand": "WritersPro", "pages": 200}'::jsonb),
('Mechanical Keyboard', 'RGB mechanical keyboard with blue switches', 89.99, 75, 'Electronics', ARRAY['keyboard', 'mechanical', 'gaming'], '{"brand": "KeyMaster", "switch_type": "blue"}'::jsonb),
('Standing Desk', 'Electric height-adjustable standing desk', 499.99, 20, 'Furniture', ARRAY['desk', 'standing', 'adjustable'], '{"brand": "ErgoDesk", "height_range": "29-48 inches"}'::jsonb),
('USB-C Hub', '7-in-1 USB-C hub with HDMI and card reader', 49.99, 150, 'Electronics', ARRAY['hub', 'usb-c', 'adapter'], '{"brand": "ConnectAll", "ports": 7}'::jsonb);

-- Seed data for orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address) VALUES
(1, CURRENT_TIMESTAMP - INTERVAL '30 days', 1329.98, 'delivered', '{"street": "123 Main St", "city": "New York", "zip": "10001"}'::jsonb),
(2, CURRENT_TIMESTAMP - INTERVAL '20 days', 279.98, 'delivered', '{"street": "456 Oak Ave", "city": "Los Angeles", "zip": "90001"}'::jsonb),
(3, CURRENT_TIMESTAMP - INTERVAL '15 days', 89.99, 'shipped', '{"street": "789 Pine Rd", "city": "Chicago", "zip": "60601"}'::jsonb),
(1, CURRENT_TIMESTAMP - INTERVAL '10 days', 549.98, 'processing', '{"street": "123 Main St", "city": "New York", "zip": "10001"}'::jsonb),
(4, CURRENT_TIMESTAMP - INTERVAL '5 days', 64.98, 'pending', '{"street": "321 Elm St", "city": "Houston", "zip": "77001"}'::jsonb),
(5, CURRENT_TIMESTAMP - INTERVAL '2 days', 1299.99, 'pending', '{"street": "654 Maple Dr", "city": "Phoenix", "zip": "85001"}'::jsonb);

-- Seed data for order_items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
(1, 1, 1, 1299.99, 1299.99),
(1, 2, 1, 29.99, 29.99),
(2, 3, 1, 249.99, 249.99),
(2, 2, 1, 29.99, 29.99),
(3, 6, 1, 89.99, 89.99),
(4, 7, 1, 499.99, 499.99),
(4, 8, 1, 49.99, 49.99),
(5, 4, 1, 39.99, 39.99),
(5, 5, 1, 14.99, 14.99),
(5, 2, 1, 29.99, 29.99),
(6, 1, 1, 1299.99, 1299.99);

-- Seed data for search_documents
INSERT INTO search_documents (title, content, author) VALUES
('Introduction to PostgreSQL', 'PostgreSQL is a powerful, open source object-relational database system with over 30 years of active development.', 'Tech Writer'),
('Advanced SQL Queries', 'Learn how to write complex SQL queries using window functions, CTEs, and advanced joins.', 'Database Expert'),
('Database Performance Tuning', 'Optimize your database performance with proper indexing, query optimization, and configuration tuning.', 'Performance Guru'),
('NoSQL vs SQL', 'Understanding the differences between NoSQL and SQL databases and when to use each.', 'Architecture Specialist'),
('Data Modeling Best Practices', 'Learn the fundamentals of data modeling and database design for scalable applications.', 'Data Architect');

-- Seed data for analytics
INSERT INTO analytics (user_id, event_type, event_data, event_value, created_at) VALUES
(1, 'page_view', '{"page": "/home", "duration": 45}'::jsonb, 45, CURRENT_TIMESTAMP - INTERVAL '1 day'),
(1, 'click', '{"element": "button", "label": "signup"}'::jsonb, 1, CURRENT_TIMESTAMP - INTERVAL '1 day'),
(2, 'page_view', '{"page": "/products", "duration": 120}'::jsonb, 120, CURRENT_TIMESTAMP - INTERVAL '1 day'),
(2, 'purchase', '{"product_id": 1, "amount": 1299.99}'::jsonb, 1299.99, CURRENT_TIMESTAMP - INTERVAL '1 day'),
(3, 'page_view', '{"page": "/about", "duration": 30}'::jsonb, 30, CURRENT_TIMESTAMP - INTERVAL '12 hours'),
(1, 'page_view', '{"page": "/dashboard", "duration": 90}'::jsonb, 90, CURRENT_TIMESTAMP - INTERVAL '6 hours'),
(4, 'page_view', '{"page": "/help", "duration": 60}'::jsonb, 60, CURRENT_TIMESTAMP - INTERVAL '3 hours'),
(5, 'signup', '{"referrer": "google", "plan": "free"}'::jsonb, 0, CURRENT_TIMESTAMP - INTERVAL '2 hours');

-- Create a materialized view for testing
CREATE MATERIALIZED VIEW product_sales_summary AS
SELECT
    p.id,
    p.name,
    p.category,
    COUNT(oi.id) as total_orders,
    SUM(oi.quantity) as total_quantity_sold,
    SUM(oi.subtotal) as total_revenue
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.category;

-- Create a view for testing
CREATE VIEW customer_order_summary AS
SELECT
    c.id,
    c.first_name,
    c.last_name,
    c.email,
    COUNT(o.id) as total_orders,
    SUM(o.total_amount) as total_spent,
    MAX(o.order_date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.first_name, c.last_name, c.email;

-- Grant permissions (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
