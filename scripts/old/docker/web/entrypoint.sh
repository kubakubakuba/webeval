#!/bin/bash
set -e

source $VENV_DIR/bin/activate

echo "Clone qtrvsim-eval-web"

#test if the qtrvsim-eval-web directory is empty

if [ -z "$( ls -A '/home/qtrvsim-eval-web' )" ]; then
	INITIALIZE_DB=true
	git clone https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web.git /home/qtrvsim-eval-web
fi

cd /home/qtrvsim-eval-web

echo "Create .env file"

if [ ! -f .env ]; then
	touch .env

	echo "DB_USER=$DB_USER" >> .env
	echo "DB_PASSWORD=$DB_PASSWORD" >> .env
	echo "DB_NAME=$DB_NAME" >> .env
	echo "DB_DATABASE=$DB_DATABASE" >> .env
	echo "DB_HOST=$DB_HOST" >> .env
	echo "DB_PORT=$DB_PORT" >> .env
	echo "SECRET_KEY=$SECRET_KEY" >> .env
	echo "MAIL_SERVER=$MAIL_SERVER" >> .env
	echo "MAIL_PORT=$MAIL_PORT" >> .env
	echo "MAIL_USE_TLS=$MAIL_USE_TLS" >> .env
	echo "MAIL_USE_SSL=$MAIL_USE_SSL" >> .env
	echo "MAIL_USERNAME=$MAIL_USERNAME" >> .env
	echo "MAIL_PASSWORD=$MAIL_PASSWORD" >> .env
	echo "MAIL_DEFAULT_SENDER=$MAIL_DEFAULT_SENDER" >> .env
	echo "TEMPLATES_DIR=/app/S_templates" >> .env
	echo "TASKS_DIR=/app/tasks" >> .env
fi

#wait until the db is ready, maximum 60 seconds

for i in {1..60}; do
	nc -z $DB_HOST $DB_PORT && break
	echo "Waiting for the database to be ready... $i s/60 s max"
	sleep 1
done

echo "Database is ready"

echo "Create database"

cd /home/qtrvsim-eval-web/scripts

if [ -f create_database.sh ]; then
	if [ "$INITIALIZE_DB" = true ]; then
		cp /home/setup/database.sh /home/qtrvsim-eval-web/scripts/database.sh

		chmod +x database.sh
		./database.sh
	fi
fi

cd /home/qtrvsim-eval-web/web

#use sed to replace 'sslmode': 'require' with 'sslmode': 'disable' in the web/db.py and in evaluator/evaldb.py

sed -i "s/'sslmode': 'require'/'sslmode': 'disable'/g" /home/qtrvsim-eval-web/web/db.py
sed -i "s/'sslmode': 'require'/'sslmode': 'disable'/g" /home/qtrvsim-eval-web/evaluator/evaldb.py

echo "Start web server"

exec gunicorn -w 3 -b 0.0.0.0:8000 app:app