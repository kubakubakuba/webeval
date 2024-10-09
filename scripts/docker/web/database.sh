#!/bin/sh

DB_USER="${DB_USER:-defaultuser}"
DB_NAME="${DB_NAME:-qtrvsim_web_eval}"
DB_PASSWORD="${DB_PASSWORD:-defaultpassword}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
MAIL_USERNAME="${MAIL_USERNAME:-defaultmail}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-rootpassword}"
EVAL_DEFAULT_ADMIN="${EVAL_DEFAULT_ADMIN:-admin}"
EVAL_DEFAULT_ADMIN_PASSWORD="${EVAL_DEFAULT_ADMIN_PASSWORD:-adminpassword}"

DOTENV_FILE="../.env"

ORIGINAL_DATABASE_SQL_FILE="qtrvsim_web_eval.sql"
MODIFIED_DATABASE_SQL_FILE="database.sql"

if [ ! -f "$ORIGINAL_DATABASE_SQL_FILE" ]; then
    echo "$ORIGINAL_DATABASE_SQL_FILE does not exist."
    exit 1
fi

sed "s/qtrvsim/$DB_USER/g" "$ORIGINAL_DATABASE_SQL_FILE" > "$MODIFIED_DATABASE_SQL_FILE"

echo "Creating user $DB_USER..."
PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

echo "Creating database $DB_NAME..."
PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "Applying database schema from $MODIFIED_DATABASE_SQL_FILE..."
PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -d $DB_NAME -a -f "$MODIFIED_DATABASE_SQL_FILE"

#if the APP_DEFAULT_ADMIN is not None, create the user

if [ "$APP_DEFAULT_ADMIN" != "None" ]; then
    echo "Creating default admin user $APP_DEFAULT_ADMIN..."
    SALT=$(openssl rand -base64 16)

    #hashed_password = sha512((password + salt).encode()).hexdigest()
    #hashed_email = sha512((email + salt).encode()).hexdigest()

    HASHED_PASSWORD=$(python -c "from hashlib import sha512; print(sha512(('$EVAL_DEFAULT_ADMIN_PASSWORD' + '$SALT').encode()).hexdigest())")
    HASHED_EMAIL=$(python -c "from hashlib import sha512; print(sha512(('$MAIL_USERNAME' + '$SALT').encode()).hexdigest())")

    PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h "$DB_HOST" -p "$DB_PORT" -d $DB_NAME -c "INSERT INTO users (email, password, salt, username, admin, verified) VALUES ('$HASHED_EMAIL', '$HASHED_PASSWORD', '$SALT', '$EVAL_DEFAULT_ADMIN', true, true);"
    echo "Default admin user created."
fi


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
