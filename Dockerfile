# Use Python 3.12 slim base image
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=pilot_feedtray.settings

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# (Optional safety net) Install missing packages directly in case they're not in requirements.txt
RUN pip install djangorestframework daphne

# Copy project files
COPY . .

# Make your entrypoint script executable
RUN chmod +x all_commands.sh

# Expose port (match the port daphne or your app runs on)
EXPOSE 8000

# Default command to run your app
CMD ["./all_commands.sh"]
