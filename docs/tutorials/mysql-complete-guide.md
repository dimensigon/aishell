# MySQL Complete Guide

A comprehensive tutorial for MySQL relational database management, from basics to advanced administration.

**Estimated Time:** 6-8 hours
**Prerequisites:** Basic SQL knowledge, Docker installed

---

## Table of Contents

1. [Setup and Installation](#1-setup-and-installation)
2. [Database and Table Management](#2-database-and-table-management)
3. [Data Types and Constraints](#3-data-types-and-constraints)
4. [CRUD Operations](#4-crud-operations)
5. [Joins and Relationships](#5-joins-and-relationships)
6. [Indexes and Optimization](#6-indexes-and-optimization)
7. [Stored Procedures and Functions](#7-stored-procedures-and-functions)
8. [Triggers and Events](#8-triggers-and-events)
9. [Transactions and Locking](#9-transactions-and-locking)
10. [Replication Basics](#10-replication-basics)
11. [Backup and Restore](#11-backup-and-restore)
12. [Performance Tuning](#12-performance-tuning)
13. [Real-World Scenarios](#13-real-world-scenarios)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Setup and Installation

**Time:** 20 minutes

### 1.1 Docker Setup

```bash
# Pull MySQL image
docker pull mysql:8

# Run MySQL container
docker run -d \
  --name my-mysql \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -e MYSQL_DATABASE=mydb \
  -e MYSQL_USER=myuser \
  -e MYSQL_PASSWORD=mypassword \
  -p 3306:3306 \
  -v mysql-data:/var/lib/mysql \
  mysql:8

# Verify container is running
docker ps | grep mysql
```

### 1.2 Connect to MySQL

```bash
# Using docker exec
docker exec -it my-mysql mysql -u root -p

# Using AIShell
aishell mysql connect --host localhost --port 3306 --user root --password root_password

# Test connection
SELECT VERSION();
```

### 1.3 Initial Configuration

```sql
-- Check MySQL version
SELECT VERSION();

-- Show current database
SELECT DATABASE();

-- List all databases
SHOW DATABASES;

-- Show server variables
SHOW VARIABLES;

-- Show server status
SHOW STATUS;

-- Set SQL mode
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Set character set
SET NAMES utf8mb4;
```

**Expected Output:**
```
MySQL version 8.x.x
```

**Exercise 1.1:** Configure MySQL for development
- Create a new database
- Create a user with specific privileges
- Test connection with new user

<details>
<summary>Solution</summary>

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS app_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'app_user'@'%' IDENTIFIED BY 'app_password';

-- Grant privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON app_db.* TO 'app_user'@'%';
GRANT CREATE, ALTER, DROP, INDEX ON app_db.* TO 'app_user'@'%';

-- Flush privileges
FLUSH PRIVILEGES;

-- Verify user
SELECT User, Host FROM mysql.user WHERE User = 'app_user';

-- Show grants
SHOW GRANTS FOR 'app_user'@'%';

-- Test connection
-- Exit and reconnect
exit;

-- docker exec -it my-mysql mysql -u app_user -p app_db
-- Enter password: app_password

-- Verify
SELECT CURRENT_USER(), DATABASE();
```
</details>

---

## 2. Database and Table Management

**Time:** 45 minutes

### 2.1 Database Operations

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS ecommerce
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Use database
USE ecommerce;

-- Show database info
SHOW CREATE DATABASE ecommerce;

-- Alter database
ALTER DATABASE ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Drop database
DROP DATABASE IF EXISTS test_db;

-- Show all databases with size
SELECT
  table_schema AS 'Database',
  ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
GROUP BY table_schema;
```

### 2.2 Table Creation

```sql
-- Create customers table
CREATE TABLE customers (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  phone VARCHAR(20),
  date_of_birth DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  INDEX idx_email (email),
  INDEX idx_name (last_name, first_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create orders table with foreign key
CREATE TABLE orders (
  order_id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
  status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
  shipping_address TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
  INDEX idx_customer (customer_id),
  INDEX idx_status (status),
  INDEX idx_order_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create order items table
CREATE TABLE order_items (
  order_item_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price DECIMAL(10, 2) NOT NULL,
  subtotal DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  INDEX idx_order (order_id),
  INDEX idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 2.3 Table Alterations

```sql
-- Add column
ALTER TABLE customers
ADD COLUMN loyalty_points INT DEFAULT 0;

-- Modify column
ALTER TABLE customers
MODIFY COLUMN phone VARCHAR(30);

-- Change column name and type
ALTER TABLE customers
CHANGE COLUMN phone phone_number VARCHAR(30);

-- Drop column
ALTER TABLE customers
DROP COLUMN phone_number;

-- Add index
ALTER TABLE customers
ADD INDEX idx_loyalty (loyalty_points);

-- Drop index
ALTER TABLE customers
DROP INDEX idx_loyalty;

-- Add foreign key
ALTER TABLE orders
ADD CONSTRAINT fk_customer
FOREIGN KEY (customer_id) REFERENCES customers(customer_id);

-- Drop foreign key
ALTER TABLE orders
DROP FOREIGN KEY fk_customer;

-- Rename table
RENAME TABLE old_name TO new_name;
```

### 2.4 Viewing Table Structure

```sql
-- Show table structure
DESCRIBE customers;
DESC customers;

-- Show create statement
SHOW CREATE TABLE customers;

-- Show table status
SHOW TABLE STATUS LIKE 'customers';

-- Show indexes
SHOW INDEXES FROM customers;

-- Show columns
SHOW COLUMNS FROM customers;
```

**Exercise 2.1:** Create a complete database schema
- Blog database with users, posts, comments, tags
- Appropriate data types and constraints
- Foreign key relationships
- Indexes for common queries

<details>
<summary>Solution</summary>

```sql
-- Create database
CREATE DATABASE blog_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE blog_db;

-- Users table
CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  bio TEXT,
  avatar_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_login_at TIMESTAMP NULL,
  is_active BOOLEAN DEFAULT TRUE,
  INDEX idx_username (username),
  INDEX idx_email (email),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Posts table
CREATE TABLE posts (
  post_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) UNIQUE NOT NULL,
  content TEXT NOT NULL,
  excerpt VARCHAR(500),
  featured_image VARCHAR(500),
  status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
  published_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  view_count INT DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  INDEX idx_user (user_id),
  INDEX idx_slug (slug),
  INDEX idx_status (status),
  INDEX idx_published (published_at),
  FULLTEXT idx_search (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Comments table
CREATE TABLE comments (
  comment_id INT AUTO_INCREMENT PRIMARY KEY,
  post_id INT NOT NULL,
  user_id INT NOT NULL,
  parent_id INT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_approved BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (parent_id) REFERENCES comments(comment_id) ON DELETE CASCADE,
  INDEX idx_post (post_id),
  INDEX idx_user (user_id),
  INDEX idx_parent (parent_id),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tags table
CREATE TABLE tags (
  tag_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,
  slug VARCHAR(50) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_slug (slug),
  INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Post-Tag relationship (many-to-many)
CREATE TABLE post_tags (
  post_id INT NOT NULL,
  tag_id INT NOT NULL,
  PRIMARY KEY (post_id, tag_id),
  FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE,
  INDEX idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Likes table
CREATE TABLE likes (
  like_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  post_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_like (user_id, post_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
  INDEX idx_post (post_id),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verify schema
SHOW TABLES;

-- Show table structures
SHOW CREATE TABLE users\G
SHOW CREATE TABLE posts\G
SHOW CREATE TABLE comments\G
```
</details>

---

## 3. Data Types and Constraints

**Time:** 30 minutes

### 3.1 Common Data Types

```sql
-- Numeric types
CREATE TABLE numeric_examples (
  tiny_int TINYINT,           -- -128 to 127
  small_int SMALLINT,         -- -32768 to 32767
  medium_int MEDIUMINT,       -- -8388608 to 8388607
  int_col INT,                -- -2147483648 to 2147483647
  big_int BIGINT,             -- Very large range
  decimal_col DECIMAL(10, 2), -- Fixed precision
  float_col FLOAT,            -- Approximate numeric
  double_col DOUBLE           -- Double precision
);

-- String types
CREATE TABLE string_examples (
  char_col CHAR(10),          -- Fixed length
  varchar_col VARCHAR(255),   -- Variable length
  text_col TEXT,              -- Long text
  medium_text MEDIUMTEXT,     -- Longer text
  long_text LONGTEXT,         -- Maximum text
  enum_col ENUM('a', 'b', 'c'), -- Enumeration
  set_col SET('x', 'y', 'z')  -- Set of values
);

-- Date and time types
CREATE TABLE datetime_examples (
  date_col DATE,              -- YYYY-MM-DD
  time_col TIME,              -- HH:MM:SS
  datetime_col DATETIME,      -- YYYY-MM-DD HH:MM:SS
  timestamp_col TIMESTAMP,    -- Unix timestamp
  year_col YEAR               -- YYYY
);

-- Binary types
CREATE TABLE binary_examples (
  binary_col BINARY(16),      -- Fixed binary
  varbinary_col VARBINARY(255), -- Variable binary
  blob_col BLOB,              -- Binary large object
  medium_blob MEDIUMBLOB,
  long_blob LONGBLOB
);

-- JSON type (MySQL 5.7+)
CREATE TABLE json_examples (
  data JSON
);
```

### 3.2 Constraints

```sql
-- Primary key
CREATE TABLE example1 (
  id INT AUTO_INCREMENT PRIMARY KEY
);

-- Unique constraint
CREATE TABLE example2 (
  email VARCHAR(255) UNIQUE NOT NULL
);

-- Foreign key
CREATE TABLE example3 (
  user_id INT,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Check constraint (MySQL 8.0.16+)
CREATE TABLE example4 (
  age INT CHECK (age >= 18),
  salary DECIMAL(10, 2) CHECK (salary > 0)
);

-- Default values
CREATE TABLE example5 (
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Not null
CREATE TABLE example6 (
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL
);

-- Generated columns
CREATE TABLE example7 (
  price DECIMAL(10, 2),
  quantity INT,
  total DECIMAL(10, 2) GENERATED ALWAYS AS (price * quantity) STORED
);
```

**Exercise 3.1:** Design a products table with constraints
- Appropriate data types
- Price must be positive
- Stock can't be negative
- SKU must be unique
- Category from predefined list

<details>
<summary>Solution</summary>

```sql
-- Create products table with comprehensive constraints
CREATE TABLE products (
  product_id INT AUTO_INCREMENT PRIMARY KEY,
  sku VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category ENUM('electronics', 'clothing', 'books', 'home', 'sports', 'toys', 'other') NOT NULL,
  price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
  cost DECIMAL(10, 2) CHECK (cost >= 0),
  stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
  reorder_level INT DEFAULT 10 CHECK (reorder_level >= 0),
  weight DECIMAL(8, 2) CHECK (weight >= 0),
  dimensions JSON,
  image_url VARCHAR(500),
  is_active BOOLEAN DEFAULT TRUE,
  is_featured BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- Generated columns
  profit_margin DECIMAL(10, 2) GENERATED ALWAYS AS (price - cost) STORED,
  needs_reorder BOOLEAN GENERATED ALWAYS AS (stock_quantity <= reorder_level) STORED,

  -- Indexes
  INDEX idx_sku (sku),
  INDEX idx_category (category),
  INDEX idx_active (is_active),
  INDEX idx_featured (is_featured),
  INDEX idx_stock (stock_quantity),
  FULLTEXT idx_search (name, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert test data
INSERT INTO products (sku, name, description, category, price, cost, stock_quantity) VALUES
  ('ELEC-001', 'Laptop Pro 15', 'High-performance laptop', 'electronics', 1299.99, 899.99, 50),
  ('ELEC-002', 'Wireless Mouse', 'Ergonomic wireless mouse', 'electronics', 29.99, 15.99, 200),
  ('BOOK-001', 'MySQL Mastery', 'Complete MySQL guide', 'books', 49.99, 20.00, 100);

-- Verify constraints
-- This should fail (negative price)
-- INSERT INTO products (sku, name, category, price, stock_quantity)
-- VALUES ('TEST-001', 'Test', 'electronics', -10.00, 50);

-- This should fail (negative stock)
-- INSERT INTO products (sku, name, category, price, stock_quantity)
-- VALUES ('TEST-002', 'Test', 'electronics', 10.00, -5);

-- This should fail (duplicate SKU)
-- INSERT INTO products (sku, name, category, price, stock_quantity)
-- VALUES ('ELEC-001', 'Test', 'electronics', 10.00, 50);

-- Query with generated columns
SELECT
  sku,
  name,
  price,
  cost,
  profit_margin,
  stock_quantity,
  needs_reorder
FROM products;
```
</details>

---

## 4. CRUD Operations

**Time:** 45 minutes

### 4.1 Insert Operations

```sql
-- Insert single row
INSERT INTO customers (email, first_name, last_name, phone)
VALUES ('john@example.com', 'John', 'Doe', '+1234567890');

-- Insert multiple rows
INSERT INTO customers (email, first_name, last_name) VALUES
  ('alice@example.com', 'Alice', 'Johnson'),
  ('bob@example.com', 'Bob', 'Smith'),
  ('carol@example.com', 'Carol', 'Williams');

-- Insert with SELECT
INSERT INTO archived_customers
SELECT * FROM customers WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- Insert or update (ON DUPLICATE KEY UPDATE)
INSERT INTO customers (email, first_name, last_name)
VALUES ('john@example.com', 'John', 'Doe')
ON DUPLICATE KEY UPDATE
  first_name = VALUES(first_name),
  last_name = VALUES(last_name),
  updated_at = CURRENT_TIMESTAMP;

-- Get last inserted ID
INSERT INTO customers (email, first_name, last_name)
VALUES ('test@example.com', 'Test', 'User');
SELECT LAST_INSERT_ID();
```

### 4.2 Select Operations

```sql
-- Basic select
SELECT * FROM customers;

-- Select specific columns
SELECT customer_id, email, first_name, last_name FROM customers;

-- With WHERE clause
SELECT * FROM customers
WHERE is_active = TRUE
  AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Pattern matching
SELECT * FROM customers
WHERE email LIKE '%@gmail.com'
   OR first_name LIKE 'John%';

-- IN clause
SELECT * FROM customers
WHERE customer_id IN (1, 2, 3, 5, 8);

-- BETWEEN
SELECT * FROM orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'
  AND total_amount BETWEEN 100 AND 1000;

-- IS NULL / IS NOT NULL
SELECT * FROM customers
WHERE phone IS NOT NULL;

-- ORDER BY
SELECT * FROM customers
ORDER BY created_at DESC
LIMIT 10;

-- DISTINCT
SELECT DISTINCT status FROM orders;

-- LIMIT and OFFSET (pagination)
SELECT * FROM customers
ORDER BY customer_id
LIMIT 10 OFFSET 20;
```

### 4.3 Update Operations

```sql
-- Update single row
UPDATE customers
SET phone = '+9876543210', updated_at = CURRENT_TIMESTAMP
WHERE email = 'john@example.com';

-- Update multiple rows
UPDATE products
SET price = price * 0.9
WHERE category = 'electronics';

-- Update with calculation
UPDATE customers
SET loyalty_points = loyalty_points + 100
WHERE customer_id IN (SELECT customer_id FROM orders WHERE total_amount > 1000);

-- Update with JOIN
UPDATE orders o
JOIN customers c ON o.customer_id = c.customer_id
SET o.status = 'priority'
WHERE c.loyalty_points > 5000;
```

### 4.4 Delete Operations

```sql
-- Delete single row
DELETE FROM customers
WHERE email = 'delete@example.com';

-- Delete with conditions
DELETE FROM customers
WHERE is_active = FALSE
  AND created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- Delete with JOIN
DELETE o FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE c.is_active = FALSE;

-- Truncate table (faster, resets AUTO_INCREMENT)
TRUNCATE TABLE test_table;
```

**Exercise 4.1:** Complex CRUD operations
- Insert 100 sample customers
- Update customers based on order history
- Find top customers by spending
- Clean up old inactive records

<details>
<summary>Solution</summary>

```sql
-- Insert 100 sample customers
DELIMITER $$

CREATE PROCEDURE insert_sample_customers()
BEGIN
  DECLARE i INT DEFAULT 1;

  WHILE i <= 100 DO
    INSERT INTO customers (email, first_name, last_name, phone, date_of_birth)
    VALUES (
      CONCAT('customer', i, '@example.com'),
      CONCAT('First', i),
      CONCAT('Last', i),
      CONCAT('+1-555-', LPAD(i, 4, '0')),
      DATE_SUB(CURDATE(), INTERVAL (20 + FLOOR(RAND() * 40)) YEAR)
    );
    SET i = i + 1;
  END WHILE;
END$$

DELIMITER ;

CALL insert_sample_customers();

-- Insert sample orders
INSERT INTO orders (customer_id, total_amount, status)
SELECT
  customer_id,
  ROUND(RAND() * 500 + 50, 2) AS total_amount,
  ELT(FLOOR(RAND() * 5) + 1, 'pending', 'processing', 'shipped', 'delivered', 'cancelled') AS status
FROM customers
CROSS JOIN (SELECT 1 UNION SELECT 2 UNION SELECT 3) AS numbers
WHERE RAND() < 0.7;

-- Update loyalty points based on order history
UPDATE customers c
SET loyalty_points = (
  SELECT COALESCE(SUM(total_amount), 0) * 0.1
  FROM orders o
  WHERE o.customer_id = c.customer_id
    AND o.status = 'delivered'
);

-- Find top 10 customers by spending
SELECT
  c.customer_id,
  c.email,
  CONCAT(c.first_name, ' ', c.last_name) AS full_name,
  COUNT(o.order_id) AS order_count,
  SUM(o.total_amount) AS total_spent,
  AVG(o.total_amount) AS avg_order_value,
  c.loyalty_points
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'delivered'
GROUP BY c.customer_id
HAVING order_count > 0
ORDER BY total_spent DESC
LIMIT 10;

-- Find customers with no orders
SELECT
  c.customer_id,
  c.email,
  c.first_name,
  c.last_name,
  c.created_at
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL
  AND c.created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);

-- Clean up old inactive records
-- Mark inactive
UPDATE customers
SET is_active = FALSE
WHERE customer_id IN (
  SELECT customer_id FROM (
    SELECT c.customer_id
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
      AND o.order_date > DATE_SUB(NOW(), INTERVAL 1 YEAR)
    WHERE o.order_id IS NULL
      AND c.created_at < DATE_SUB(NOW(), INTERVAL 2 YEAR)
  ) AS inactive
);

-- Delete very old inactive customers (archive first)
CREATE TABLE IF NOT EXISTS archived_customers LIKE customers;

INSERT INTO archived_customers
SELECT * FROM customers
WHERE is_active = FALSE
  AND created_at < DATE_SUB(NOW(), INTERVAL 3 YEAR);

DELETE FROM customers
WHERE is_active = FALSE
  AND created_at < DATE_SUB(NOW(), INTERVAL 3 YEAR);

-- Show statistics
SELECT
  'Total Customers' AS metric,
  COUNT(*) AS value
FROM customers
UNION ALL
SELECT
  'Active Customers',
  COUNT(*)
FROM customers
WHERE is_active = TRUE
UNION ALL
SELECT
  'Total Orders',
  COUNT(*)
FROM orders
UNION ALL
SELECT
  'Delivered Orders',
  COUNT(*)
FROM orders
WHERE status = 'delivered';
```
</details>

---

## 5. Joins and Relationships

**Time:** 60 minutes

### 5.1 Types of Joins

```sql
-- INNER JOIN
SELECT
  c.customer_id,
  c.email,
  o.order_id,
  o.total_amount
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id;

-- LEFT JOIN (LEFT OUTER JOIN)
SELECT
  c.customer_id,
  c.email,
  COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id;

-- RIGHT JOIN (RIGHT OUTER JOIN)
SELECT
  o.order_id,
  c.email
FROM orders o
RIGHT JOIN customers c ON o.customer_id = c.customer_id;

-- CROSS JOIN (Cartesian product)
SELECT
  c.customer_id,
  p.product_id
FROM customers c
CROSS JOIN products p
LIMIT 10;

-- SELF JOIN
SELECT
  e1.employee_id,
  e1.name AS employee_name,
  e2.name AS manager_name
FROM employees e1
LEFT JOIN employees e2 ON e1.manager_id = e2.employee_id;
```

### 5.2 Multiple Joins

```sql
-- Three-way join
SELECT
  c.email,
  o.order_id,
  o.total_amount,
  oi.product_id,
  oi.quantity,
  oi.unit_price
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'delivered'
ORDER BY c.email, o.order_id;

-- Complex multi-table query
SELECT
  c.customer_id,
  CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
  COUNT(DISTINCT o.order_id) AS total_orders,
  SUM(o.total_amount) AS total_spent,
  AVG(o.total_amount) AS avg_order_value,
  COUNT(DISTINCT oi.product_id) AS unique_products_purchased
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'delivered'
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY c.customer_id
HAVING total_orders > 0
ORDER BY total_spent DESC;
```

### 5.3 Subqueries

```sql
-- Subquery in WHERE
SELECT *
FROM customers
WHERE customer_id IN (
  SELECT customer_id
  FROM orders
  WHERE total_amount > 1000
);

-- Subquery in SELECT
SELECT
  c.customer_id,
  c.email,
  (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.customer_id) AS order_count,
  (SELECT SUM(total_amount) FROM orders o WHERE o.customer_id = c.customer_id) AS total_spent
FROM customers c;

-- Correlated subquery
SELECT *
FROM orders o1
WHERE total_amount > (
  SELECT AVG(total_amount)
  FROM orders o2
  WHERE o2.customer_id = o1.customer_id
);

-- EXISTS
SELECT *
FROM customers c
WHERE EXISTS (
  SELECT 1
  FROM orders o
  WHERE o.customer_id = c.customer_id
    AND o.total_amount > 1000
);

-- NOT EXISTS
SELECT *
FROM customers c
WHERE NOT EXISTS (
  SELECT 1
  FROM orders o
  WHERE o.customer_id = c.customer_id
);
```

### 5.4 Common Table Expressions (CTEs)

```sql
-- Simple CTE
WITH high_value_customers AS (
  SELECT customer_id, SUM(total_amount) AS total_spent
  FROM orders
  WHERE status = 'delivered'
  GROUP BY customer_id
  HAVING total_spent > 5000
)
SELECT
  c.email,
  c.first_name,
  c.last_name,
  hvc.total_spent
FROM high_value_customers hvc
JOIN customers c ON hvc.customer_id = c.customer_id
ORDER BY hvc.total_spent DESC;

-- Multiple CTEs
WITH
  monthly_revenue AS (
    SELECT
      DATE_FORMAT(order_date, '%Y-%m') AS month,
      SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'delivered'
    GROUP BY month
  ),
  monthly_customers AS (
    SELECT
      DATE_FORMAT(created_at, '%Y-%m') AS month,
      COUNT(*) AS new_customers
    FROM customers
    GROUP BY month
  )
SELECT
  mr.month,
  mr.revenue,
  mc.new_customers,
  mr.revenue / NULLIF(mc.new_customers, 0) AS revenue_per_new_customer
FROM monthly_revenue mr
LEFT JOIN monthly_customers mc ON mr.month = mc.month
ORDER BY mr.month DESC;

-- Recursive CTE (organizational hierarchy)
WITH RECURSIVE employee_hierarchy AS (
  -- Base case: top-level managers
  SELECT
    employee_id,
    name,
    manager_id,
    1 AS level,
    CAST(name AS CHAR(255)) AS path
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive case
  SELECT
    e.employee_id,
    e.name,
    e.manager_id,
    eh.level + 1,
    CONCAT(eh.path, ' > ', e.name)
  FROM employees e
  INNER JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
  WHERE eh.level < 10
)
SELECT * FROM employee_hierarchy
ORDER BY level, name;
```

**Exercise 5.1:** Complex join queries
- Customer lifetime value analysis
- Product recommendations based on purchase history
- Find customers who bought products in multiple categories

<details>
<summary>Solution</summary>

```sql
-- Customer Lifetime Value Analysis
WITH customer_orders AS (
  SELECT
    c.customer_id,
    c.email,
    CONCAT(c.first_name, ' ', c.last_name) AS full_name,
    c.created_at AS registration_date,
    COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.status = 'delivered' THEN o.total_amount ELSE 0 END) AS lifetime_value,
    AVG(CASE WHEN o.status = 'delivered' THEN o.total_amount END) AS avg_order_value,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date,
    DATEDIFF(MAX(o.order_date), MIN(o.order_date)) AS customer_lifespan_days
  FROM customers c
  LEFT JOIN orders o ON c.customer_id = o.customer_id
  GROUP BY c.customer_id
),
customer_segments AS (
  SELECT
    *,
    CASE
      WHEN lifetime_value >= 5000 AND DATEDIFF(NOW(), last_order_date) <= 30 THEN 'VIP Active'
      WHEN lifetime_value >= 2000 THEN 'Premium'
      WHEN DATEDIFF(NOW(), last_order_date) <= 90 THEN 'Active'
      WHEN DATEDIFF(NOW(), last_order_date) > 90 THEN 'At Risk'
      ELSE 'New'
    END AS segment
  FROM customer_orders
)
SELECT
  segment,
  COUNT(*) AS customer_count,
  AVG(lifetime_value) AS avg_ltv,
  AVG(total_orders) AS avg_orders,
  AVG(avg_order_value) AS avg_order_value
FROM customer_segments
GROUP BY segment
ORDER BY avg_ltv DESC;

-- Product Recommendations (Collaborative Filtering)
-- "Customers who bought X also bought Y"
WITH product_pairs AS (
  SELECT DISTINCT
    oi1.product_id AS product_a,
    oi2.product_id AS product_b,
    COUNT(DISTINCT oi1.order_id) AS co_purchase_count
  FROM order_items oi1
  JOIN order_items oi2 ON oi1.order_id = oi2.order_id
    AND oi1.product_id < oi2.product_id
  GROUP BY oi1.product_id, oi2.product_id
  HAVING co_purchase_count >= 3
)
SELECT
  pp.product_a,
  p1.name AS product_a_name,
  pp.product_b,
  p2.name AS product_b_name,
  pp.co_purchase_count,
  ROUND(pp.co_purchase_count * 100.0 / (
    SELECT COUNT(DISTINCT order_id)
    FROM order_items
    WHERE product_id = pp.product_a
  ), 2) AS recommendation_strength
FROM product_pairs pp
JOIN products p1 ON pp.product_a = p1.product_id
JOIN products p2 ON pp.product_b = p2.product_id
ORDER BY pp.co_purchase_count DESC
LIMIT 20;

-- Multi-Category Buyers
WITH customer_categories AS (
  SELECT DISTINCT
    c.customer_id,
    c.email,
    CONCAT(c.first_name, ' ', c.last_name) AS full_name,
    p.category
  FROM customers c
  JOIN orders o ON c.customer_id = o.customer_id
  JOIN order_items oi ON o.order_id = oi.order_id
  JOIN products p ON oi.product_id = p.product_id
  WHERE o.status = 'delivered'
),
category_counts AS (
  SELECT
    customer_id,
    email,
    full_name,
    COUNT(DISTINCT category) AS category_count,
    GROUP_CONCAT(DISTINCT category ORDER BY category SEPARATOR ', ') AS categories
  FROM customer_categories
  GROUP BY customer_id, email, full_name
  HAVING category_count >= 3
),
customer_value AS (
  SELECT
    customer_id,
    SUM(total_amount) AS total_spent,
    COUNT(order_id) AS order_count
  FROM orders
  WHERE status = 'delivered'
  GROUP BY customer_id
)
SELECT
  cc.email,
  cc.full_name,
  cc.category_count,
  cc.categories,
  cv.total_spent,
  cv.order_count
FROM category_counts cc
JOIN customer_value cv ON cc.customer_id = cv.customer_id
ORDER BY cc.category_count DESC, cv.total_spent DESC;

-- Cohort Analysis
WITH customer_cohorts AS (
  SELECT
    c.customer_id,
    DATE_FORMAT(c.created_at, '%Y-%m') AS cohort_month,
    o.order_date,
    DATE_FORMAT(o.order_date, '%Y-%m') AS order_month,
    o.total_amount
  FROM customers c
  LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'delivered'
),
cohort_metrics AS (
  SELECT
    cohort_month,
    order_month,
    COUNT(DISTINCT customer_id) AS active_customers,
    SUM(total_amount) AS revenue,
    PERIOD_DIFF(
      CAST(REPLACE(order_month, '-', '') AS UNSIGNED),
      CAST(REPLACE(cohort_month, '-', '') AS UNSIGNED)
    ) AS months_since_registration
  FROM customer_cohorts
  WHERE order_month IS NOT NULL
  GROUP BY cohort_month, order_month
),
cohort_sizes AS (
  SELECT
    DATE_FORMAT(created_at, '%Y-%m') AS cohort_month,
    COUNT(*) AS cohort_size
  FROM customers
  GROUP BY cohort_month
)
SELECT
  cm.cohort_month,
  cm.months_since_registration,
  cm.active_customers,
  cs.cohort_size,
  ROUND(cm.active_customers * 100.0 / cs.cohort_size, 2) AS retention_rate,
  cm.revenue,
  ROUND(cm.revenue / cm.active_customers, 2) AS revenue_per_customer
FROM cohort_metrics cm
JOIN cohort_sizes cs ON cm.cohort_month = cs.cohort_month
ORDER BY cm.cohort_month DESC, cm.months_since_registration;
```
</details>

---

## 6. Indexes and Optimization

**Time:** 60 minutes

### 6.1 Index Types

```sql
-- Primary key (automatically indexed)
CREATE TABLE example1 (
  id INT AUTO_INCREMENT PRIMARY KEY
);

-- Unique index
CREATE UNIQUE INDEX idx_email ON customers(email);

-- Regular index
CREATE INDEX idx_last_name ON customers(last_name);

-- Composite index
CREATE INDEX idx_name ON customers(last_name, first_name);

-- Full-text index
CREATE FULLTEXT INDEX idx_description ON products(name, description);

-- Spatial index (for geometry types)
-- CREATE SPATIAL INDEX idx_location ON stores(location);

-- Prefix index (for long strings)
CREATE INDEX idx_long_text ON articles(content(100));
```

### 6.2 Index Management

```sql
-- Show indexes
SHOW INDEXES FROM customers;

-- Analyze table and update index statistics
ANALYZE TABLE customers;

-- Drop index
DROP INDEX idx_last_name ON customers;

-- Add index to existing table
ALTER TABLE customers
ADD INDEX idx_created (created_at);

-- Force index usage
SELECT * FROM customers
FORCE INDEX (idx_email)
WHERE email = 'john@example.com';

-- Check index cardinality
SELECT
  TABLE_NAME,
  INDEX_NAME,
  CARDINALITY,
  SEQ_IN_INDEX,
  COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'ecommerce'
  AND TABLE_NAME = 'customers';
```

### 6.3 Query Optimization with EXPLAIN

```sql
-- Basic EXPLAIN
EXPLAIN SELECT * FROM orders WHERE customer_id = 1;

-- EXPLAIN with multiple tables
EXPLAIN
SELECT c.email, o.order_id, o.total_amount
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE c.is_active = TRUE;

-- EXPLAIN ANALYZE (shows actual execution)
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE order_date >= DATE_SUB(NOW(), INTERVAL 7 DAY);

-- EXPLAIN FORMAT=JSON
EXPLAIN FORMAT=JSON
SELECT * FROM customers
WHERE email LIKE '%@gmail.com';
```

### 6.4 Query Optimization Techniques

```sql
-- Use covering indexes (index-only scan)
CREATE INDEX idx_email_name ON customers(email, first_name, last_name);

SELECT email, first_name, last_name
FROM customers
WHERE email = 'john@example.com';

-- Avoid functions on indexed columns
-- BAD: Index not used
SELECT * FROM customers WHERE YEAR(created_at) = 2024;

-- GOOD: Index can be used
SELECT * FROM customers
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';

-- Use EXISTS instead of IN for large result sets
-- GOOD for large subqueries
SELECT * FROM customers c
WHERE EXISTS (
  SELECT 1 FROM orders o
  WHERE o.customer_id = c.customer_id
    AND o.total_amount > 1000
);

-- Limit result sets
SELECT * FROM orders
ORDER BY order_date DESC
LIMIT 100;

-- Use appropriate data types
-- Smaller data types = better performance
-- TINYINT vs INT for small ranges
-- VARCHAR vs TEXT for strings
```

**Exercise 6.1:** Index optimization challenge
- Analyze slow query
- Add appropriate indexes
- Measure performance improvement
- Identify unused indexes

<details>
<summary>Solution</summary>

```sql
-- Create test data for analysis
CREATE TABLE IF NOT EXISTS test_orders (
  order_id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  total_amount DECIMAL(10, 2),
  status VARCHAR(20)
) ENGINE=InnoDB;

-- Insert 100,000 test orders
DELIMITER $$
CREATE PROCEDURE generate_test_orders()
BEGIN
  DECLARE i INT DEFAULT 1;
  WHILE i <= 100000 DO
    INSERT INTO test_orders (customer_id, order_date, total_amount, status)
    VALUES (
      FLOOR(1 + RAND() * 1000),
      DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 365) DAY),
      ROUND(RAND() * 500 + 50, 2),
      ELT(FLOOR(RAND() * 5) + 1, 'pending', 'processing', 'shipped', 'delivered', 'cancelled')
    );
    SET i = i + 1;
    IF i % 10000 = 0 THEN
      COMMIT;
    END IF;
  END WHILE;
END$$
DELIMITER ;

CALL generate_test_orders();

-- Slow Query: Find orders by customer and date range
SET profiling = 1;

SELECT *
FROM test_orders
WHERE customer_id = 500
  AND order_date >= '2024-01-01'
  AND status = 'delivered'
ORDER BY order_date DESC;

SHOW PROFILES;

-- Analyze query performance BEFORE optimization
EXPLAIN
SELECT *
FROM test_orders
WHERE customer_id = 500
  AND order_date >= '2024-01-01'
  AND status = 'delivered'
ORDER BY order_date DESC;

-- Add optimized indexes
CREATE INDEX idx_customer_date ON test_orders(customer_id, order_date);
CREATE INDEX idx_status ON test_orders(status);

-- Or better: composite index covering all conditions
CREATE INDEX idx_customer_date_status ON test_orders(customer_id, status, order_date);

-- Analyze query performance AFTER optimization
EXPLAIN
SELECT *
FROM test_orders
WHERE customer_id = 500
  AND order_date >= '2024-01-01'
  AND status = 'delivered'
ORDER BY order_date DESC;

-- Measure performance improvement
SELECT SQL_NO_CACHE *
FROM test_orders
WHERE customer_id = 500
  AND order_date >= '2024-01-01'
  AND status = 'delivered'
ORDER BY order_date DESC;

SHOW PROFILES;

-- Find unused indexes
SELECT
  s.TABLE_SCHEMA,
  s.TABLE_NAME,
  s.INDEX_NAME,
  s.CARDINALITY
FROM information_schema.STATISTICS s
LEFT JOIN (
  SELECT DISTINCT
    object_schema,
    object_name,
    index_name
  FROM performance_schema.table_io_waits_summary_by_index_usage
  WHERE index_name IS NOT NULL
    AND index_name != 'PRIMARY'
    AND count_star > 0
) u ON s.TABLE_SCHEMA = u.object_schema
  AND s.TABLE_NAME = u.object_name
  AND s.INDEX_NAME = u.index_name
WHERE s.TABLE_SCHEMA = 'ecommerce'
  AND s.INDEX_NAME != 'PRIMARY'
  AND u.index_name IS NULL
GROUP BY s.TABLE_SCHEMA, s.TABLE_NAME, s.INDEX_NAME;

-- Analyze index efficiency
SELECT
  TABLE_NAME,
  INDEX_NAME,
  CARDINALITY,
  COLUMN_NAME,
  ROUND(CARDINALITY / (
    SELECT TABLE_ROWS
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = 'ecommerce'
      AND TABLE_NAME = s.TABLE_NAME
  ) * 100, 2) AS selectivity_percent
FROM information_schema.STATISTICS s
WHERE TABLE_SCHEMA = 'ecommerce'
  AND TABLE_NAME = 'test_orders'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- Index size analysis
SELECT
  TABLE_NAME,
  INDEX_NAME,
  ROUND(STAT_VALUE * @@innodb_page_size / 1024 / 1024, 2) AS index_size_mb
FROM mysql.innodb_index_stats
WHERE database_name = 'ecommerce'
  AND TABLE_NAME = 'test_orders'
  AND stat_name = 'size'
ORDER BY index_size_mb DESC;

-- Drop unused indexes (example)
-- DROP INDEX idx_status ON test_orders;

-- Cleanup
DROP PROCEDURE IF EXISTS generate_test_orders;
SET profiling = 0;
```
</details>

---

## 7. Stored Procedures and Functions

**Time:** 45 minutes

### 7.1 Stored Procedures

```sql
-- Simple procedure
DELIMITER $$

CREATE PROCEDURE get_customer_orders(IN p_customer_id INT)
BEGIN
  SELECT * FROM orders
  WHERE customer_id = p_customer_id
  ORDER BY order_date DESC;
END$$

DELIMITER ;

-- Call procedure
CALL get_customer_orders(1);

-- Procedure with multiple parameters
DELIMITER $$

CREATE PROCEDURE create_order(
  IN p_customer_id INT,
  IN p_total_amount DECIMAL(10, 2),
  OUT p_order_id INT
)
BEGIN
  INSERT INTO orders (customer_id, total_amount, status)
  VALUES (p_customer_id, p_total_amount, 'pending');

  SET p_order_id = LAST_INSERT_ID();
END$$

DELIMITER ;

-- Call with OUT parameter
CALL create_order(1, 99.99, @new_order_id);
SELECT @new_order_id;

-- Procedure with transaction
DELIMITER $$

CREATE PROCEDURE process_order_payment(
  IN p_order_id INT,
  IN p_payment_amount DECIMAL(10, 2)
)
BEGIN
  DECLARE v_order_total DECIMAL(10, 2);
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    SELECT 'Error occurred, transaction rolled back' AS message;
  END;

  START TRANSACTION;

  -- Get order total
  SELECT total_amount INTO v_order_total
  FROM orders
  WHERE order_id = p_order_id
  FOR UPDATE;

  -- Verify payment amount
  IF p_payment_amount < v_order_total THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Insufficient payment amount';
  END IF;

  -- Update order status
  UPDATE orders
  SET status = 'paid'
  WHERE order_id = p_order_id;

  COMMIT;
  SELECT 'Payment processed successfully' AS message;
END$$

DELIMITER ;
```

### 7.2 Stored Functions

```sql
-- Simple function
DELIMITER $$

CREATE FUNCTION calculate_discount(p_total DECIMAL(10, 2))
RETURNS DECIMAL(10, 2)
DETERMINISTIC
BEGIN
  DECLARE v_discount DECIMAL(10, 2);

  IF p_total >= 1000 THEN
    SET v_discount = p_total * 0.15;
  ELSEIF p_total >= 500 THEN
    SET v_discount = p_total * 0.10;
  ELSEIF p_total >= 100 THEN
    SET v_discount = p_total * 0.05;
  ELSE
    SET v_discount = 0;
  END IF;

  RETURN v_discount;
END$$

DELIMITER ;

-- Use function in query
SELECT
  order_id,
  total_amount,
  calculate_discount(total_amount) AS discount,
  total_amount - calculate_discount(total_amount) AS final_amount
FROM orders;

-- Function with complex logic
DELIMITER $$

CREATE FUNCTION get_customer_segment(p_customer_id INT)
RETURNS VARCHAR(20)
READS SQL DATA
BEGIN
  DECLARE v_total_spent DECIMAL(10, 2);
  DECLARE v_segment VARCHAR(20);

  SELECT COALESCE(SUM(total_amount), 0) INTO v_total_spent
  FROM orders
  WHERE customer_id = p_customer_id
    AND status = 'delivered';

  IF v_total_spent >= 5000 THEN
    SET v_segment = 'VIP';
  ELSEIF v_total_spent >= 2000 THEN
    SET v_segment = 'Premium';
  ELSEIF v_total_spent >= 500 THEN
    SET v_segment = 'Standard';
  ELSE
    SET v_segment = 'Basic';
  END IF;

  RETURN v_segment;
END$$

DELIMITER ;
```

### 7.3 Control Flow

```sql
DELIMITER $$

CREATE PROCEDURE example_control_flow(IN p_value INT)
BEGIN
  -- IF statement
  IF p_value > 100 THEN
    SELECT 'Large value';
  ELSEIF p_value > 50 THEN
    SELECT 'Medium value';
  ELSE
    SELECT 'Small value';
  END IF;

  -- CASE statement
  CASE
    WHEN p_value > 100 THEN
      SELECT 'Large';
    WHEN p_value > 50 THEN
      SELECT 'Medium';
    ELSE
      SELECT 'Small';
  END CASE;

  -- LOOP
  DECLARE v_counter INT DEFAULT 0;
  my_loop: LOOP
    SET v_counter = v_counter + 1;
    IF v_counter >= 10 THEN
      LEAVE my_loop;
    END IF;
  END LOOP;

  -- WHILE loop
  SET v_counter = 0;
  WHILE v_counter < 10 DO
    SET v_counter = v_counter + 1;
  END WHILE;

  -- REPEAT loop
  SET v_counter = 0;
  REPEAT
    SET v_counter = v_counter + 1;
  UNTIL v_counter >= 10
  END REPEAT;
END$$

DELIMITER ;
```

**Exercise 7.1:** Build complete order processing system
- Procedure to create order with items
- Function to calculate shipping cost
- Transaction handling
- Error handling

<details>
<summary>Solution</summary>

```sql
-- Shipping cost calculator function
DELIMITER $$

CREATE FUNCTION calculate_shipping_cost(
  p_total_amount DECIMAL(10, 2),
  p_item_count INT,
  p_weight DECIMAL(8, 2)
)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
BEGIN
  DECLARE v_shipping_cost DECIMAL(10, 2);

  -- Free shipping for orders over $100
  IF p_total_amount >= 100 THEN
    RETURN 0.00;
  END IF;

  -- Base shipping cost
  SET v_shipping_cost = 5.99;

  -- Add per-item fee
  SET v_shipping_cost = v_shipping_cost + (p_item_count * 0.50);

  -- Add weight-based fee
  IF p_weight > 5 THEN
    SET v_shipping_cost = v_shipping_cost + ((p_weight - 5) * 0.25);
  END IF;

  -- Cap at $20
  IF v_shipping_cost > 20 THEN
    SET v_shipping_cost = 20.00;
  END IF;

  RETURN ROUND(v_shipping_cost, 2);
END$$

DELIMITER ;

-- Complete order processing procedure
DELIMITER $$

CREATE PROCEDURE create_complete_order(
  IN p_customer_id INT,
  IN p_items JSON,
  IN p_shipping_address TEXT,
  OUT p_order_id INT,
  OUT p_error_message VARCHAR(255)
)
BEGIN
  DECLARE v_item_index INT DEFAULT 0;
  DECLARE v_item_count INT;
  DECLARE v_subtotal DECIMAL(10, 2) DEFAULT 0;
  DECLARE v_shipping_cost DECIMAL(10, 2);
  DECLARE v_total_amount DECIMAL(10, 2);
  DECLARE v_total_weight DECIMAL(8, 2) DEFAULT 0;
  DECLARE v_product_id INT;
  DECLARE v_quantity INT;
  DECLARE v_unit_price DECIMAL(10, 2);
  DECLARE v_weight DECIMAL(8, 2);
  DECLARE v_stock INT;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    SET p_error_message = 'Transaction failed';
    SET p_order_id = NULL;
  END;

  SET p_error_message = NULL;
  SET p_order_id = NULL;

  -- Validate customer exists
  IF NOT EXISTS (SELECT 1 FROM customers WHERE customer_id = p_customer_id AND is_active = TRUE) THEN
    SET p_error_message = 'Customer not found or inactive';
    RETURN;
  END IF;

  -- Get item count
  SET v_item_count = JSON_LENGTH(p_items);

  IF v_item_count = 0 THEN
    SET p_error_message = 'No items in order';
    RETURN;
  END IF;

  START TRANSACTION;

  -- Validate items and calculate totals
  WHILE v_item_index < v_item_count DO
    SET v_product_id = JSON_EXTRACT(p_items, CONCAT('$[', v_item_index, '].product_id'));
    SET v_quantity = JSON_EXTRACT(p_items, CONCAT('$[', v_item_index, '].quantity'));

    -- Get product details
    SELECT
      price,
      weight,
      stock_quantity
    INTO
      v_unit_price,
      v_weight,
      v_stock
    FROM products
    WHERE product_id = v_product_id
      AND is_active = TRUE
    FOR UPDATE;

    -- Validate product exists
    IF v_unit_price IS NULL THEN
      ROLLBACK;
      SET p_error_message = CONCAT('Product ', v_product_id, ' not found');
      RETURN;
    END IF;

    -- Validate stock
    IF v_stock < v_quantity THEN
      ROLLBACK;
      SET p_error_message = CONCAT('Insufficient stock for product ', v_product_id);
      RETURN;
    END IF;

    -- Update stock
    UPDATE products
    SET stock_quantity = stock_quantity - v_quantity
    WHERE product_id = v_product_id;

    -- Calculate subtotal and weight
    SET v_subtotal = v_subtotal + (v_unit_price * v_quantity);
    SET v_total_weight = v_total_weight + (v_weight * v_quantity);

    SET v_item_index = v_item_index + 1;
  END WHILE;

  -- Calculate shipping
  SET v_shipping_cost = calculate_shipping_cost(v_subtotal, v_item_count, v_total_weight);
  SET v_total_amount = v_subtotal + v_shipping_cost;

  -- Create order
  INSERT INTO orders (customer_id, total_amount, status, shipping_address)
  VALUES (p_customer_id, v_total_amount, 'pending', p_shipping_address);

  SET p_order_id = LAST_INSERT_ID();

  -- Add order items
  SET v_item_index = 0;
  WHILE v_item_index < v_item_count DO
    SET v_product_id = JSON_EXTRACT(p_items, CONCAT('$[', v_item_index, '].product_id'));
    SET v_quantity = JSON_EXTRACT(p_items, CONCAT('$[', v_item_index, '].quantity'));

    SELECT price INTO v_unit_price
    FROM products
    WHERE product_id = v_product_id;

    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
    VALUES (p_order_id, v_product_id, v_quantity, v_unit_price);

    SET v_item_index = v_item_index + 1;
  END WHILE;

  -- Update customer loyalty points
  UPDATE customers
  SET loyalty_points = loyalty_points + FLOOR(v_total_amount * 0.1)
  WHERE customer_id = p_customer_id;

  COMMIT;
END$$

DELIMITER ;

-- Test the order processing
SET @order_id = NULL;
SET @error = NULL;

CALL create_complete_order(
  1,
  '[{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 1}]',
  '123 Main St, New York, NY 10001',
  @order_id,
  @error
);

SELECT @order_id AS order_id, @error AS error_message;

-- Verify order
SELECT
  o.order_id,
  o.customer_id,
  o.total_amount,
  o.status,
  (SELECT COUNT(*) FROM order_items WHERE order_id = o.order_id) AS item_count
FROM orders o
WHERE order_id = @order_id;

-- Cancel order procedure
DELIMITER $$

CREATE PROCEDURE cancel_order(
  IN p_order_id INT,
  OUT p_error_message VARCHAR(255)
)
BEGIN
  DECLARE v_status VARCHAR(20);

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    SET p_error_message = 'Failed to cancel order';
  END;

  SET p_error_message = NULL;

  -- Get current status
  SELECT status INTO v_status
  FROM orders
  WHERE order_id = p_order_id;

  IF v_status IS NULL THEN
    SET p_error_message = 'Order not found';
    RETURN;
  END IF;

  IF v_status IN ('shipped', 'delivered') THEN
    SET p_error_message = 'Cannot cancel shipped or delivered order';
    RETURN;
  END IF;

  START TRANSACTION;

  -- Restore stock
  UPDATE products p
  JOIN order_items oi ON p.product_id = oi.product_id
  SET p.stock_quantity = p.stock_quantity + oi.quantity
  WHERE oi.order_id = p_order_id;

  -- Update order status
  UPDATE orders
  SET status = 'cancelled'
  WHERE order_id = p_order_id;

  COMMIT;
END$$

DELIMITER ;
```
</details>

---

## 8. Triggers and Events

**Time:** 30 minutes

### 8.1 Triggers

```sql
-- BEFORE INSERT trigger
DELIMITER $$

CREATE TRIGGER before_customer_insert
BEFORE INSERT ON customers
FOR EACH ROW
BEGIN
  SET NEW.email = LOWER(NEW.email);
  SET NEW.created_at = NOW();
END$$

DELIMITER ;

-- AFTER INSERT trigger
DELIMITER $$

CREATE TRIGGER after_order_insert
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
  -- Log order creation
  INSERT INTO order_audit_log (order_id, action, user, timestamp)
  VALUES (NEW.order_id, 'CREATED', USER(), NOW());
END$$

DELIMITER ;

-- BEFORE UPDATE trigger
DELIMITER $$

CREATE TRIGGER before_product_update
BEFORE UPDATE ON products
FOR EACH ROW
BEGIN
  IF NEW.price < 0 THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Price cannot be negative';
  END IF;

  SET NEW.updated_at = NOW();
END$$

DELIMITER ;

-- AFTER UPDATE trigger
DELIMITER $$

CREATE TRIGGER after_order_status_update
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
  IF NEW.status != OLD.status THEN
    INSERT INTO order_status_history (order_id, old_status, new_status, changed_at)
    VALUES (NEW.order_id, OLD.status, NEW.status, NOW());
  END IF;
END$$

DELIMITER ;

-- Show triggers
SHOW TRIGGERS;

-- Drop trigger
DROP TRIGGER IF EXISTS before_customer_insert;
```

### 8.2 Events

```sql
-- Enable event scheduler
SET GLOBAL event_scheduler = ON;

-- Create recurring event
DELIMITER $$

CREATE EVENT cleanup_old_sessions
ON SCHEDULE EVERY 1 HOUR
DO
BEGIN
  DELETE FROM sessions
  WHERE last_activity < DATE_SUB(NOW(), INTERVAL 24 HOUR);
END$$

DELIMITER ;

-- One-time event
DELIMITER $$

CREATE EVENT generate_monthly_report
ON SCHEDULE AT '2024-02-01 00:00:00'
DO
BEGIN
  INSERT INTO monthly_reports (month, total_orders, total_revenue, created_at)
  SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS total_revenue,
    NOW()
  FROM orders
  WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
    AND status = 'delivered'
  GROUP BY month;
END$$

DELIMITER ;

-- Show events
SHOW EVENTS;

-- Disable event
ALTER EVENT cleanup_old_sessions DISABLE;

-- Drop event
DROP EVENT IF EXISTS cleanup_old_sessions;
```

**Exercise 8.1:** Build audit system with triggers
- Track all changes to orders table
- Automatically update timestamps
- Validate business rules
- Schedule cleanup tasks

<details>
<summary>Solution</summary>

```sql
-- Create audit table
CREATE TABLE order_audit (
  audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  order_id INT,
  action VARCHAR(10),
  old_data JSON,
  new_data JSON,
  changed_by VARCHAR(100),
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_order (order_id),
  INDEX idx_action (action),
  INDEX idx_changed_at (changed_at)
) ENGINE=InnoDB;

-- Audit trigger for INSERT
DELIMITER $$

CREATE TRIGGER audit_order_insert
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
  INSERT INTO order_audit (order_id, action, new_data, changed_by)
  VALUES (
    NEW.order_id,
    'INSERT',
    JSON_OBJECT(
      'customer_id', NEW.customer_id,
      'total_amount', NEW.total_amount,
      'status', NEW.status,
      'order_date', NEW.order_date
    ),
    USER()
  );
END$$

DELIMITER ;

-- Audit trigger for UPDATE
DELIMITER $$

CREATE TRIGGER audit_order_update
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
  INSERT INTO order_audit (order_id, action, old_data, new_data, changed_by)
  VALUES (
    NEW.order_id,
    'UPDATE',
    JSON_OBJECT(
      'customer_id', OLD.customer_id,
      'total_amount', OLD.total_amount,
      'status', OLD.status,
      'order_date', OLD.order_date
    ),
    JSON_OBJECT(
      'customer_id', NEW.customer_id,
      'total_amount', NEW.total_amount,
      'status', NEW.status,
      'order_date', NEW.order_date
    ),
    USER()
  );
END$$

DELIMITER ;

-- Audit trigger for DELETE
DELIMITER $$

CREATE TRIGGER audit_order_delete
BEFORE DELETE ON orders
FOR EACH ROW
BEGIN
  INSERT INTO order_audit (order_id, action, old_data, changed_by)
  VALUES (
    OLD.order_id,
    'DELETE',
    JSON_OBJECT(
      'customer_id', OLD.customer_id,
      'total_amount', OLD.total_amount,
      'status', OLD.status,
      'order_date', OLD.order_date
    ),
    USER()
  );
END$$

DELIMITER ;

-- Business rule: Prevent editing delivered orders
DELIMITER $$

CREATE TRIGGER prevent_delivered_order_changes
BEFORE UPDATE ON orders
FOR EACH ROW
BEGIN
  IF OLD.status = 'delivered' AND NEW.status != 'delivered' THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Cannot modify delivered orders';
  END IF;
END$$

DELIMITER ;

-- Auto-update order total when items change
DELIMITER $$

CREATE TRIGGER update_order_total
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
  UPDATE orders
  SET total_amount = (
    SELECT SUM(subtotal)
    FROM order_items
    WHERE order_id = NEW.order_id
  )
  WHERE order_id = NEW.order_id;
END$$

DELIMITER ;

-- Scheduled event: Archive old orders
DELIMITER $$

CREATE EVENT archive_old_orders
ON SCHEDULE EVERY 1 DAY
STARTS '2024-01-01 02:00:00'
DO
BEGIN
  -- Archive orders older than 2 years
  INSERT INTO archived_orders
  SELECT * FROM orders
  WHERE order_date < DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    AND status IN ('delivered', 'cancelled');

  -- Delete archived orders
  DELETE FROM orders
  WHERE order_date < DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
    AND status IN ('delivered', 'cancelled');
END$$

DELIMITER ;

-- Scheduled event: Update customer segments
DELIMITER $$

CREATE EVENT update_customer_segments
ON SCHEDULE EVERY 1 WEEK
STARTS '2024-01-01 00:00:00'
DO
BEGIN
  UPDATE customers c
  SET loyalty_segment = (
    CASE
      WHEN (
        SELECT SUM(total_amount)
        FROM orders o
        WHERE o.customer_id = c.customer_id
          AND o.status = 'delivered'
      ) >= 5000 THEN 'VIP'
      WHEN (
        SELECT SUM(total_amount)
        FROM orders o
        WHERE o.customer_id = c.customer_id
          AND o.status = 'delivered'
      ) >= 2000 THEN 'Premium'
      ELSE 'Standard'
    END
  );
END$$

DELIMITER ;

-- Test audit system
INSERT INTO orders (customer_id, total_amount, status)
VALUES (1, 99.99, 'pending');

UPDATE orders
SET status = 'processing'
WHERE order_id = LAST_INSERT_ID();

-- View audit log
SELECT
  audit_id,
  order_id,
  action,
  JSON_PRETTY(old_data) AS old_data,
  JSON_PRETTY(new_data) AS new_data,
  changed_by,
  changed_at
FROM order_audit
ORDER BY audit_id DESC
LIMIT 10;
```
</details>

---

## 9. Transactions and Locking

**Time:** 30 minutes

### 9.1 Transactions

```sql
-- Basic transaction
START TRANSACTION;

UPDATE accounts
SET balance = balance - 100
WHERE account_id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE account_id = 2;

COMMIT;

-- Transaction with rollback
START TRANSACTION;

UPDATE products
SET stock_quantity = stock_quantity - 10
WHERE product_id = 1;

-- Check if update was successful
IF ROW_COUNT() = 0 THEN
  ROLLBACK;
ELSE
  COMMIT;
END IF;

-- Savepoints
START TRANSACTION;

INSERT INTO orders (customer_id, total_amount) VALUES (1, 99.99);
SAVEPOINT order_created;

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
VALUES (LAST_INSERT_ID(), 1, 2, 49.99);

-- Something went wrong
ROLLBACK TO SAVEPOINT order_created;

COMMIT;
```

### 9.2 Isolation Levels

```sql
-- Set isolation level
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;  -- Default
SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Check current isolation level
SELECT @@transaction_isolation;
```

### 9.3 Locking

```sql
-- SELECT FOR UPDATE (exclusive lock)
START TRANSACTION;

SELECT * FROM products
WHERE product_id = 1
FOR UPDATE;

-- Make changes
UPDATE products
SET stock_quantity = stock_quantity - 5
WHERE product_id = 1;

COMMIT;

-- SELECT FOR SHARE (shared lock)
SELECT * FROM customers
WHERE customer_id = 1
FOR SHARE;

-- NOWAIT (fail immediately if locked)
SELECT * FROM orders
WHERE order_id = 123
FOR UPDATE NOWAIT;

-- SKIP LOCKED (skip locked rows)
SELECT * FROM tasks
WHERE status = 'pending'
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

**Exercise 9.1:** Implement concurrent order processing
- Handle inventory updates safely
- Prevent double-booking
- Implement queuing system

<details>
<summary>Solution</summary>

```sql
-- Safe order processing with locking
DELIMITER $$

CREATE PROCEDURE process_order_safe(
  IN p_customer_id INT,
  IN p_product_id INT,
  IN p_quantity INT,
  OUT p_order_id INT,
  OUT p_error VARCHAR(255)
)
BEGIN
  DECLARE v_stock INT;
  DECLARE v_price DECIMAL(10, 2);

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    SET p_error = 'Transaction failed';
    SET p_order_id = NULL;
  END;

  SET p_error = NULL;
  SET p_order_id = NULL;

  START TRANSACTION;

  -- Lock product row for update
  SELECT
    stock_quantity,
    price
  INTO
    v_stock,
    v_price
  FROM products
  WHERE product_id = p_product_id
    AND is_active = TRUE
  FOR UPDATE;

  -- Check stock availability
  IF v_stock < p_quantity THEN
    ROLLBACK;
    SET p_error = CONCAT('Insufficient stock. Available: ', v_stock);
    RETURN;
  END IF;

  -- Update stock
  UPDATE products
  SET stock_quantity = stock_quantity - p_quantity
  WHERE product_id = p_product_id;

  -- Create order
  INSERT INTO orders (customer_id, total_amount, status)
  VALUES (p_customer_id, v_price * p_quantity, 'processing');

  SET p_order_id = LAST_INSERT_ID();

  -- Add order item
  INSERT INTO order_items (order_id, product_id, quantity, unit_price)
  VALUES (p_order_id, p_product_id, p_quantity, v_price);

  COMMIT;
END$$

DELIMITER ;

-- Task queue processor (prevents double-processing)
DELIMITER $$

CREATE PROCEDURE get_next_task(
  OUT p_task_id INT,
  OUT p_task_data JSON
)
BEGIN
  DECLARE v_done INT DEFAULT FALSE;

  START TRANSACTION;

  -- Get next pending task with lock, skip locked rows
  SELECT task_id, data
  INTO p_task_id, p_task_data
  FROM tasks
  WHERE status = 'pending'
  ORDER BY created_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1;

  IF p_task_id IS NOT NULL THEN
    -- Mark as processing
    UPDATE tasks
    SET status = 'processing',
        processing_started_at = NOW(),
        worker_id = CONNECTION_ID()
    WHERE task_id = p_task_id;
  END IF;

  COMMIT;
END$$

DELIMITER ;

-- Complete task
DELIMITER $$

CREATE PROCEDURE complete_task(
  IN p_task_id INT,
  IN p_result JSON
)
BEGIN
  UPDATE tasks
  SET status = 'completed',
      result = p_result,
      completed_at = NOW()
  WHERE task_id = p_task_id
    AND status = 'processing';
END$$

DELIMITER ;

-- Test concurrent processing
-- Simulate multiple workers
-- Session 1:
CALL get_next_task(@task_id1, @task_data1);
SELECT @task_id1, @task_data1;

-- Session 2 (simultaneously):
CALL get_next_task(@task_id2, @task_data2);
SELECT @task_id2, @task_data2;

-- They should get different tasks due to SKIP LOCKED

-- Deadlock prevention example
DELIMITER $$

CREATE PROCEDURE transfer_inventory(
  IN p_from_product INT,
  IN p_to_product INT,
  IN p_quantity INT
)
BEGIN
  DECLARE v_lock_order_1 INT;
  DECLARE v_lock_order_2 INT;

  -- Always lock in same order to prevent deadlocks
  SET v_lock_order_1 = LEAST(p_from_product, p_to_product);
  SET v_lock_order_2 = GREATEST(p_from_product, p_to_product);

  START TRANSACTION;

  -- Lock products in consistent order
  SELECT stock_quantity
  FROM products
  WHERE product_id = v_lock_order_1
  FOR UPDATE;

  SELECT stock_quantity
  FROM products
  WHERE product_id = v_lock_order_2
  FOR UPDATE;

  -- Perform transfer
  UPDATE products
  SET stock_quantity = stock_quantity - p_quantity
  WHERE product_id = p_from_product;

  UPDATE products
  SET stock_quantity = stock_quantity + p_quantity
  WHERE product_id = p_to_product;

  COMMIT;
END$$

DELIMITER ;
```
</details>

---

## 10. Replication Basics

**Time:** 45 minutes

### 10.1 Master-Slave Replication Setup

```bash
# Master configuration (my.cnf)
[mysqld]
server-id=1
log-bin=mysql-bin
binlog-format=ROW
binlog-do-db=mydb

# Slave configuration (my.cnf)
[mysqld]
server-id=2
relay-log=mysql-relay-bin
read-only=1
```

### 10.2 Replication Commands

```sql
-- On master: Create replication user
CREATE USER 'repl'@'%' IDENTIFIED BY 'repl_password';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
FLUSH PRIVILEGES;

-- Get master status
SHOW MASTER STATUS;

-- On slave: Configure replication
CHANGE MASTER TO
  MASTER_HOST='master_host',
  MASTER_USER='repl',
  MASTER_PASSWORD='repl_password',
  MASTER_LOG_FILE='mysql-bin.000001',
  MASTER_LOG_POS=154;

-- Start slave
START SLAVE;

-- Check slave status
SHOW SLAVE STATUS\G

-- Stop slave
STOP SLAVE;

-- Reset slave
RESET SLAVE;
```

### 10.3 Monitoring Replication

```sql
-- Check replication lag
SHOW SLAVE STATUS\G

-- Look for:
-- Seconds_Behind_Master
-- Slave_IO_Running: Yes
-- Slave_SQL_Running: Yes

-- View binary log events
SHOW BINLOG EVENTS IN 'mysql-bin.000001';

-- View relay log events
SHOW RELAYLOG EVENTS;
```

---

## 11. Backup and Restore

**Time:** 30 minutes

### 11.1 mysqldump

```bash
# Backup single database
docker exec my-mysql mysqldump -u root -p mydb > mydb_backup.sql

# Backup all databases
docker exec my-mysql mysqldump -u root -p --all-databases > all_databases_backup.sql

# Backup with routines and events
docker exec my-mysql mysqldump -u root -p --routines --events mydb > mydb_complete_backup.sql

# Backup specific tables
docker exec my-mysql mysqldump -u root -p mydb customers orders > tables_backup.sql

# Backup structure only
docker exec my-mysql mysqldump -u root -p --no-data mydb > mydb_schema.sql

# Backup data only
docker exec my-mysql mysqldump -u root -p --no-create-info mydb > mydb_data.sql
```

### 11.2 Restore

```bash
# Restore database
docker exec -i my-mysql mysql -u root -p mydb < mydb_backup.sql

# Restore all databases
docker exec -i my-mysql mysql -u root -p < all_databases_backup.sql

# Restore to different database
docker exec -i my-mysql mysql -u root -p new_db < mydb_backup.sql
```

### 11.3 Automated Backup Script

```bash
#!/bin/bash
# mysql-backup.sh

CONTAINER="my-mysql"
USER="root"
PASSWORD="root_password"
BACKUP_DIR="/backups/mysql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASES=("mydb" "app_db")
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

for DB in "${DATABASES[@]}"; do
  echo "Backing up $DB..."

  docker exec $CONTAINER mysqldump \
    -u $USER \
    -p$PASSWORD \
    --routines \
    --events \
    --single-transaction \
    --quick \
    --lock-tables=false \
    $DB > $BACKUP_DIR/${DB}_${TIMESTAMP}.sql

  if [ -f "$BACKUP_DIR/${DB}_${TIMESTAMP}.sql" ]; then
    gzip $BACKUP_DIR/${DB}_${TIMESTAMP}.sql
    echo "Backup completed: ${DB}_${TIMESTAMP}.sql.gz"
  else
    echo "Backup failed for $DB"
  fi
done

# Delete old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup process completed"
```

---

## 12. Performance Tuning

**Time:** 45 minutes

### 12.1 Configuration Optimization

```sql
-- View configuration
SHOW VARIABLES LIKE '%buffer%';
SHOW VARIABLES LIKE '%cache%';

-- Key buffer (for MyISAM)
SET GLOBAL key_buffer_size = 256M;

-- InnoDB buffer pool
SET GLOBAL innodb_buffer_pool_size = 2G;

-- Query cache (deprecated in MySQL 8.0)
-- SET GLOBAL query_cache_size = 256M;

-- Max connections
SET GLOBAL max_connections = 200;

-- Slow query log
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 2;
```

### 12.2 Query Optimization

```sql
-- Analyze queries
EXPLAIN SELECT * FROM orders WHERE customer_id = 1;

-- Use indexes effectively
CREATE INDEX idx_customer_status ON orders(customer_id, status);

-- Avoid SELECT *
SELECT order_id, total_amount FROM orders;

-- Use LIMIT
SELECT * FROM orders ORDER BY order_date DESC LIMIT 100;

-- Optimize joins
-- Ensure join columns are indexed
CREATE INDEX idx_customer_id ON orders(customer_id);
```

### 12.3 Monitoring

```sql
-- Process list
SHOW FULL PROCESSLIST;

-- Table status
SHOW TABLE STATUS;

-- InnoDB status
SHOW ENGINE INNODB STATUS\G

-- Performance schema queries
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

---

## 13. Real-World Scenarios

### Scenario 1: E-commerce Order System
(See Exercise solutions above for complete implementation)

### Scenario 2: User Analytics
```sql
-- Daily active users
SELECT
  DATE(login_time) AS date,
  COUNT(DISTINCT user_id) AS dau
FROM user_logins
WHERE login_time >= CURDATE() - INTERVAL 30 DAY
GROUP BY date;

-- Monthly cohort retention
WITH cohorts AS (
  SELECT
    user_id,
    DATE_FORMAT(MIN(login_time), '%Y-%m') AS cohort_month
  FROM user_logins
  GROUP BY user_id
)
SELECT
  c.cohort_month,
  COUNT(DISTINCT c.user_id) AS cohort_size,
  COUNT(DISTINCT CASE WHEN l.login_time >= '2024-01-01' THEN l.user_id END) AS active_users
FROM cohorts c
LEFT JOIN user_logins l ON c.user_id = l.user_id
GROUP BY c.cohort_month;
```

---

## 14. Troubleshooting

### Common Issues

#### Issue 1: Slow Queries
```sql
-- Find slow queries
SELECT * FROM mysql.slow_log
ORDER BY query_time DESC
LIMIT 10;

-- Or use performance schema
SELECT
  DIGEST_TEXT,
  COUNT_STAR,
  AVG_TIMER_WAIT/1000000000 AS avg_time_ms
FROM performance_schema.events_statements_summary_by_digest
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 10;
```

#### Issue 2: Deadlocks
```sql
-- Show InnoDB status (includes deadlock info)
SHOW ENGINE INNODB STATUS\G

-- Enable innodb_print_all_deadlocks
SET GLOBAL innodb_print_all_deadlocks = ON;
```

#### Issue 3: High Memory Usage
```sql
-- Check buffer pool usage
SELECT
  POOL_ID,
  POOL_SIZE,
  FREE_BUFFERS,
  DATABASE_PAGES,
  OLD_DATABASE_PAGES
FROM information_schema.INNODB_BUFFER_POOL_STATS;
```

---

## Conclusion

You've completed the MySQL Complete Guide! You should now be able to:

✅ Set up and configure MySQL databases
✅ Design efficient database schemas
✅ Write optimized queries with proper indexing
✅ Create stored procedures and functions
✅ Implement triggers and events
✅ Handle transactions safely
✅ Set up replication
✅ Perform backups and optimization

**Next Steps:**
1. Explore MySQL 8.0 features (window functions, CTEs)
2. Learn about MySQL clustering (Group Replication)
3. Study advanced performance tuning
4. Practice with production workloads

Happy querying! 🐬
