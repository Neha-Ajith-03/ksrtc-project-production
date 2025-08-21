# Use a smaller Python image
FROM python:3.10-slim  

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1  

# Set the working directory
WORKDIR /app  

# Install system dependencies (if needed for certain Python packages)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy and install only dependencies first (to leverage caching)
COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt  

# Copy the Django project
COPY . .  

# Collect static files (avoid storing them inside the container)
RUN python manage.py collectstatic --noinput --clear  

# Expose the port Django runs on
EXPOSE 8000  

# Use gunicorn to serve the application
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "ksrtc1.wsgi:application"]
