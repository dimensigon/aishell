-- E-Commerce Sample Data Generator
-- This generates realistic sample data for demonstration

-- Insert categories
INSERT INTO categories (name, slug, description, image_url) VALUES
('Electronics', 'electronics', 'Electronic devices and accessories', 'https://example.com/cat/electronics.jpg'),
('Computers', 'computers', 'Laptops, desktops, and computer accessories', 'https://example.com/cat/computers.jpg'),
('Mobile Phones', 'mobile-phones', 'Smartphones and mobile accessories', 'https://example.com/cat/mobile.jpg'),
('Clothing', 'clothing', 'Fashion and apparel', 'https://example.com/cat/clothing.jpg'),
('Books', 'books', 'Books and magazines', 'https://example.com/cat/books.jpg'),
('Home & Garden', 'home-garden', 'Home improvement and gardening', 'https://example.com/cat/home.jpg'),
('Sports', 'sports', 'Sports equipment and accessories', 'https://example.com/cat/sports.jpg'),
('Toys', 'toys', 'Toys and games', 'https://example.com/cat/toys.jpg'),
('Beauty', 'beauty', 'Beauty and personal care', 'https://example.com/cat/beauty.jpg'),
('Automotive', 'automotive', 'Auto parts and accessories', 'https://example.com/cat/auto.jpg');

-- Sample products (this is a starter set - use generate-data.js for full 10k)
INSERT INTO products (sku, name, description, category_id, price, cost, stock, reorder_point, weight_kg, is_featured) VALUES
('ELEC-001', 'Wireless Bluetooth Headphones', 'Premium wireless headphones with noise cancellation', 1, 89.99, 45.00, 150, 20, 0.3, true),
('COMP-001', 'Gaming Laptop 15.6"', 'High-performance gaming laptop with RTX graphics', 2, 1299.99, 900.00, 25, 5, 2.5, true),
('MOBI-001', 'Smartphone Pro Max', 'Latest flagship smartphone with 5G', 3, 999.99, 600.00, 100, 10, 0.2, true),
('CLOT-001', 'Cotton T-Shirt', 'Comfortable cotton t-shirt', 4, 19.99, 8.00, 500, 50, 0.2, false),
('BOOK-001', 'The Art of Database Design', 'Comprehensive guide to database design', 5, 49.99, 20.00, 200, 20, 0.8, false),
('HOME-001', 'LED Desk Lamp', 'Adjustable LED desk lamp', 6, 39.99, 18.00, 150, 25, 0.5, false),
('SPOR-001', 'Yoga Mat Premium', 'Non-slip yoga mat with carrying strap', 7, 29.99, 12.00, 300, 40, 1.2, false),
('TOYS-001', 'Educational Building Blocks', 'STEM learning building block set', 8, 34.99, 15.00, 200, 30, 1.5, false),
('BEAU-001', 'Organic Face Cream', 'Natural ingredients face moisturizer', 9, 24.99, 10.00, 250, 35, 0.15, false),
('AUTO-001', 'Car Phone Mount', 'Universal smartphone car mount', 10, 14.99, 6.00, 400, 50, 0.3, false);

-- Sample customers
INSERT INTO customers (email, first_name, last_name, phone, password_hash, is_verified, lifetime_value) VALUES
('john.doe@email.com', 'John', 'Doe', '+1234567890', '$2a$10$...', true, 2450.00),
('jane.smith@email.com', 'Jane', 'Smith', '+1234567891', '$2a$10$...', true, 5800.00),
('bob.wilson@email.com', 'Bob', 'Wilson', '+1234567892', '$2a$10$...', true, 1200.00),
('alice.brown@email.com', 'Alice', 'Brown', '+1234567893', '$2a$10$...', true, 15000.00),
('charlie.davis@email.com', 'Charlie', 'Davis', '+1234567894', '$2a$10$...', false, 0.00);

-- Mark VIP customers (>$10k lifetime value)
UPDATE customers SET is_vip = true WHERE lifetime_value > 10000;

