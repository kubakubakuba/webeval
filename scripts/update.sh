#!/usr/bin/sh

echo "Pulling latest changes from git..."
sudo git pull

echo "Restarting services..."
sudo systemctl restart apache2

echo "Restarting evaluator service..."
sudo systemctl restart evaluator.service

echo "Update complete."