#!/bin/bash

# Make migrations for the route_analyzer app
echo "Making migrations for route_analyzer app..."
python manage.py makemigrations route_analyzer

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

echo "Setup complete!"
