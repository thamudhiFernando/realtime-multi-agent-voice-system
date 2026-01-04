-- ============================================================================
-- ElectroMart Database Population Script
-- Run this in pgAdmin Query Tool to populate all tables with sample data
-- ============================================================================

-- Insert Customers
INSERT INTO customers (name, email, phone, created_at) VALUES
('John Doe', 'john.doe@email.com', '(555) 111-2222', NOW()),
('Jane Smith', 'jane.smith@email.com', '(555) 222-3333', NOW()),
('Bob Johnson', 'bob.johnson@email.com', '(555) 333-4444', NOW()),
('Alice Williams', 'alice.williams@email.com', '(555) 444-5555', NOW()),
('Charlie Brown', 'charlie.brown@email.com', '(555) 555-6666', NOW());

-- Insert Products
INSERT INTO products (name, category, price, stock_status, specs, description, created_at) VALUES
('iPhone 15 Pro', 'smartphones', 999.99, 'in_stock',
 '{"display": "6.1-inch Super Retina XDR", "processor": "A17 Pro chip", "camera": "48MP Main, 12MP Ultra Wide, 12MP Telephoto", "storage": "128GB, 256GB, 512GB, 1TB", "battery": "Up to 23 hours video playback", "colors": ["Natural Titanium", "Blue Titanium", "White Titanium", "Black Titanium"]}',
 'The most powerful iPhone ever with titanium design and Action button', NOW()),

('Samsung Galaxy S24 Ultra', 'smartphones', 1199.99, 'in_stock',
 '{"display": "6.8-inch Dynamic AMOLED 2X", "processor": "Snapdragon 8 Gen 3", "camera": "200MP Main, 12MP Ultra Wide, 50MP Telephoto (5x), 10MP Telephoto (3x)", "storage": "256GB, 512GB, 1TB", "battery": "5000mAh", "colors": ["Titanium Gray", "Titanium Black", "Titanium Violet", "Titanium Yellow"]}',
 'Ultimate flagship with S Pen and AI-powered features', NOW()),

('Google Pixel 8 Pro', 'smartphones', 899.99, 'in_stock',
 '{"display": "6.7-inch LTPO OLED", "processor": "Google Tensor G3", "camera": "50MP Main, 48MP Ultra Wide, 48MP Telephoto", "storage": "128GB, 256GB, 512GB", "battery": "5050mAh", "colors": ["Obsidian", "Porcelain", "Bay"]}',
 'Best Android camera phone with Google AI features', NOW()),

('MacBook Pro 16"', 'laptops', 2499.99, 'in_stock',
 '{"display": "16.2-inch Liquid Retina XDR", "processor": "M3 Max", "ram": "16GB, 32GB, 64GB, 128GB", "storage": "512GB, 1TB, 2TB, 4TB, 8TB", "battery": "Up to 22 hours", "colors": ["Space Black", "Silver"]}',
 'The ultimate pro laptop with M3 Max chip', NOW()),

('Dell XPS 15', 'laptops', 1799.99, 'in_stock',
 '{"display": "15.6-inch OLED 3.5K", "processor": "Intel Core i7-13700H", "ram": "16GB, 32GB, 64GB", "storage": "512GB, 1TB, 2TB SSD", "graphics": "NVIDIA GeForce RTX 4050", "battery": "Up to 13 hours"}',
 'Premium Windows laptop with stunning OLED display', NOW()),

('Sony WH-1000XM5', 'headphones', 399.99, 'in_stock',
 '{"type": "Over-ear", "noise_cancellation": "Industry-leading ANC", "battery": "Up to 30 hours", "connectivity": "Bluetooth 5.2, USB-C", "features": ["Multipoint connection", "Speak-to-Chat", "Adaptive Sound Control"]}',
 'Best noise-cancelling headphones with exceptional sound quality', NOW()),

('Apple AirPods Pro (2nd Gen)', 'headphones', 249.99, 'in_stock',
 '{"type": "In-ear", "noise_cancellation": "Active Noise Cancellation", "battery": "Up to 6 hours (30 hours with case)", "connectivity": "Bluetooth 5.3, USB-C", "features": ["Adaptive Audio", "Conversation Awareness", "Personalized Spatial Audio"]}',
 'Premium wireless earbuds with advanced features', NOW()),

