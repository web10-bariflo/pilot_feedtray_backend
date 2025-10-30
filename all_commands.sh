#!/bin/bash

# Ensure /app/logs exists
mkdir -p /app/logs

# Graceful shutdown handler
function terminate_processes {
    echo "Terminating Daphne server..."
    pkill -f "daphne"
    exit
}
trap terminate_processes SIGTERM

# Run migrations
echo "Running migrations..."
python3 manage.py migrate

# Start Daphne in foreground
echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 pilot_feedtray.asgi:application




