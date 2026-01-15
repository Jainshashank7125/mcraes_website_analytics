#!/bin/bash
# Automatic cron setup script for Docker containers
# This script sets up cron jobs automatically without user interaction
# Called by docker-entrypoint.sh on container start

set -e

SCRIPT_NAME="daily_sync_job.py"
CRON_SCHEDULE="30 18 * * *"  # 18:30 UTC = 11:30 PM IST
LOG_FILE="/app/logs/daily_sync.log"

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Get Python path
PYTHON_PATH=$(which python3 || which python)

# Get current cron jobs (if any)
CRON_JOBS=$(crontab -l 2>/dev/null || echo "")

# Setup hourly GA4 token generation cron job
if [ -f "/app/generate_ga4_token.py" ]; then
    if ! echo "$CRON_JOBS" | grep -q "generate_ga4_token.py"; then
        echo "[AUTO-SETUP] Setting up hourly GA4 token generation cron job..."
        TOKEN_CRON_JOB="0 * * * * cd /app && ${PYTHON_PATH} generate_ga4_token.py >> /app/logs/ga4_token.log 2>&1"
        if [ -z "$CRON_JOBS" ]; then
            echo "$TOKEN_CRON_JOB" | crontab -
        else
            (echo "$CRON_JOBS"; echo "$TOKEN_CRON_JOB") | crontab -
        fi
        echo "[AUTO-SETUP] GA4 token generation cron job configured (runs every hour)"
        # Update CRON_JOBS for next check
        CRON_JOBS=$(crontab -l 2>/dev/null || echo "")
    else
        echo "[AUTO-SETUP] GA4 token generation cron job already configured"
    fi
fi

# Setup daily sync cron job
if [ -f "/app/${SCRIPT_NAME}" ]; then
    if ! echo "$CRON_JOBS" | grep -q "${SCRIPT_NAME}"; then
        echo "[AUTO-SETUP] Setting up daily sync cron job..."
        # Export required environment variables for cron job
        SYNC_CRON_JOB="${CRON_SCHEDULE} cd /app && export AGENCY_ANALYTICS_API_KEY='${AGENCY_ANALYTICS_API_KEY}' && export SCRUNCH_API_TOKEN='${SCRUNCH_API_TOKEN}' && export OPENAI_API_KEY='${OPENAI_API_KEY}' && export SUPABASE_DB_HOST='${SUPABASE_DB_HOST}' && export SUPABASE_DB_PORT='${SUPABASE_DB_PORT}' && export SUPABASE_DB_NAME='${SUPABASE_DB_NAME}' && export SUPABASE_DB_USER='${SUPABASE_DB_USER}' && export SUPABASE_DB_PASSWORD='${SUPABASE_DB_PASSWORD}' && export JWT_SECRET_KEY='${JWT_SECRET_KEY}' && export GA4_CREDENTIALS_PATH='${GA4_CREDENTIALS_PATH}' && ${PYTHON_PATH} ${SCRIPT_NAME} >> ${LOG_FILE} 2>&1"
        if [ -z "$CRON_JOBS" ]; then
            echo "$SYNC_CRON_JOB" | crontab -
        else
            (echo "$CRON_JOBS"; echo "$SYNC_CRON_JOB") | crontab -
        fi
        echo "[AUTO-SETUP] Daily sync cron job configured (runs at 18:30 UTC / 11:30 PM IST)"
    else
        echo "[AUTO-SETUP] Daily sync cron job already configured"
    fi
else
    echo "[AUTO-SETUP] WARNING: ${SCRIPT_NAME} not found, skipping daily sync cron job setup"
fi

# Display configured cron jobs
echo "[AUTO-SETUP] Current cron jobs:"
crontab -l 2>/dev/null || echo "  (none)"
echo ""

