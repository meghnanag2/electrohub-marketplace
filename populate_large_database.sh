#!/bin/bash

set -e

echo "==============================================="
echo "🌱 ElectroHub LARGE Database Population"
echo "==============================================="
echo ""

# Check Docker running
echo "🐳 Checking Docker..."
docker ps > /dev/null 2>&1 || { echo "❌ Docker not running"; exit 1; }
echo "✅ Docker running"

# Check database
echo "🔍 Checking database..."
docker exec electrohub-postgres psql -U postgres -d electrohub -c "SELECT 1" > /dev/null 2>&1 || { echo "❌ Database not ready"; exit 1; }
echo "✅ Database ready"

# Clear old data
echo ""
echo "🧹 Clearing old data..."
docker exec electrohub-postgres psql -U postgres -d electrohub << 'CLEANSQL'
TRUNCATE TABLE item_interactions CASCADE;
TRUNCATE TABLE item_saved CASCADE;
TRUNCATE TABLE item_images CASCADE;
TRUNCATE TABLE marketplace_messages CASCADE;
TRUNCATE TABLE marketplace_items CASCADE;
TRUNCATE TABLE user_accounts CASCADE;
CLEANSQL
echo "✅ Old data cleared"

# Insert demo users
echo ""
echo "📝 Creating 5 demo users..."
docker exec electrohub-postgres psql -U postgres -d electrohub << 'DEMOUSERSQL'
INSERT INTO user_accounts (user_id, email, password_hash, name, phone, city, state, is_active) VALUES 
('user_demo_001', 'demo@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'Demo User', '555-0001', 'Denver', 'CO', true),
('user_demo_002', 'seller@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'John Seller', '555-0002', 'Boulder', 'CO', true),
('user_demo_003', 'buyer@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'Sarah Buyer', '555-0003', 'Aurora', 'CO', true),
('user_demo_004', 'alice@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'Alice Johnson', '555-0004', 'Fort Collins', 'CO', true),
('user_demo_005', 'bob@electrohub.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW', 'Bob Smith', '555-0005', 'Lakewood', 'CO', true);
DEMOUSERSQL
echo "✅ 5 demo users created"

# Generate 250+ regular users
echo ""
echo "👥 Creating 250+ regular users..."
docker exec electrohub-postgres psql -U postgres -d electrohub << 'USERSQL'
INSERT INTO user_accounts (user_id, email, password_hash, name, phone, city, state, is_active) 
SELECT 
  'user_' || LPAD(n::text, 6, '0'),
  'user' || n || '@example.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUKqMKuW',
  (ARRAY['John', 'Sarah', 'Mike', 'Emma', 'David', 'Lisa', 'James', 'Jennifer', 'Robert', 'Mary'])[((n-1) % 10) + 1] || ' ' ||
  (ARRAY['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez'])[((n-1) % 10) + 1],
  '555-' || LPAD((1000 + n)::text, 4, '0'),
  (ARRAY['Denver', 'Boulder', 'Aurora', 'Fort Collins', 'Lakewood', 'Littleton', 'Thornton', 'Broomfield', 'Westminster', 'Arvada'])[((n-1) % 10) + 1],
  'CO',
  true
FROM generate_series(1, 250) as t(n);
USERSQL
echo "✅ 250+ users created"

# Generate 1000+ products
echo ""
echo "🛍️  Creating 1000+ products..."
docker exec electrohub-postgres psql -U postgres -d electrohub << 'PRODUCTSQL'
INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, is_active, views_count, saves_count)
SELECT
  CASE WHEN (n % 5) = 0 THEN 'user_demo_001'
       WHEN (n % 5) = 1 THEN 'user_demo_002'
       WHEN (n % 5) = 2 THEN 'user_demo_003'
       WHEN (n % 5) = 3 THEN 'user_demo_004'
       ELSE 'user_demo_005' END,
  (ARRAY['iPhone', 'Samsung', 'Google Pixel', 'OnePlus', 'Motorola'])[((n-1) % 5) + 1] || ' ' ||
  (ARRAY['14 Pro', '13', '12', '11', 'Pro Max'])[((n-1) % 5) + 1] || ' ' ||
  (ARRAY['- Like New', '- Excellent', '- Good', '- Very Good', '- Brand New'])[((n-1) % 5) + 1],
  'Smartphone in ' || (ARRAY['pristine', 'excellent', 'great', 'good', 'very good'])[((n-1) % 5) + 1] || ' condition. ' ||
  (ARRAY['Full warranty', 'Includes box', 'All accessories', 'Screen protector', 'Case included'])[((n-1) % 5) + 1],
  'Smartphone',
  (100.00 + random() * 800.00)::numeric(10,2),
  (ARRAY['Denver', 'Boulder', 'Aurora', 'Fort Collins', 'Lakewood', 'Littleton', 'Thornton', 'Broomfield', 'Westminster', 'Arvada'])[((n-1) % 10) + 1],
  'CO',
  true,
  (random() * 500)::int,
  (random() * 100)::int
FROM generate_series(1, 300) as t(n);

INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, is_active, views_count, saves_count)
SELECT
  CASE WHEN (n % 5) = 0 THEN 'user_demo_001'
       WHEN (n % 5) = 1 THEN 'user_demo_002'
       WHEN (n % 5) = 2 THEN 'user_demo_003'
       WHEN (n % 5) = 3 THEN 'user_demo_004'
       ELSE 'user_demo_005' END,
  (ARRAY['MacBook', 'Dell XPS', 'HP Spectre', 'Lenovo ThinkPad', 'Asus ROG'])[((n-1) % 5) + 1] || ' ' ||
  (ARRAY['Pro 16', 'Air M2', 'x360', 'X1 Carbon', 'Strix'])[((n-1) % 5) + 1] || ' ' ||
  (ARRAY['- Pristine', '- Excellent', '- Good', '- Very Good', '- Like New'])[((n-1) % 5) + 1],
  'High-performance laptop with ' || (ARRAY['16GB', '32GB', '64GB'])[((n-1) % 3) + 1] || ' RAM. ' ||
  (ARRAY['Perfect for work', 'Great for gaming', 'Perfect for development', 'Excellent for editing', 'Great for streaming'])[((n-1) % 5) + 1],
  'Laptop',
  (800.00 + random() * 2000.00)::numeric(10,2),
  (ARRAY['Denver', 'Boulder', 'Aurora', 'Fort Collins', 'Lakewood', 'Littleton', 'Thornton', 'Broomfield', 'Westminster', 'Arvada'])[((n-1) % 10) + 1],
  'CO',
  true,
  (random() * 800)::int,
  (random() * 150)::int
FROM generate_series(1, 250) as t(n);

INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, is_active, views_count, saves_count)
SELECT
  CASE WHEN (n % 5) = 0 THEN 'user_demo_001'
       WHEN (n % 5) = 1 THEN 'user_demo_002'
       WHEN (n % 5) = 2 THEN 'user_demo_003'
       WHEN (n % 5) = 3 THEN 'user_demo_004'
       ELSE 'user_demo_005' END,
  (ARRAY['Bose QC45', 'Sony WH-1000XM5', 'AirPods Pro', 'Beats Studio', 'JBL Charge'])[((n-1) % 5) + 1] || ' ' ||
  (ARRAY['- Like New', '- Excellent', '- Good', '- Very Good', '- Pristine'])[((n-1) % 5) + 1],
  'High-quality audio equipment. ' || (ARRAY['Noise-canceling', 'Water-resistant', 'Long battery life', 'Bluetooth 5.0', 'Premium sound'])[((n-1) % 5) + 1],
  'Headphones',
  (50.00 + random() * 400.00)::numeric(10,2),
  (ARRAY['Denver', 'Boulder', 'Aurora', 'Fort Collins', 'Lakewood', 'Littleton', 'Thornton', 'Broomfield', 'Westminster', 'Arvada'])[((n-1) % 10) + 1],
  'CO',
  true,
  (random() * 600)::int,
  (random() * 120)::int
FROM generate_series(1, 200) as t(n);

INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, is_active, views_count, saves_count)
SELECT
  CASE WHEN (n % 5) = 0 THEN 'user_demo_001'
       WHEN (n % 5) = 1 THEN 'user_demo_002'
       WHEN (n % 5) = 2 THEN 'user_demo_003'
       WHEN (n % 5) = 3 THEN 'user_demo_004'
       ELSE 'user_demo_005' END,
  (ARRAY['iPad Pro', 'Samsung Tab S9', 'Microsoft Surface', 'Amazon Fire HD', 'Lenovo Tab'])[((n-1) % 5) + 1] || ' ' ||
  (ARRAY['11"', '12.9"', '13"', '8"', '10"'])[((n-1) % 5) + 1],
  'Tablet with ' || (ARRAY['64GB', '128GB', '256GB', '512GB', '1TB'])[((n-1) % 5) + 1] || ' storage. ' ||
  (ARRAY['Perfect for media', 'Great for work', 'Excellent display', 'High performance', 'Perfect for students'])[((n-1) % 5) + 1],
  'Tablet',
  (200.00 + random() * 1000.00)::numeric(10,2),
  (ARRAY['Denver', 'Boulder', 'Aurora', 'Fort Collins', 'Lakewood', 'Littleton', 'Thornton', 'Broomfield', 'Westminster', 'Arvada'])[((n-1) % 10) + 1],
  'CO',
  true,
  (random() * 400)::int,
  (random() * 80)::int
