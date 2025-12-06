#!/bin/bash
# Script to initialize the database and load data

# Exit on error
set -e

echo "Starting database initialization..."

# Apply migrations
echo "Applying migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if not exists (requires Django 3.0+)
# This is a bit tricky in a script without interaction, usually done via custom command or env vars
# Skipping for now, user can create manually

echo "Database initialized successfully!"
