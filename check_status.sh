#!/bin/bash
docker-compose ps
docker exec electrohub-postgres psql -U postgres -d electrohub -c "SELECT COUNT(*) FROM user_accounts;" 2>/dev/null
