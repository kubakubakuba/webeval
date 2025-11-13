#!/bin/bash
set -e

echo "Waiting for database to be ready..."
until PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_DATABASE" -c '\q' 2>/dev/null; do
  sleep 1
done
echo "Database is ready!"

cd /app

# Create .env file with environment variables
cat > .env <<EOF
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_DATABASE=$DB_DATABASE
TASKS_DIR=$TASKS_DIR
EOF

# Disable SSL mode for internal docker communication
sed -i "s/'sslmode': 'require'/'sslmode': 'disable'/g" /app/evaldb.py

echo "Starting evaluator..."
exec python3 evaluator.py
