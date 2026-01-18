#!/usr/bin/env bash
set -e

echo "Installing system packages..."

if [ "$EUID" -ne 0 ]; then 
	echo "Please run as root (use sudo)"
	exit 1
fi

apt-get update

echo "Installing PostgreSQL database server..."
apt-get install -y --no-install-recommends \
	postgresql \
	postgresql-contrib

echo "Installing web server dependencies..."
apt-get install -y --no-install-recommends \
	postgresql-client \
	netcat-traditional \
	python3

echo "Installing evaluator dependencies..."
apt-get install -y --no-install-recommends \
	make \
	gcc \
	g++ \
	curl \
	gcc-riscv64-unknown-elf \
	qtrvsim

echo "Installing Node.js for VitePress documentation..."
apt-get install -y --no-install-recommends \
	nodejs \
	npm

echo "Installing Apache2..."
apt-get install -y apache2

echo "Enabling Apache modules..."
a2enmod proxy
a2enmod proxy_http
a2enmod headers
a2enmod ssl
a2enmod rewrite

echo "Restarting Apache2.."
systemctl restart apache2

echo "Installing uv.."
if ! command -v uv &> /dev/null; then
	echo "uv is not installed. Installing uv..."
	
	curl -LsSf https://astral.sh/uv/install.sh | sh

	echo "[OK] uv installed successfully"
fi

echo "[OK] All system requirements installed successfully"

echo "Run source ~.local/bin/env/ to have uv on path"