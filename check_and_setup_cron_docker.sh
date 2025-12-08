#!/bin/bash
# Script to check and setup cron jobs for Docker containers
# This script checks if cron is active and sets it up if needed

set -e

CONTAINER_NAME="mcraes-backend"
SCRIPT_NAME="daily_sync_job.py"
CRON_SCHEDULE="30 18 * * *"  # 18:30 UTC = 11:30 PM IST
LOG_FILE="/app/logs/daily_sync.log"

echo "=========================================="
echo "McRAE Analytics - Cron Job Checker"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if container is running
print_status "$YELLOW" "Checking if container '$CONTAINER_NAME' is running..."
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_status "$RED" "[ERROR] Container '$CONTAINER_NAME' is not running!"
    echo "Please start the container first: docker-compose up -d"
    exit 1
fi
print_status "$GREEN" "[OK] Container is running"
echo ""

# Check if cron is installed in container
print_status "$YELLOW" "Checking if cron is installed in container..."
if ! docker exec $CONTAINER_NAME which cron > /dev/null 2>&1; then
    print_status "$YELLOW" "[WARNING] Cron is not installed in container"
    print_status "$YELLOW" "Installing cron..."
    docker exec $CONTAINER_NAME bash -c "apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*" || {
        print_status "$RED" "[ERROR] Failed to install cron"
        exit 1
    }
    print_status "$GREEN" "[OK] Cron installed"
else
    print_status "$GREEN" "[OK] Cron is installed"
fi
echo ""

# Check if cron service is running
print_status "$YELLOW" "Checking if cron service is running..."
if ! docker exec $CONTAINER_NAME pgrep -x cron > /dev/null 2>&1; then
    print_status "$YELLOW" "[WARNING] Cron service is not running"
    print_status "$YELLOW" "Starting cron service..."
    docker exec $CONTAINER_NAME service cron start || {
        print_status "$RED" "[ERROR] Failed to start cron service"
        exit 1
    }
    print_status "$GREEN" "[OK] Cron service started"
else
    print_status "$GREEN" "[OK] Cron service is running (PID: $(docker exec $CONTAINER_NAME pgrep -x cron))"
fi
echo ""

# Check if daily_sync_job.py exists in container
print_status "$YELLOW" "Checking if $SCRIPT_NAME exists in container..."
if ! docker exec $CONTAINER_NAME test -f "/app/$SCRIPT_NAME"; then
    print_status "$RED" "[ERROR] $SCRIPT_NAME not found in container at /app/$SCRIPT_NAME"
    print_status "$YELLOW" "Make sure the file is copied to the container or mounted as a volume"
    exit 1
fi
print_status "$GREEN" "[OK] $SCRIPT_NAME exists"

# Check if generate_ga4_token.py exists in container
print_status "$YELLOW" "Checking if generate_ga4_token.py exists in container..."
if docker exec $CONTAINER_NAME test -f "/app/generate_ga4_token.py"; then
    print_status "$GREEN" "[OK] generate_ga4_token.py exists"
else
    print_status "$YELLOW" "[WARNING] generate_ga4_token.py not found (GA4 token generation will not work)"
fi
echo ""

# Create logs directory if it doesn't exist
print_status "$YELLOW" "Checking logs directory..."
docker exec $CONTAINER_NAME mkdir -p /app/logs
print_status "$GREEN" "[OK] Logs directory ready"
echo ""

# Check current cron jobs
print_status "$YELLOW" "Checking current cron jobs..."
CRON_JOBS=$(docker exec $CONTAINER_NAME crontab -l 2>/dev/null || echo "")

if echo "$CRON_JOBS" | grep -q "$SCRIPT_NAME"; then
    print_status "$GREEN" "[OK] Daily sync cron job is already configured!"
    echo ""
    echo "Current cron jobs:"
    echo "----------------------------------------"
    docker exec $CONTAINER_NAME crontab -l
    echo "----------------------------------------"
    echo ""
