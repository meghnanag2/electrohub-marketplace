#!/bin/bash
echo "🚀 ElectroHub Setup"
docker-compose down -v 2>/dev/null
docker-compose build --no-cache
docker-compose up -d
sleep 60
echo "✅ Done! http://localhost:3000"
