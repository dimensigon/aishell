-- AI-Shell Oracle Database 23c Initialization Script
-- Creates test schema and sample data for testing

-- Connect to the pluggable database
ALTER SESSION SET CONTAINER = FREEPDB1;

-- Create test user
CREATE USER testuser IDENTIFIED BY MyOraclePass123
DEFAULT TABLESPACE USERS
TEMPORARY TABLESPACE TEMP
QUOTA UNLIMITED ON USERS;

-- Grant privileges
GRANT CONNECT, RESOURCE, CREATE VIEW TO testuser;
GRANT CREATE SESSION TO testuser;
GRANT CREATE TABLE TO testuser;
GRANT CREATE SEQUENCE TO testuser;
GRANT CREATE PROCEDURE TO testuser;
GRANT CREATE TRIGGER TO testuser;

-- Connect as testuser for table creation
-- Note: In practice, this would be done in a separate session
-- For init script, we'll create objects in SYSTEM schema and grant access

-- Create sample users table
CREATE TABLE SYSTEM.users (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR2(50) UNIQUE NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    full_name VARCHAR2(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active NUMBER(1) DEFAULT 1
);

-- Create sample products table
CREATE TABLE SYSTEM.products (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    description CLOB,
    price NUMBER(10, 2) NOT NULL,
    stock_quantity NUMBER DEFAULT 0,
    category VARCHAR2(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sample orders table
CREATE TABLE SYSTEM.orders (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id NUMBER NOT NULL,
    total_amount NUMBER(10, 2) NOT NULL,
    status VARCHAR2(20) DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES SYSTEM.users(id) ON DELETE CASCADE
);

-- Create sample order_items table
CREATE TABLE SYSTEM.order_items (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id NUMBER NOT NULL,
    product_id NUMBER NOT NULL,
    quantity NUMBER NOT NULL,
    price NUMBER(10, 2) NOT NULL,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES SYSTEM.orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES SYSTEM.products(id) ON DELETE CASCADE
);

-- Insert sample users
INSERT INTO SYSTEM.users (username, email, full_name) VALUES
    ('john_doe', 'john@example.com', 'John Doe');
INSERT INTO SYSTEM.users (username, email, full_name) VALUES
    ('jane_smith', 'jane@example.com', 'Jane Smith');
INSERT INTO SYSTEM.users (username, email, full_name) VALUES
    ('bob_wilson', 'bob@example.com', 'Bob Wilson');
INSERT INTO SYSTEM.users (username, email, full_name) VALUES
    ('alice_jones', 'alice@example.com', 'Alice Jones');
INSERT INTO SYSTEM.users (username, email, full_name) VALUES
    ('charlie_brown', 'charlie@example.com', 'Charlie Brown');
COMMIT;

-- Insert sample products
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Laptop', 'High-performance laptop', 999.99, 50, 'Electronics');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Mouse', 'Wireless mouse', 29.99, 200, 'Electronics');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Keyboard', 'Mechanical keyboard', 79.99, 150, 'Electronics');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Monitor', '27-inch 4K monitor', 399.99, 75, 'Electronics');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Headphones', 'Noise-cancelling headphones', 199.99, 100, 'Electronics');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Desk Chair', 'Ergonomic office chair', 299.99, 30, 'Furniture');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Desk', 'Standing desk', 499.99, 20, 'Furniture');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Notebook', 'Spiral notebook pack', 9.99, 500, 'Office Supplies');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('Pen Set', 'Professional pen set', 19.99, 300, 'Office Supplies');
INSERT INTO SYSTEM.products (name, description, price, stock_quantity, category) VALUES
    ('USB Cable', 'USB-C cable', 14.99, 400, 'Electronics');
COMMIT;

-- Create indexes
CREATE INDEX idx_users_email ON SYSTEM.users(email);
CREATE INDEX idx_users_username ON SYSTEM.users(username);
CREATE INDEX idx_products_category ON SYSTEM.products(category);
CREATE INDEX idx_products_name ON SYSTEM.products(name);
CREATE INDEX idx_orders_user_id ON SYSTEM.orders(user_id);
CREATE INDEX idx_orders_status ON SYSTEM.orders(status);
CREATE INDEX idx_order_items_order_id ON SYSTEM.order_items(order_id);

