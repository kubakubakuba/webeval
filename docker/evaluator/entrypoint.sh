#!/bin/bash
set -e

echo "[EVALUATOR] TASKS_DIR=${TASKS_DIR}"

echo "[EVALUATOR] Waiting for database to be ready..."
RETRY_COUNT=0
until python3 -c "import psycopg2; psycopg2.connect(host='$DB_HOST', port='$DB_PORT', user='$DB_USER', password='$DB_PASSWORD', database='$DB_DATABASE', connect_timeout=5).close()" 2>&1; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "[EVALUATOR] Database connection attempt $RETRY_COUNT failed, retrying in 2 seconds..."
  sleep 2
  
  if [ $RETRY_COUNT -ge 30 ]; then
    echo "[EVALUATOR] ERROR: Could not connect to database after 30 attempts"
    exit 1
  fi
done
echo "[EVALUATOR] Database is ready!"

cd /app

echo "[EVALUATOR] Creating .env file..."
# Create .env file with environment variables
cat > .env <<EOF
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_DATABASE=$DB_DATABASE
TASKS_DIR=$TASKS_DIR
EOF

sed -i "s/'sslmode': 'require'/'sslmode': 'disable'/g" /app/evaldb.py

echo "[EVALUATOR] Starting evaluator service..."
exec python3 evaluator.py