FROM generate_series(1, 150) as t(n);

INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, is_active, views_count, saves_count)
SELECT
  CASE WHEN (n % 5) = 0 THEN 'user_demo_001'
       WHEN (n % 5) = 1 THEN 'user_demo_002'
       WHEN (n % 5) = 2 THEN 'user_demo_003'
       WHEN (n % 5) = 3 THEN 'user_demo_004'
       ELSE 'user_demo_005' END,
  (ARRAY['Apple Watch', 'Samsung Galaxy Watch', 'Fitbit Versa', 'Garmin Fenix', 'Fossil Gen'])[((n-1) % 5) + 1] || ' ' ||
  (ARRAY['Series 8', 'Series 5', '5', '7', '6'])[((n-1) % 5) + 1],
  'Smartwatch with ' || (ARRAY['fitness tracking', 'health monitoring', 'GPS', 'water resistance', 'long battery life'])[((n-1) % 5) + 1],
  'Smartwatch',
  (150.00 + random() * 500.00)::numeric(10,2),
  (ARRAY['Denver', 'Boulder', 'Aurora', 'Fort Collins', 'Lakewood', 'Littleton', 'Thornton', 'Broomfield', 'Westminster', 'Arvada'])[((n-1) % 10) + 1],
  'CO',
  true,
  (random() * 300)::int,
  (random() * 60)::int