-- Create a view for order summaries
CREATE OR REPLACE VIEW SYSTEM.order_summary AS
SELECT
    o.id AS order_id,
    u.username,
    u.email,
    o.total_amount,
    o.status,
    o.order_date,
    COUNT(oi.id) AS item_count
FROM SYSTEM.orders o
JOIN SYSTEM.users u ON o.user_id = u.id
LEFT JOIN SYSTEM.order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.username, u.email, o.total_amount, o.status, o.order_date;

-- Create a trigger for updating timestamps
CREATE OR REPLACE TRIGGER SYSTEM.trg_users_updated_at
BEFORE UPDATE ON SYSTEM.users
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- Create a stored procedure
CREATE OR REPLACE PROCEDURE SYSTEM.get_user_orders(
    p_user_id IN NUMBER,
    p_cursor OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_cursor FOR
    SELECT
        o.id,
        o.total_amount,
        o.status,
        o.order_date,
        COUNT(oi.id) AS item_count
    FROM SYSTEM.orders o
    LEFT JOIN SYSTEM.order_items oi ON o.id = oi.order_id
    WHERE o.user_id = p_user_id
    GROUP BY o.id, o.total_amount, o.status, o.order_date
    ORDER BY o.order_date DESC;
END;
/

-- Create a function
CREATE OR REPLACE FUNCTION SYSTEM.calculate_order_total(
    p_order_id IN NUMBER
) RETURN NUMBER AS
    v_total NUMBER;
BEGIN
    SELECT NVL(SUM(quantity * price), 0)
    INTO v_total
    FROM SYSTEM.order_items
    WHERE order_id = p_order_id;

    RETURN v_total;
END;
/

-- Insert sample orders
INSERT INTO SYSTEM.orders (user_id, total_amount, status) VALUES (1, 1029.98, 'completed');
INSERT INTO SYSTEM.orders (user_id, total_amount, status) VALUES (2, 479.98, 'pending');
INSERT INTO SYSTEM.orders (user_id, total_amount, status) VALUES (1, 199.99, 'completed');
INSERT INTO SYSTEM.orders (user_id, total_amount, status) VALUES (3, 599.98, 'shipped');
COMMIT;

-- Insert sample order items
INSERT INTO SYSTEM.order_items (order_id, product_id, quantity, price) VALUES (1, 1, 1, 999.99);
INSERT INTO SYSTEM.order_items (order_id, product_id, quantity, price) VALUES (1, 2, 1, 29.99);
INSERT INTO SYSTEM.order_items (order_id, product_id, quantity, price) VALUES (2, 4, 1, 399.99);
INSERT INTO SYSTEM.order_items (order_id, product_id, quantity, price) VALUES (2, 3, 1, 79.99);
INSERT INTO SYSTEM.order_items (order_id, product_id, quantity, price) VALUES (3, 5, 1, 199.99);
INSERT INTO SYSTEM.order_items (order_id, product_id, quantity, price) VALUES (4, 6, 2, 299.99);
COMMIT;

-- Grant access to testuser
GRANT SELECT, INSERT, UPDATE, DELETE ON SYSTEM.users TO testuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON SYSTEM.products TO testuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON SYSTEM.orders TO testuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON SYSTEM.order_items TO testuser;
GRANT SELECT ON SYSTEM.order_summary TO testuser;
GRANT EXECUTE ON SYSTEM.get_user_orders TO testuser;
GRANT EXECUTE ON SYSTEM.calculate_order_total TO testuser;

-- Log initialization
BEGIN
    DBMS_OUTPUT.PUT_LINE('AI-Shell Oracle Database 23c test database initialized successfully');
    DBMS_OUTPUT.PUT_LINE('Container: FREEPDB1');
    DBMS_OUTPUT.PUT_LINE('Schema: SYSTEM');
    DBMS_OUTPUT.PUT_LINE('User: testuser');
    DBMS_OUTPUT.PUT_LINE('Tables: users, products, orders, order_items');
    DBMS_OUTPUT.PUT_LINE('Sample data loaded');
END;
/

EXIT;