('Samsung 65" QLED 4K TV', 'tvs', 1299.99, 'in_stock',
 '{"screen_size": "65 inches", "resolution": "4K QLED", "refresh_rate": "120Hz", "smart_features": "Tizen OS, Alexa, Google Assistant", "ports": ["4x HDMI 2.1", "3x USB", "Ethernet"]}',
 'Stunning QLED picture quality with gaming features', NOW()),

('LG 77" OLED C3', 'tvs', 2799.99, 'in_stock',
 '{"screen_size": "77 inches", "resolution": "4K OLED", "refresh_rate": "120Hz", "smart_features": "webOS, Alexa, Google Assistant, HomeKit", "features": ["Dolby Vision IQ", "Dolby Atmos", "NVIDIA G-Sync", "FreeSync"]}',
 'Premium OLED TV with perfect blacks and gaming features', NOW()),

('iPad Pro 12.9"', 'tablets', 1099.99, 'in_stock',
 '{"display": "12.9-inch Liquid Retina XDR", "processor": "M2 chip", "storage": "128GB, 256GB, 512GB, 1TB, 2TB", "connectivity": "Wi-Fi 6E, 5G (optional)", "features": ["Apple Pencil support", "Magic Keyboard support", "Face ID"]}',
 'The ultimate iPad experience with M2 chip', NOW());

-- Insert Promotions
INSERT INTO promotions (name, description, discount_percentage, promo_code, start_date, end_date, is_active, created_at) VALUES
('New Year Sale', 'Start the year with amazing deals on all electronics', 15, 'NEWYEAR2024', '2024-01-01', '2024-01-31', true, NOW()),
('Spring Electronics Fest', 'Spring into savings with up to 20% off on selected items', 20, 'SPRING20', '2024-03-01', '2024-03-31', true, NOW()),
('Back to School', 'Get ready for school with special discounts on laptops and tablets', 25, 'SCHOOL25', '2024-08-01', '2024-09-15', true, NOW());

-- Insert Orders (using customer and product IDs)
INSERT INTO orders (order_number, customer_id, product_id, status, tracking_number, order_date, delivery_date, total_amount, created_at) VALUES
('ORD001234', 1, 1, 'delivered', 'TRK001234XYZ', NOW() - INTERVAL '15 days', NOW() - INTERVAL '10 days', 999.99, NOW() - INTERVAL '15 days'),
('ORD001235', 2, 4, 'shipped', 'TRK001235XYZ', NOW() - INTERVAL '3 days', NOW() + INTERVAL '2 days', 2499.99, NOW() - INTERVAL '3 days'),
('ORD001236', 3, 6, 'processing', NULL, NOW() - INTERVAL '1 day', NULL, 399.99, NOW() - INTERVAL '1 day'),
('ORD001237', 4, 8, 'out_for_delivery', 'TRK001237XYZ', NOW() - INTERVAL '5 days', NOW(), 1299.99, NOW() - INTERVAL '5 days'),
('ORD001238', 5, 3, 'delivered', 'TRK001238XYZ', NOW() - INTERVAL '30 days', NOW() - INTERVAL '23 days', 899.99, NOW() - INTERVAL '30 days');

-- Insert Support Tickets
INSERT INTO support_tickets (ticket_number, customer_id, product_id, issue_type, description, status, priority, created_at, resolved_at) VALUES
('TKT12345678', 1, 4, 'technical', 'Laptop won''t boot up after Windows update', 'open', 'high', NOW() - INTERVAL '2 days', NULL),
('TKT12345679', 2, 1, 'warranty', 'Phone screen cracked, checking warranty coverage', 'in_progress', 'medium', NOW() - INTERVAL '5 days', NULL),
('TKT12345680', 3, 8, 'repair', 'TV has no picture, backlight issue suspected', 'resolved', 'medium', NOW() - INTERVAL '15 days', NOW() - INTERVAL '10 days'),
('TKT12345681', 4, 6, 'setup', 'Need help connecting headphones to multiple devices', 'resolved', 'low', NOW() - INTERVAL '20 days', NOW() - INTERVAL '18 days');

-- Verification Queries
SELECT 'Customers' as table_name, COUNT(*) as record_count FROM customers
UNION ALL
SELECT 'Products', COUNT(*) FROM products
UNION ALL
SELECT 'Promotions', COUNT(*) FROM promotions
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Support Tickets', COUNT(*) FROM support_tickets;

-- Show iPhone 15 Pro specifically
SELECT name, category, price, stock_status
FROM products
WHERE name = 'iPhone 15 Pro';
