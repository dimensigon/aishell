-- AI-Shell MySQL Initialization Script
-- Creates test schema and sample data for testing

USE testdb;

-- Create sample users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create sample products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create sample orders table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create sample order_items table
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample users
INSERT INTO users (username, email, full_name) VALUES
    ('john_doe', 'john@example.com', 'John Doe'),
    ('jane_smith', 'jane@example.com', 'Jane Smith'),
    ('bob_wilson', 'bob@example.com', 'Bob Wilson'),
    ('alice_jones', 'alice@example.com', 'Alice Jones'),
    ('charlie_brown', 'charlie@example.com', 'Charlie Brown')
ON DUPLICATE KEY UPDATE username=username;

-- Insert sample products
INSERT INTO products (name, description, price, stock_quantity, category) VALUES
    ('Laptop', 'High-performance laptop', 999.99, 50, 'Electronics'),
    ('Mouse', 'Wireless mouse', 29.99, 200, 'Electronics'),
    ('Keyboard', 'Mechanical keyboard', 79.99, 150, 'Electronics'),
    ('Monitor', '27-inch 4K monitor', 399.99, 75, 'Electronics'),
    ('Headphones', 'Noise-cancelling headphones', 199.99, 100, 'Electronics'),
    ('Desk Chair', 'Ergonomic office chair', 299.99, 30, 'Furniture'),
    ('Desk', 'Standing desk', 499.99, 20, 'Furniture'),
    ('Notebook', 'Spiral notebook pack', 9.99, 500, 'Office Supplies'),
    ('Pen Set', 'Professional pen set', 19.99, 300, 'Office Supplies'),
    ('USB Cable', 'USB-C cable', 14.99, 400, 'Electronics');

-- Create a view for order summaries
CREATE OR REPLACE VIEW order_summary AS
SELECT
    o.id AS order_id,
    u.username,
    u.email,
    o.total_amount,
    o.status,
    o.order_date,
    COUNT(oi.id) AS item_count
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.username, u.email, o.total_amount, o.status, o.order_date;

-- Create sample stored procedure
DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS get_user_orders(IN p_user_id INT)
BEGIN
    SELECT
        o.id,
        o.total_amount,
        o.status,
        o.order_date,
        COUNT(oi.id) AS item_count
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    WHERE o.user_id = p_user_id
    GROUP BY o.id, o.total_amount, o.status, o.order_date
    ORDER BY o.order_date DESC;
END$$

CREATE PROCEDURE IF NOT EXISTS add_product_stock(
    IN p_product_id INT,
    IN p_quantity INT
)
BEGIN
    UPDATE products
    SET stock_quantity = stock_quantity + p_quantity
    WHERE id = p_product_id;
END$$

DELIMITER ;

-- Create sample function
DELIMITER $$

CREATE FUNCTION IF NOT EXISTS calculate_order_total(p_order_id INT)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
BEGIN
    DECLARE v_total DECIMAL(10, 2);

    SELECT COALESCE(SUM(quantity * price), 0)
    INTO v_total
    FROM order_items
    WHERE order_id = p_order_id;

    RETURN v_total;
END$$

DELIMITER ;

-- Insert some sample orders
INSERT INTO orders (user_id, total_amount, status) VALUES
    (1, 1029.98, 'completed'),
    (2, 479.98, 'pending'),
    (1, 199.99, 'completed'),
    (3, 599.98, 'shipped');

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
    (1, 1, 1, 999.99),
    (1, 2, 1, 29.99),
    (2, 4, 1, 399.99),
    (2, 3, 1, 79.99),
    (3, 5, 1, 199.99),
    (4, 6, 2, 299.99);

-- Log initialization (MySQL doesn't support RAISE NOTICE, so we use SELECT)
SELECT 'AI-Shell MySQL test database initialized successfully' AS Status;
SELECT 'Database: testdb' AS Info;
SELECT 'Tables: users, products, orders, order_items' AS Info;
SELECT 'Sample data loaded' AS Info;
