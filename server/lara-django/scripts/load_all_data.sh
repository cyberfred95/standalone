#!/bin/bash
# Script to load all initial data from XML/JSON files

# Exit on error
set -e

echo "Loading all data..."

# Load domains
echo "Loading domains..."
python manage.py load_domains data/domaines.xml

# Load glossaries
echo "Loading glossaries..."
python manage.py load_glossaries data/lara-glossaries.xml

# Load memories
echo "Loading memories..."
python manage.py load_memories data/lara-memories.xml

# Load resources
echo "Loading resources..."
python manage.py load_resources data/lara-resources.json

# Load templates
echo "Loading templates..."
python manage.py load_templates data/templates.xml

echo "All data loaded successfully!"
