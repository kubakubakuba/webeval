#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Building VitePress documentation..."
echo "===================================="
echo ""

if [ ! -d "$PROJECT_ROOT/node_modules" ]; then
	echo "Installing Node.js dependencies..."
	cd "$PROJECT_ROOT"
	npm install
fi

echo "Building documentation..."
cd "$PROJECT_ROOT"
npm run docs:build

if [ $? -eq 0 ]; then
	echo ""
	echo "[OK] Documentation built successfully"
	echo ""
	echo "Built files location: $PROJECT_ROOT/docs/.vitepress/dist"
else
	echo "[ERROR] Failed to build documentation"
	exit 1
fi

if [ -d "$PROJECT_ROOT/docs/.vitepress/dist" ]; then
	echo "Setting wiki permissions for www-data..."
	chmod 755 "$PROJECT_ROOT"
	chmod 755 "$PROJECT_ROOT/docs"
	chmod -R 755 "$PROJECT_ROOT/docs/.vitepress/dist"
fi