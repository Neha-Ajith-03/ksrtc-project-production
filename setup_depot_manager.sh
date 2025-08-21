#!/bin/bash

# Make migrations for the depot_manager app
echo "Making migrations for depot_manager app..."
python manage.py makemigrations depot_manager

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Create dummy employees (drivers and conductors)
echo "Creating dummy employees..."
python manage.py create_dummy_employees --drivers 30 --conductors 30 --depots 5

echo "Setup complete!"
