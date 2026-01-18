#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ "$EUID" -ne 0 ]; then 
	echo "Please run as root (use sudo)"
	exit 1
fi

echo "Project directory: $PROJECT_ROOT"
echo ""

echo "Installing Apache configuration..."
sed "s|PROJECT_ROOT|$PROJECT_ROOT|g" "$SCRIPT_DIR/webeval-apache.conf" > /etc/apache2/sites-available/webeval.conf

if ! a2query -s qtrvsim-eval > /dev/null 2>&1; then
	echo "Enabling Apache site..."
	a2ensite webeval
	
	if a2query -s 000-default > /dev/null 2>&1; then
		echo "Disabling default Apache site..."
		a2dissite 000-default.conf
	fi
else
	echo "[INFO] Site qtrvsim-eval already enabled"
fi

echo "Testing Apache configuration..."
apache2ctl configtest

if [ $? -eq 0 ]; then
	echo "[OK] Apache configuration is valid"
	echo ""
	echo "Reloading Apache..."
	systemctl reload apache2
	echo "[OK] Apache reloaded"
else
	echo "[ERROR] Apache configuration test failed"
	exit 1
fi

echo ""
echo "[OK] Apache2 setup complete!"