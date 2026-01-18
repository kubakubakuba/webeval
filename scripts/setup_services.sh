#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Service Setup"
echo "======================================="
echo ""

if [ "$EUID" -ne 0 ]; then 
	echo "Please run as root (use sudo)"
	exit 1
fi

echo "Project directory: $PROJECT_ROOT"
echo ""

if [ ! -f "$PROJECT_ROOT/.env" ]; then
	echo "[ERROR] .env file not found in $PROJECT_ROOT"
	echo "Please create .env file based on .env.example"
	exit 1
fi

echo "Creating Python virtual environment for web service..."
cd "$PROJECT_ROOT/web"
uv venv /opt/web-venv

echo "Installing web dependencies..."
uv pip install --python /opt/web-venv/bin/python \
	flask \
	flask-mail \
	gunicorn \
	toml \
	markdown \
	psycopg2-binary \
	python-dotenv \
	pygments

echo ""
echo "Creating Python virtual environment for evaluator service..."
cd "$PROJECT_ROOT/evaluator"
uv venv /opt/eval-venv

echo "Installing evaluator dependencies..."
uv pip install --python /opt/eval-venv/bin/python \
	toml \
	markdown \
	psycopg2-binary \
	python-dotenv

echo ""
echo "Creating qtrvsim system user..."
if ! id -u qtrvsim > /dev/null 2>&1; then
	useradd --system --no-create-home --shell /usr/sbin/nologin qtrvsim
	echo "[OK] User qtrvsim created"
else
	echo "[INFO] User qtrvsim already exists"
fi

echo "Setting permissions..."
chown -R qtrvsim:qtrvsim "$PROJECT_ROOT"
chmod 750 "$PROJECT_ROOT"
chmod 640 "$PROJECT_ROOT/.env"

echo ""
echo "Installing systemd services..."
sed "s|PROJECT_ROOT|$PROJECT_ROOT|g" "$SCRIPT_DIR/webeval.service" > /etc/systemd/system/webeval.service
sed "s|PROJECT_ROOT|$PROJECT_ROOT|g" "$SCRIPT_DIR/evaluator.service" > /etc/systemd/system/evaluator.service

systemctl daemon-reload

systemctl start webeval
systemctl start evaluator

echo ""
echo "[OK] Service setup complete!"