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

POSTGRES_USER=${POSTGRES_USER:-postgres}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_DATABASE=${DB_DATABASE:-qtrvsim_web_eval}

echo "Creating database '$DB_DATABASE'..."
echo "Database host: $DB_HOST:$DB_PORT"
echo "Postgres user: $POSTGRES_USER"
echo "App user: $DB_USER"
echo ""

DB_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_DATABASE'" 2>/dev/null || echo "")

if [ "$DB_EXISTS" != "1" ]; then
	echo "Creating database..."
	PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<-EOSQL
		CREATE DATABASE $DB_DATABASE;
EOSQL
	echo "[OK] Database created"
else
	echo "Database already exists"
fi

TABLES_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)

if [ "$TABLES_COUNT" -eq "0" ]; then
	echo "Initializing database schema..."
	
	echo "Creating database user '$DB_USER'..."
	PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" <<-EOSQL
		DO \$\$
		BEGIN
			IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
				CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
			END IF;
		END
		\$\$;
		GRANT ALL PRIVILEGES ON DATABASE $DB_DATABASE TO $DB_USER;
		GRANT ALL PRIVILEGES ON SCHEMA public TO $DB_USER;
EOSQL
	
	SCHEMA_FILE="$PROJECT_ROOT/docker/webeval_schema.sql"
	if [ ! -f "$SCHEMA_FILE" ]; then
		echo "Error: Schema file not found at $SCHEMA_FILE"
		exit 1
	fi
	
	TMP_SCHEMA=$(mktemp)
	sed "s/qtrvsim/${DB_USER}/g" "$SCHEMA_FILE" > "$TMP_SCHEMA"
	
	echo "Importing schema..."
	PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" -f "$TMP_SCHEMA"
	
	if [ $? -eq 0 ]; then
		echo "[OK] Database schema initialized successfully"
		
		PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" <<-EOSQL
			GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
			GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
EOSQL
	else
		echo "[ERROR] Error initializing database schema"
		rm "$TMP_SCHEMA"
		exit 1
	fi
	
	rm "$TMP_SCHEMA"
else
	echo "Database schema already exists (found $TABLES_COUNT tables)"
fi

echo ""
echo "[OK] Database setup complete"