-- Sample test data for database testing
-- This file contains sample SQL statements for populating test databases
-- Syntax is compatible with PostgreSQL, MySQL, and Oracle (with minor variations)

-- Sample users table data
-- INSERT INTO users (id, username, email, created_at) VALUES
--   (1, 'alice', 'alice@example.com', CURRENT_TIMESTAMP),
--   (2, 'bob', 'bob@example.com', CURRENT_TIMESTAMP),
--   (3, 'charlie', 'charlie@example.com', CURRENT_TIMESTAMP);

-- Sample products table data
-- INSERT INTO products (id, name, price, category, stock) VALUES
--   (1, 'Laptop', 999.99, 'Electronics', 50),
--   (2, 'Mouse', 19.99, 'Electronics', 200),
--   (3, 'Keyboard', 49.99, 'Electronics', 150),
--   (4, 'Monitor', 299.99, 'Electronics', 75),
--   (5, 'Desk Chair', 199.99, 'Furniture', 30);

-- Sample orders table data
-- INSERT INTO orders (id, user_id, total_amount, status, order_date) VALUES
--   (1, 1, 1049.98, 'completed', CURRENT_TIMESTAMP - INTERVAL '5 days'),
--   (2, 2, 19.99, 'pending', CURRENT_TIMESTAMP - INTERVAL '2 days'),
--   (3, 1, 349.98, 'shipped', CURRENT_TIMESTAMP - INTERVAL '1 day'),
--   (4, 3, 199.99, 'completed', CURRENT_TIMESTAMP);

-- Sample for testing different data types
-- INSERT INTO data_types_test (
--   int_col, varchar_col, text_col, decimal_col,
--   date_col, timestamp_col, boolean_col
-- ) VALUES (
--   42, 'test string', 'long text content', 123.45,
--   CURRENT_DATE, CURRENT_TIMESTAMP, true
-- );

-- Sample for testing NULL values
-- INSERT INTO null_test (id, nullable_col, not_null_col) VALUES
--   (1, NULL, 'value1'),
--   (2, 'value2', 'value2'),
--   (3, NULL, 'value3');

-- Sample large dataset for performance testing
-- DO $$
-- BEGIN
--   FOR i IN 1..1000 LOOP
--     INSERT INTO large_table (id, value) VALUES (i, 'Value_' || i);
--   END LOOP;
-- END $$;
