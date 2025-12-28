-- AI-Shell PostgreSQL Initialization Script
-- Creates test schema and sample data for testing

-- Create test schema
CREATE SCHEMA IF NOT EXISTS test_schema;

-- Create sample users table
CREATE TABLE IF NOT EXISTS test_schema.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create sample products table
CREATE TABLE IF NOT EXISTS test_schema.products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sample orders table
CREATE TABLE IF NOT EXISTS test_schema.orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES test_schema.users(id) ON DELETE CASCADE,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sample order_items table
CREATE TABLE IF NOT EXISTS test_schema.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES test_schema.orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES test_schema.products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Insert sample users
INSERT INTO test_schema.users (username, email, full_name) VALUES
    ('john_doe', 'john@example.com', 'John Doe'),
    ('jane_smith', 'jane@example.com', 'Jane Smith'),
    ('bob_wilson', 'bob@example.com', 'Bob Wilson'),
    ('alice_jones', 'alice@example.com', 'Alice Jones'),
    ('charlie_brown', 'charlie@example.com', 'Charlie Brown')
ON CONFLICT (username) DO NOTHING;

-- Insert sample products
INSERT INTO test_schema.products (name, description, price, stock_quantity, category) VALUES
    ('Laptop', 'High-performance laptop', 999.99, 50, 'Electronics'),
    ('Mouse', 'Wireless mouse', 29.99, 200, 'Electronics'),
    ('Keyboard', 'Mechanical keyboard', 79.99, 150, 'Electronics'),
    ('Monitor', '27-inch 4K monitor', 399.99, 75, 'Electronics'),
    ('Headphones', 'Noise-cancelling headphones', 199.99, 100, 'Electronics'),
    ('Desk Chair', 'Ergonomic office chair', 299.99, 30, 'Furniture'),
    ('Desk', 'Standing desk', 499.99, 20, 'Furniture'),
    ('Notebook', 'Spiral notebook pack', 9.99, 500, 'Office Supplies'),
    ('Pen Set', 'Professional pen set', 19.99, 300, 'Office Supplies'),
    ('USB Cable', 'USB-C cable', 14.99, 400, 'Electronics')
ON CONFLICT DO NOTHING;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON test_schema.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON test_schema.users(username);
CREATE INDEX IF NOT EXISTS idx_products_category ON test_schema.products(category);
CREATE INDEX IF NOT EXISTS idx_products_name ON test_schema.products(name);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON test_schema.orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON test_schema.orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON test_schema.order_items(order_id);

-- Create a view for order summaries
CREATE OR REPLACE VIEW test_schema.order_summary AS
SELECT
    o.id AS order_id,
    u.username,
    u.email,
    o.total_amount,
    o.status,
    o.order_date,
    COUNT(oi.id) AS item_count
FROM test_schema.orders o
JOIN test_schema.users u ON o.user_id = u.id
LEFT JOIN test_schema.order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.username, u.email, o.total_amount, o.status, o.order_date;

-- Create a function for updating timestamps
CREATE OR REPLACE FUNCTION test_schema.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON test_schema.users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON test_schema.users
    FOR EACH ROW
    EXECUTE FUNCTION test_schema.update_updated_at_column();

-- Grant permissions (if needed for additional users)
GRANT USAGE ON SCHEMA test_schema TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA test_schema TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA test_schema TO postgres;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'AI-Shell PostgreSQL test database initialized successfully';
    RAISE NOTICE 'Schema: test_schema';
    RAISE NOTICE 'Tables: users, products, orders, order_items';
    RAISE NOTICE 'Sample data loaded';
END $$;