else
    print_status "$YELLOW" "[INFO] Daily sync cron job is NOT configured"
    echo ""
    read -p "Do you want to set up the daily sync cron job? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "$YELLOW" "Setting up daily sync cron job..."
        
        # Get Python path in container
        PYTHON_PATH=$(docker exec $CONTAINER_NAME which python3 || docker exec $CONTAINER_NAME which python)
        
        # Setup hourly GA4 token generation cron job first
        if docker exec $CONTAINER_NAME test -f "/app/generate_ga4_token.py"; then
            if ! echo "$CRON_JOBS" | grep -q "generate_ga4_token.py"; then
                print_status "$YELLOW" "Setting up hourly GA4 token generation cron job..."
                TOKEN_CRON_JOB="0 * * * * cd /app && ${PYTHON_PATH} generate_ga4_token.py >> /app/logs/ga4_token.log 2>&1"
                if [ -z "$CRON_JOBS" ]; then
                    echo "$TOKEN_CRON_JOB" | docker exec -i $CONTAINER_NAME crontab -
                else
                    (echo "$CRON_JOBS"; echo "$TOKEN_CRON_JOB") | docker exec -i $CONTAINER_NAME crontab -
                fi
                print_status "$GREEN" "[OK] GA4 token generation cron job configured (hourly)"
                CRON_JOBS=$(docker exec $CONTAINER_NAME crontab -l 2>/dev/null || echo "")
            fi
        fi
        
        # Create daily sync cron job entry
        CRON_JOB="${CRON_SCHEDULE} cd /app && ${PYTHON_PATH} ${SCRIPT_NAME} >> ${LOG_FILE} 2>&1"
        
        # Add to crontab
        if [ -z "$CRON_JOBS" ]; then
            # No existing crontab
            echo "$CRON_JOB" | docker exec -i $CONTAINER_NAME crontab -
        else
            # Append to existing crontab
            (echo "$CRON_JOBS"; echo "$CRON_JOB") | docker exec -i $CONTAINER_NAME crontab -
        fi
        
        print_status "$GREEN" "[SUCCESS] Daily sync cron job configured!"
        echo ""
        echo "Cron job details:"
        echo "  GA4 Token Generation: Every hour (0 * * * *)"
        echo "  Daily Sync: ${CRON_SCHEDULE} (Daily at 18:30 UTC = 11:30 PM IST)"
        echo "  Script: ${SCRIPT_NAME}"
        echo "  Logs: ${LOG_FILE}"
        echo ""
    else
        print_status "$YELLOW" "Skipping cron job setup"
    fi
fi
echo ""

# Verify cron jobs are active
print_status "$YELLOW" "Verifying cron job configuration..."
FINAL_CRON_JOBS=$(docker exec $CONTAINER_NAME crontab -l 2>/dev/null || echo "")
HAS_SYNC_JOB=$(echo "$FINAL_CRON_JOBS" | grep -q "$SCRIPT_NAME" && echo "yes" || echo "no")
HAS_TOKEN_JOB=$(echo "$FINAL_CRON_JOBS" | grep -q "generate_ga4_token.py" && echo "yes" || echo "no")

if [ "$HAS_SYNC_JOB" = "yes" ] || [ "$HAS_TOKEN_JOB" = "yes" ]; then
    print_status "$GREEN" "[OK] Cron jobs are active and configured"
    echo ""
    echo "Active cron jobs:"
    echo "----------------------------------------"
    docker exec $CONTAINER_NAME crontab -l
    echo "----------------------------------------"
    echo ""
    if [ "$HAS_TOKEN_JOB" = "yes" ]; then
        print_status "$GREEN" "✓ GA4 token generation: Hourly"
    fi
    if [ "$HAS_SYNC_JOB" = "yes" ]; then
        print_status "$GREEN" "✓ Daily sync: 18:30 UTC (11:30 PM IST)"
    fi
else
    print_status "$RED" "[WARNING] No cron jobs found in crontab"
fi
echo ""

# Check if we can test the script
print_status "$YELLOW" "Checking if we can test the sync script..."
if docker exec $CONTAINER_NAME test -f "/app/$SCRIPT_NAME"; then
    print_status "$GREEN" "[OK] Script is accessible"
    echo ""
    read -p "Do you want to test the sync script now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "$YELLOW" "Running test sync (this may take a while)..."
        docker exec $CONTAINER_NAME python3 /app/$SCRIPT_NAME || {
            print_status "$RED" "[ERROR] Test sync failed. Check the output above for errors."
        }
    fi
fi
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Container: $CONTAINER_NAME"
echo "Cron Status: $(docker exec $CONTAINER_NAME pgrep -x cron > /dev/null 2>&1 && echo 'Running' || echo 'Not Running')"
echo "Cron Jobs Configured: $(docker exec $CONTAINER_NAME crontab -l 2>/dev/null | grep -c "$SCRIPT_NAME" || echo "0")"
echo ""
echo "To check cron jobs manually:"
echo "  docker exec $CONTAINER_NAME crontab -l"
echo ""
echo "To view cron logs:"
echo "  docker exec $CONTAINER_NAME tail -f $LOG_FILE"
echo ""
echo "To test sync manually:"
echo "  docker exec $CONTAINER_NAME python3 /app/$SCRIPT_NAME"
echo ""
echo "To check if cron is running:"
echo "  docker exec $CONTAINER_NAME pgrep -x cron"
echo ""

