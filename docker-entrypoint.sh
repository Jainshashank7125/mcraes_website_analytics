#!/bin/bash
# Docker entrypoint script to run both cron and uvicorn

set -e

# Create logs directory
mkdir -p /app/logs

# Start cron service
echo "Starting cron service..."
service cron start

# Check if cron is running
if ! pgrep -x cron > /dev/null; then
    echo "Warning: Cron service failed to start"
fi

# Automatically setup cron jobs using the auto-setup script
if [ -f "/usr/local/bin/setup_cron_auto.sh" ]; then
    echo "Running automatic cron job setup..."
    /usr/local/bin/setup_cron_auto.sh
elif [ -f "/app/setup_cron_auto.sh" ]; then
    echo "Running automatic cron job setup..."
    /app/setup_cron_auto.sh
else
    echo "Warning: setup_cron_auto.sh not found, skipping automatic cron setup"
fi

# Start the main application
exec "$@"