-- Sample addresses
INSERT INTO addresses (customer_id, address_type, street_line1, city, state, postal_code, country, is_default) VALUES
(1, 'shipping', '123 Main St', 'New York', 'NY', '10001', 'US', true),
(1, 'billing', '123 Main St', 'New York', 'NY', '10001', 'US', true),
(2, 'shipping', '456 Oak Ave', 'Los Angeles', 'CA', '90001', 'US', true),
(3, 'shipping', '789 Pine Rd', 'Chicago', 'IL', '60601', 'US', true),
(4, 'shipping', '321 Elm St', 'Houston', 'TX', '77001', 'US', true),
(5, 'shipping', '654 Maple Dr', 'Phoenix', 'AZ', '85001', 'US', true);

-- Sample orders
INSERT INTO orders (order_number, customer_id, status, payment_method, payment_status, subtotal, tax, shipping, discount, total, shipping_address_id, billing_address_id, created_at) VALUES
('ORD-2024-001', 1, 'delivered', 'credit_card', 'captured', 89.99, 7.20, 9.99, 0.00, 107.18, 1, 2, '2024-10-01 10:30:00'),
('ORD-2024-002', 2, 'delivered', 'paypal', 'captured', 1299.99, 103.99, 0.00, 50.00, 1353.98, 3, 3, '2024-10-05 14:20:00'),
('ORD-2024-003', 3, 'shipped', 'credit_card', 'captured', 49.99, 4.00, 5.99, 0.00, 59.98, 4, 4, '2024-10-20 09:15:00'),
('ORD-2024-004', 4, 'processing', 'stripe', 'authorized', 999.99, 80.00, 0.00, 0.00, 1079.99, 5, 5, '2024-10-25 16:45:00'),
('ORD-2024-005', 1, 'pending', 'credit_card', 'pending', 69.98, 5.60, 9.99, 0.00, 85.57, 1, 2, '2024-10-27 11:00:00');

-- Sample order items
INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price, subtotal) VALUES
(1, 1, 'ELEC-001', 'Wireless Bluetooth Headphones', 1, 89.99, 89.99),
(2, 2, 'COMP-001', 'Gaming Laptop 15.6"', 1, 1299.99, 1299.99),
(3, 5, 'BOOK-001', 'The Art of Database Design', 1, 49.99, 49.99),
(4, 3, 'MOBI-001', 'Smartphone Pro Max', 1, 999.99, 999.99),
(5, 4, 'CLOT-001', 'Cotton T-Shirt', 2, 19.99, 39.98),
(5, 7, 'SPOR-001', 'Yoga Mat Premium', 1, 29.99, 29.99);

-- Sample shopping carts (abandoned)
INSERT INTO carts (customer_id, status, created_at, updated_at, abandoned_at) VALUES
(1, 'abandoned', '2024-10-26 10:00:00', '2024-10-26 10:15:00', '2024-10-26 12:15:00'),
(3, 'abandoned', '2024-10-26 14:00:00', '2024-10-26 14:30:00', '2024-10-26 16:30:00'),
(5, 'active', '2024-10-27 09:00:00', '2024-10-27 09:30:00', NULL);

-- Sample cart items
INSERT INTO cart_items (cart_id, product_id, quantity, added_at) VALUES
(1, 2, 1, '2024-10-26 10:00:00'),
(1, 1, 1, '2024-10-26 10:15:00'),
(2, 3, 1, '2024-10-26 14:00:00'),
(3, 4, 2, '2024-10-27 09:00:00');

-- Sample inventory logs
INSERT INTO inventory_logs (product_id, change_type, quantity_change, previous_stock, new_stock, reference_id, notes) VALUES
(1, 'sale', -1, 151, 150, 1, 'Order ORD-2024-001'),
(2, 'sale', -1, 26, 25, 2, 'Order ORD-2024-002'),
(2, 'restock', 25, 25, 50, NULL, 'Warehouse restock'),
(3, 'sale', -1, 101, 100, 4, 'Order ORD-2024-004');

-- Sample price history
INSERT INTO price_history (product_id, old_price, new_price, changed_at) VALUES
(2, 1399.99, 1299.99, '2024-10-01 00:00:00'),
(3, 1099.99, 999.99, '2024-10-15 00:00:00'),
(1, 99.99, 89.99, '2024-09-01 00:00:00');

-- Refresh materialized view
REFRESH MATERIALIZED VIEW product_sales_summary;

-- Analyze tables for better query planning
ANALYZE;
