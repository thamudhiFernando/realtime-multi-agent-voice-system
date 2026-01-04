-- ElectroMart Demo Queries for pgAdmin
-- Copy and run these queries in pgAdmin during your demo

-- ============================================================================
-- 1. CHECK CONVERSATIONS TABLE (Shows chat history - READ/WRITE operations)
-- ============================================================================

-- View all conversations
SELECT
    session_id,
    current_agent,
    created_at,
    updated_at,
    jsonb_array_length(messages) as message_count
FROM conversations
ORDER BY updated_at DESC;

-- View latest conversation with messages
SELECT
    session_id,
    current_agent,
    messages,
    created_at,
    updated_at
FROM conversations
ORDER BY updated_at DESC
LIMIT 1;

SELECT
    session_id,
    messages,
    created_at,
    updated_at
FROM conversations
ORDER BY updated_at DESC
LIMIT 1;

-- Count total conversations
SELECT COUNT(*) as total_conversations FROM conversations;

-- ============================================================================
-- 2. CHECK PRODUCTS TABLE (Shows product queries - READ operations)
-- ============================================================================

-- View all products
SELECT
    id,
    name,
    category,
    price,
    stock_status,
    specs
FROM products
ORDER BY id;

-- Search products by category (like the agent does)
SELECT
    name,
    category,
    price,
    stock_status
FROM products
WHERE category = 'smartphones'
ORDER BY price DESC;

-- Count products by category
SELECT
    category,
    COUNT(*) as product_count,
    AVG(price) as avg_price
FROM products
GROUP BY category
ORDER BY product_count DESC;

-- ============================================================================
-- 3. CHECK ORDERS TABLE (Shows order queries - READ operations)
-- ============================================================================

-- View recent orders with customer and product details (JOIN operation)
SELECT
    o.order_number,
    c.name as customer_name,
    c.email as customer_email,
    p.name as product_name,
    o.status,
    o.total_amount,
    o.tracking_number,
    o.order_date
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
ORDER BY o.order_date DESC
LIMIT 10;

-- Orders by status
SELECT
    status,
    COUNT(*) as count,
    SUM(total_amount) as total_value
FROM orders
GROUP BY status;

-- ============================================================================
-- 4. CHECK CUSTOMERS TABLE
-- ============================================================================

-- View all customers
SELECT
    id,
    name,
    email,
    phone,
    created_at
FROM customers
ORDER BY created_at DESC;

-- Customer with their order count
SELECT
    c.name,
    c.email,
    COUNT(o.id) as total_orders,
    SUM(o.total_amount) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name, c.email
ORDER BY total_orders DESC;

-- ============================================================================
-- 5. CHECK SUPPORT TICKETS TABLE
-- ============================================================================

-- View active support tickets
SELECT
    ticket_number,
    c.name as customer_name,
    issue_type,
    status,
    priority,
    description,
    created_at
FROM support_tickets st
JOIN customers c ON st.customer_id = c.id
WHERE status IN ('open', 'in_progress')
ORDER BY priority DESC, created_at DESC;

-- Tickets by status
SELECT
    status,
    COUNT(*) as count
FROM support_tickets
GROUP BY status;

-- ============================================================================
-- 6. CHECK PROMOTIONS TABLE
-- ============================================================================

-- View active promotions
SELECT
    name,
    description,
    discount_percentage,
    promo_code,
    start_date,
    end_date,
    is_active
FROM promotions
WHERE is_active = true
AND start_date <= CURRENT_TIMESTAMP
AND end_date >= CURRENT_TIMESTAMP
ORDER BY discount_percentage DESC;

-- ============================================================================
-- 7. REAL-TIME MONITORING QUERIES (Run these during demo)
-- ============================================================================

-- Latest conversation activity (refresh to see new messages)
SELECT
    session_id,
    current_agent,
    jsonb_array_length(messages) as msg_count,
    updated_at,
    AGE(NOW(), updated_at) as last_activity
FROM conversations
ORDER BY updated_at DESC
LIMIT 5;

-- Database activity summary
SELECT
    'Conversations' as table_name,
    COUNT(*) as record_count,
    MAX(updated_at) as last_update
FROM conversations
UNION ALL
SELECT
    'Orders',
    COUNT(*),
    MAX(order_date)
FROM orders
UNION ALL
SELECT
    'Customers',
    COUNT(*),
    MAX(created_at)
FROM customers
UNION ALL
SELECT
    'Products',
    COUNT(*),
    MAX(created_at)
FROM products
UNION ALL
SELECT
    'Support Tickets',
    COUNT(*),
    MAX(created_at)
FROM support_tickets;

-- ============================================================================
-- 8. SPECIFIC MESSAGE LOOKUP (for detailed inspection)
-- ============================================================================

-- View messages from a specific conversation
-- Replace 'SESSION_ID_HERE' with actual session_id
SELECT
    jsonb_pretty(messages) as formatted_messages
FROM conversations
WHERE session_id = 'SESSION_ID_HERE';

-- Extract individual messages
SELECT
    session_id,
    jsonb_array_elements(messages) as individual_message
FROM conversations
WHERE session_id = 'SESSION_ID_HERE';
