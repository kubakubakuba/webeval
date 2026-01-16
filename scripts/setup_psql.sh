#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ "$EUID" -ne 0 ]; then 
	echo "Please run as root (use sudo)"
	exit 1
fi

if [ -f "$PROJECT_ROOT/.env" ]; then
	export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
else
	echo "Error: .env file not found at $PROJECT_ROOT/.env"
	echo "Please create .env file based on .env.example"
	exit 1
fi

echo "Starting PostgreSQL..."
systemctl enable postgresql
systemctl start postgresql

sleep 2

echo "Setting PostgreSQL password..."
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$POSTGRES_PASSWORD';" 2>/dev/null

if [ $? -eq 0 ]; then
	echo "[OK] PostgreSQL password set successfully"
else
	echo "[ERROR] Failed to set PostgreSQL password"
	exit 1
fi

echo ""
echo "[OK] PostgreSQL setup complete"