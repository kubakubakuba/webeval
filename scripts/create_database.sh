#!/bin/sh

DB_USER="${DB_USER:-defaultuser}"
DB_NAME="${DB_NAME:-qtrvsim_web_eval}"
DB_PASSWORD="${DB_PASSWORD:-defaultpassword}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

DOTENV_FILE=".env"

ORIGINAL_DATABASE_SQL_FILE="qtrvsim_web_eval.sql"
MODIFIED_DATABASE_SQL_FILE="database.sql"

if [ ! -f "$ORIGINAL_DATABASE_SQL_FILE" ]; then
    echo "$ORIGINAL_DATABASE_SQL_FILE does not exist."
    exit 1
fi

sed "s/qtrvsim/$DB_USER/g" "$ORIGINAL_DATABASE_SQL_FILE" > "$MODIFIED_DATABASE_SQL_FILE"

echo "Creating user $DB_USER..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

echo "Creating database $DB_NAME..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "Applying database schema from $MODIFIED_DATABASE_SQL_FILE..."
sudo -u postgres psql -d $DB_NAME -a -f "$MODIFIED_DATABASE_SQL_FILE"

echo "Database and user setup complete."

rm "$MODIFIED_DATABASE_SQL_FILE"

#export this info in the .env file

#remove the DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, and DB_PORT if they exist
sed -i '/DB_USER/d' "$DOTENV_FILE"
sed -i '/DB_PASSWORD/d' "$DOTENV_FILE"
sed -i '/DB_DATABASE/d' "$DOTENV_FILE"
sed -i '/DB_HOST/d' "$DOTENV_FILE"
sed -i '/DB_PORT/d' "$DOTENV_FILE"

# append the new values to the .env file
{
    echo "DB_USER=$DB_USER"
    echo "DB_PASSWORD=$DB_PASSWORD"
    echo "DB_HOST=$DB_HOST"
    echo "DB_DATABASE=$DB_NAME"
    echo "DB_PORT=$DB_PORT"
} >> "$DOTENV_FILE"
