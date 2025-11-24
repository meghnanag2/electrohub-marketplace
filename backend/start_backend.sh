#!/bin/bash
export DB_HOST="127.0.0.1"
export DB_NAME="electrohub"
export DB_USER="postgres"
export DB_PASSWORD="password"
export DB_PORT="5432"

cd "$(dirname "$0")"
pip install -r requirements.txt --user
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
