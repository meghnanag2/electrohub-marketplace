#!/bin/bash

echo "==============================================="
echo "🌱 ElectroHub Data Generation Script"
echo "==============================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python3."
    exit 1
fi

echo "✅ Python3 found"

echo "📦 Installing Python dependencies..."
pip3 install bcrypt psycopg2-binary --quiet 2>/dev/null || pip install bcrypt psycopg2-binary --quiet

echo "✅ Dependencies installed"

echo ""
echo "🐳 Checking Docker..."
docker ps > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Docker not running"
    exit 1
fi

echo "✅ Docker is running"

echo ""
echo "🔍 Checking database connection..."
PGPASSWORD=password docker exec electrohub-postgres psql -U postgres -d electrohub -c "SELECT 1" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Database not ready. Start containers first:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "✅ Database is ready"

echo ""
echo "🚀 Starting data generation..."
echo "   This may take 1-2 minutes..."
echo ""

export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=password
export DB_NAME=electrohub

python3 generate_large_dataset.py

if [ $? -eq 0 ]; then
    echo ""
    echo "==============================================="
    echo "🎉 SUCCESS! Data generation complete!"
    echo "==============================================="
    echo ""
else
    echo "❌ Data generation failed"
    exit 1
fi
