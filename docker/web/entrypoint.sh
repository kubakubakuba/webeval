#!/bin/bash
set -e

echo "Waiting for database to be ready..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER"; do
  sleep 1
done
echo "Database is ready!"

# Check if database schema is initialized
TABLES_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")

if [ "$TABLES_COUNT" -eq "0" ]; then
	echo "Initializing database schema..."
	
	# Create database user if it doesn't exist
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
		GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
		GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
EOSQL
	
	# Replace username in schema file
	sed "s/qtrvsim/${DB_USER}/g" /docker-init/schema.sql > /tmp/schema.sql
	
	# Import schema
	PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" -f /tmp/schema.sql
	
	if [ $? -eq 0 ]; then
		echo "✓ Database schema initialized successfully"
		
		# Check if initial data file is provided and exists
		if [ -n "$DB_INITIAL_DATA_MOUNTED" ] && [ -f "$DB_INITIAL_DATA_MOUNTED" ]; then
			echo "Loading initial data from SQL dump..."
			PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" -f "$DB_INITIAL_DATA_MOUNTED"
			
			if [ $? -eq 0 ]; then
				echo "✓ Initial data loaded successfully"
				
				# Grant privileges on all tables and sequences to DB_USER after loading data
				echo "Granting privileges to '$DB_USER'..."
				PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" <<-EOSQL
					GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
					GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
EOSQL
			else
				echo "⚠ Warning: Error loading initial data (continuing anyway)"
			fi
		else
			# Load sample data for testing/development
			echo "Loading sample data (admin/admin, test1-3/test)..."
			PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" -f /docker-init/sample_data.sql
			
			if [ $? -eq 0 ]; then
				echo "✓ Sample data loaded successfully"
				
				# Grant privileges after loading sample data
				PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_DATABASE" <<-EOSQL
					GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
					GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
EOSQL
			else
				echo "⚠ Warning: Error loading sample data"
			fi
		fi
	else
		echo "✗ Error initializing database schema"
		exit 1
	fi
	
	rm /tmp/schema.sql
else
	echo "Database schema already exists (found $TABLES_COUNT tables)"
fi

# Create .env file with environment variables
cat > /app/.env <<EOF
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_DATABASE=$DB_DATABASE
SECRET_KEY=$SECRET_KEY
MAIL_SERVER=$MAIL_SERVER
MAIL_PORT=$MAIL_PORT
MAIL_USE_TLS=$MAIL_USE_TLS
MAIL_USE_SSL=$MAIL_USE_SSL
MAIL_USERNAME=$MAIL_USERNAME
MAIL_PASSWORD=$MAIL_PASSWORD
MAIL_DEFAULT_SENDER=$MAIL_DEFAULT_SENDER
BASE_URL=$BASE_URL
TEMPLATES_DIR=$TEMPLATES_DIR
TASKS_DIR=$TASKS_DIR
EOF

# Disable SSL mode for internal docker communication
sed -i "s/'sslmode': 'require'/'sslmode': 'disable'/g" /app/db.py

echo "Starting web server..."
exec gunicorn -w 3 -b 0.0.0.0:8000 app:app
