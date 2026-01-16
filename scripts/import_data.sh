#!/usr/bin/env bash

set -e

if [ $# -lt 1 ]; then
	echo "Usage: $0 <sql-file>"
	echo ""
	echo "Examples:"
	echo "  $0 docker/webeval_sample_data.sql"
	echo "  $0 /path/to/backup.sql"
	exit 1
fi

SQL_FILE="$1"

if [ ! -f "$SQL_FILE" ]; then
	echo "Error: SQL file not found: $SQL_FILE"
	exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/.env" ]; then
	export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
else
	echo "Error: .env file not found at $PROJECT_ROOT/.env"
	exit 1
fi

POSTGRES_USER=${POSTGRES_USER:-postgres}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_DATABASE=${DB_DATABASE:-qtrvsim_web_eval}

echo "Importing data into database '$DB_DATABASE'..."
echo "Database host: $DB_HOST:$DB_PORT"
echo "SQL file: $SQL_FILE"
echo ""

PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" -f "$SQL_FILE"

if [ $? -eq 0 ]; then
	echo ""
	echo "[OK] Data imported successfully"
	
	echo "Granting privileges to '$DB_USER'..."
	PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" <<-EOSQL
		GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
		GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
EOSQL
	echo "[OK] Privileges granted"
else
	echo "[ERROR] Error importing data"
	exit 1
fi
