#!/bin/bash

echo "🗄️  Initializing ElectroHub Database..."
echo ""

export DB_PASSWORD="password"

# Step 1: Create schema
echo "📋 Creating database schema..."
PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -U postgres -d electrohub -f 01_schema.sql
echo "✅ Schema created"
echo ""

# Step 2: Create indexes
echo "⚡ Creating performance indexes..."
PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -U postgres -d electrohub -f 02_indexes.sql
echo "✅ Indexes created"
echo ""

# Step 3: Generate synthetic data (uses venv python)
echo "🌱 Generating synthetic data..."
python 03_seed_data.py
echo "✅ Data generated"
echo ""

# Step 4: Verify
echo "📊 Database Summary:"
PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -U postgres -d electrohub -c "
SELECT 
    (SELECT COUNT(*) FROM user_accounts) as users,
    (SELECT COUNT(*) FROM marketplace_items) as items,
    (SELECT COUNT(*) FROM item_interactions) as interactions;
"

echo ""
echo "✅ Database initialization complete!"
