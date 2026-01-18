#!/usr/bin/sh

echo "Pulling latest changes from git..."
sudo git pull

echo "Building wiki pages..."
cd ../docs
npm run docs:build

echo "Restarting services..."
sudo systemctl restart apache2

echo "Restarting evaluator service..."
sudo systemctl restart evaluator.service

echo "Update complete."