FROM generate_series(1, 100) as t(n);
PRODUCTSQL
echo "✅ 1000+ products created"

# Generate messages
echo ""
echo "💬 Creating 500+ messages..."
docker exec electrohub-postgres psql -U postgres -d electrohub << 'MESSAGESQL'
INSERT INTO marketplace_messages (sender_id, receiver_id, item_id, message_text, is_read)
SELECT
  'user_' || LPAD((1 + (n-1) % 250)::text, 6, '0'),
  'user_' || LPAD((2 + (n-1) % 248)::text, 6, '0'),
  1 + (n-1) % (SELECT COUNT(*) FROM marketplace_items),
  (ARRAY[
    'Is this still available?',
    'What''s the lowest price?',
    'Can you ship this?',
    'Interested! When can we meet?',
    'Does it work perfectly?',
    'Any scratches or damage?',
    'Can I see more photos?',
    'What''s the warranty?',
    'Is this price negotiable?',
    'I''ll take it! How do we proceed?'
  ])[((n-1) % 10) + 1],
  CASE WHEN random() > 0.3 THEN true ELSE false END
FROM generate_series(1, 500) as t(n);
MESSAGESQL
echo "✅ 500+ messages created"

# Generate saved items
echo ""
echo "⭐ Creating 2000+ saved items..."
docker exec electrohub-postgres psql -U postgres -d electrohub << 'SAVEDSQL'
INSERT INTO item_saved (user_id, item_id)
SELECT
  'user_' || LPAD((1 + (n-1) % 250)::text, 6, '0'),
  1 + (n-1) % (SELECT COUNT(*) FROM marketplace_items)
FROM generate_series(1, 2000) as t(n);
SAVEDSQL
echo "✅ 2000+ saved items created"

# Generate interactions (views, saves, messages)
echo ""
echo "👀 Creating 10000+ interactions..."
docker exec electrohub-postgres psql -U postgres -d electrohub << 'INTERACTIONSQL'
INSERT INTO item_interactions (user_id, item_id, event_type)
SELECT
  'user_' || LPAD((1 + (n-1) % 250)::text, 6, '0'),
  1 + (n-1) % (SELECT COUNT(*) FROM marketplace_items),
  CASE 
    WHEN random() < 0.7 THEN 'view'
    WHEN random() < 0.9 THEN 'save'
    ELSE 'message'
  END
FROM generate_series(1, 10000) as t(n);
INTERACTIONSQL
echo "✅ 10000+ interactions created"

# Verify
echo ""
echo "="*60
echo "📊 Verifying data..."
echo "="*60
docker exec electrohub-postgres psql -U postgres -d electrohub << 'VERIFYSQL'
SELECT 
  (SELECT COUNT(*) FROM user_accounts) as "👥 Users",
  (SELECT COUNT(*) FROM marketplace_items) as "🛍️  Products",
  (SELECT COUNT(*) FROM marketplace_messages) as "💬 Messages",
  (SELECT COUNT(*) FROM item_interactions) as "👀 Interactions",
  (SELECT COUNT(*) FROM item_saved) as "⭐ Saved Items";
VERIFYSQL

echo ""
echo "="*60
echo "✅ LARGE DATABASE POPULATION COMPLETE!"
echo "="*60
echo ""
echo "🔑 Demo Login:"
echo "   demo@electrohub.com / password123"
echo ""
echo "🌐 Access: http://localhost:3000"
echo ""
echo "📊 Database includes:"
echo "   • 250+ users with real passwords"
echo "   • 1000+ products across multiple categories"
echo "   • 500+ messages between users"
echo "   • 2000+ saved items (wishlists)"
echo "   • 10000+ user interactions"
echo ""
