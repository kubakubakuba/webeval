#!/bin/bash
set -e


source $VENV_DIR/bin/activate

echo "Cloning qtrvsim repository"
if [ ! -d /home/qtrvsim-eval-web ]; then
  git clone https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web.git /home/qtrvsim-eval-web
fi

cd /home/qtrvsim-eval-web/evaluator

echo "Installing dependencies"

cp /requirements.txt .

$VENV_DIR/bin/pip install -r requirements.txt

echo "Setting up environment variables"
touch .env
echo "DB_HOST=$DB_HOST" >> .env
echo "DB_PORT=$DB_PORT" >> .env
echo "DB_USER=$DB_USER" >> .env
echo "DB_PASSWORD=$DB_PASSWORD" >> .env

cd /home/qtrvsim-eval-web/evaluator

#use sed to replace 'sslmode': 'require' with 'sslmode': 'disable' in the web/db.py and in evaluator/evaldb.py

sed -i "s/'sslmode': 'require'/'sslmode': 'disable'/g" /home/qtrvsim-eval-web/web/db.py
sed -i "s/'sslmode': 'require'/'sslmode': 'disable'/g" /home/qtrvsim-eval-web/evaluator/evaldb.py

echo "Running evaluator service"
python3 evaluator.py
