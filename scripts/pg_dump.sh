#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/.env" ]; then
	export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
else
	echo "Error: .env file not found at $PROJECT_ROOT/.env"
	exit 1
fi

DB_USER=${DB_USER:-qtrvsim}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_DATABASE=${DB_DATABASE:-qtrvsim_web_eval}

SCHEMA_ONLY=false
OUTPUT_FILE=""

for arg in "$@"; do
	case $arg in
		--schema-only)
			SCHEMA_ONLY=true
			shift
			;;
		*)
			OUTPUT_FILE="$arg"
			shift
			;;
	esac
done

if [ -z "$OUTPUT_FILE" ]; then
	if [ "$SCHEMA_ONLY" = true ]; then
		OUTPUT_FILE="${DB_DATABASE}_schema_$(date +%Y%m%d_%H%M%S).sql"
	else
		OUTPUT_FILE="${DB_DATABASE}_$(date +%Y%m%d_%H%M%S).sql"
	fi
fi

if [ "$SCHEMA_ONLY" = true ]; then
	echo "Dumping database schema only..."
	DUMP_OPTIONS="--schema-only"
else
	echo "Dumping database with data..."
	DUMP_OPTIONS=""
fi

echo "Database: $DB_DATABASE"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo "Output: $OUTPUT_FILE"
echo ""

PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_DATABASE" $DUMP_OPTIONS -f "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
	echo "[OK] Database dumped to: $OUTPUT_FILE"
else
	echo "[ERROR] Error dumping database"
	exit 1
fi