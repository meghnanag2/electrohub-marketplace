#!/bin/bash

echo "🌱 Loading demo data..."

docker exec electrohub-postgres psql -U postgres -d electrohub << 'SQLEOF'

-- Users
INSERT INTO user_accounts (user_id, email, password_hash, name, phone, city, state, is_active) VALUES 
('user_demo_001', 'demo@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'Demo User', '555-0001', 'Denver', 'CO', true),
('user_demo_002', 'seller@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'John Seller', '555-0002', 'Boulder', 'CO', true),
('user_demo_003', 'buyer@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'Sarah Buyer', '555-0003', 'Aurora', 'CO', true),
('user_demo_004', 'alice@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'Alice Johnson', '555-0004', 'Fort Collins', 'CO', true),
('user_demo_005', 'bob@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'Bob Smith', '555-0005', 'Lakewood', 'CO', true);

-- Products
INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, is_active) VALUES
('user_demo_002', 'Apple iPhone 14 Pro', 'Excellent condition, 256GB', 'Smartphone', 899.99, 'Boulder', 'CO', true),
('user_demo_002', 'Dell XPS 13 Laptop', 'Intel i7, 16GB RAM, 512GB SSD', 'Laptop', 1299.99, 'Boulder', 'CO', true),
('user_demo_002', 'Sony WH-1000XM4', 'Noise-canceling headphones', 'Headphones', 299.99, 'Boulder', 'CO', true),
('user_demo_002', 'iPad Air 5th Gen', '64GB, WiFi only', 'Tablet', 549.99, 'Boulder', 'CO', true),
('user_demo_002', 'Samsung Galaxy Watch 5', 'Pristine condition', 'Smartwatch', 249.99, 'Boulder', 'CO', true),
('user_demo_001', 'MacBook Pro 16" M2 Max', '32GB RAM, 1TB SSD', 'Laptop', 2499.99, 'Denver', 'CO', true),
('user_demo_001', 'Canon EOS R5 Camera', 'Professional mirrorless', 'Camera', 3299.99, 'Denver', 'CO', true),
('user_demo_001', 'DJI Mini 3 Pro Drone', 'Like new, complete', 'Drone', 449.99, 'Denver', 'CO', true),
('user_demo_001', 'Nintendo Switch OLED', 'With games and accessories', 'Gaming', 349.99, 'Denver', 'CO', true),
('user_demo_001', 'Bose QuietComfort 45', 'Excellent audio quality', 'Headphones', 379.99, 'Denver', 'CO', true),
('user_demo_004', 'AirPods Pro', 'Like new, barely used', 'Audio', 149.99, 'Fort Collins', 'CO', true),
('user_demo_004', 'Apple Watch Series 8', 'Stainless steel', 'Smartwatch', 349.99, 'Fort Collins', 'CO', true),
('user_demo_004', 'GoPro Hero 11', 'Action camera', 'Camera', 399.99, 'Fort Collins', 'CO', true),
('user_demo_005', 'Google Pixel 7 Pro', 'Great phone', 'Smartphone', 599.99, 'Lakewood', 'CO', true),
('user_demo_005', 'Meta Quest 3', 'VR headset, excellent condition', 'Gaming', 499.99, 'Lakewood', 'CO', true);

-- Messages
INSERT INTO marketplace_messages (sender_id, receiver_id, item_id, message_text, is_read) VALUES
('user_demo_003', 'user_demo_002', 1, 'Is this still available?', false),
('user_demo_004', 'user_demo_002', 2, 'Does laptop have any issues?', false),
('user_demo_005', 'user_demo_001', 6, 'Is your MacBook available?', true),
('user_demo_001', 'user_demo_003', 1, 'Yes, still available!', true);

-- Saved Items
INSERT INTO item_saved (user_id, item_id) VALUES
('user_demo_003', 1),
('user_demo_003', 2),
('user_demo_003', 6),
('user_demo_004', 4),
('user_demo_004', 7),
('user_demo_005', 8),
('user_demo_005', 9),
('user_demo_001', 11);

-- Interactions
INSERT INTO item_interactions (user_id, item_id, event_type) VALUES
('user_demo_003', 1, 'view'),
('user_demo_003', 2, 'view'),
('user_demo_004', 6, 'view'),
('user_demo_005', 8, 'view'),
('user_demo_005', 8, 'save'),
('user_demo_001', 11, 'view'),
('user_demo_001', 11, 'save');

SQLEOF

echo "✅ Data inserted!"
echo ""

docker exec electrohub-postgres psql -U postgres -d electrohub -c "
SELECT 
  (SELECT COUNT(*) FROM user_accounts) as users,
  (SELECT COUNT(*) FROM marketplace_items) as products,
  (SELECT COUNT(*) FROM marketplace_messages) as messages,
  (SELECT COUNT(*) FROM item_interactions) as interactions,
  (SELECT COUNT(*) FROM item_saved) as saved;
"

echo ""
echo "🎉 Done!"
echo "🔑 Login: demo@electrohub.com / password123"
echo "🌐 http://localhost:3000"
