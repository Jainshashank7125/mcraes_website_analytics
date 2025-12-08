#!/bin/bash
# Quick validation script to check cron status in Docker container

CONTAINER_NAME="mcraes-backend"

echo "=== Cron Job Validation for Docker ==="
echo ""

# Check container status
echo "1. Container Status:"
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "   ✓ Container '$CONTAINER_NAME' is running"
else
    echo "   ✗ Container '$CONTAINER_NAME' is NOT running"
    exit 1
fi
echo ""

# Check cron service
echo "2. Cron Service Status:"
if docker exec $CONTAINER_NAME pgrep -x cron > /dev/null 2>&1; then
    CRON_PID=$(docker exec $CONTAINER_NAME pgrep -x cron)
    echo "   ✓ Cron service is running (PID: $CRON_PID)"
else
    echo "   ✗ Cron service is NOT running"
    echo "   → Run: docker exec $CONTAINER_NAME service cron start"
fi
echo ""

# Check cron jobs
echo "3. Cron Jobs Configuration:"
CRON_JOBS=$(docker exec $CONTAINER_NAME crontab -l 2>/dev/null || echo "")
if [ -z "$CRON_JOBS" ]; then
    echo "   ✗ No cron jobs configured"
    echo "   → Run: ./check_and_setup_cron_docker.sh"
else
    HAS_TOKEN_JOB=$(echo "$CRON_JOBS" | grep -q "generate_ga4_token.py" && echo "yes" || echo "no")
    HAS_SYNC_JOB=$(echo "$CRON_JOBS" | grep -q "daily_sync_job.py" && echo "yes" || echo "no")
    
    if [ "$HAS_TOKEN_JOB" = "yes" ]; then
        echo "   ✓ GA4 token generation cron job is configured (hourly)"
    else
        echo "   ✗ GA4 token generation cron job NOT found"
    fi
    
    if [ "$HAS_SYNC_JOB" = "yes" ]; then
        echo "   ✓ Daily sync cron job is configured"
    else
        echo "   ✗ Daily sync cron job NOT found"
    fi
    
    if [ "$HAS_TOKEN_JOB" = "yes" ] || [ "$HAS_SYNC_JOB" = "yes" ]; then
        echo ""
        echo "   Active cron jobs:"
        docker exec $CONTAINER_NAME crontab -l | sed 's/^/      /'
    fi
    
    if [ "$HAS_TOKEN_JOB" = "no" ] || [ "$HAS_SYNC_JOB" = "no" ]; then
        echo "   → Run: ./check_and_setup_cron_docker.sh"
    fi
fi
echo ""

# Check script exists
echo "4. Sync Script:"
if docker exec $CONTAINER_NAME test -f "/app/daily_sync_job.py"; then
    echo "   ✓ daily_sync_job.py exists"
else
    echo "   ✗ daily_sync_job.py NOT found"
fi
echo ""

# Check recent sync logs
echo "5. Recent Sync Activity:"
if docker exec $CONTAINER_NAME test -f "/app/logs/daily_sync.log"; then
    echo "   ✓ Daily sync log file exists"
    echo "   Last 5 lines:"
    docker exec $CONTAINER_NAME tail -n 5 /app/logs/daily_sync.log 2>/dev/null | sed 's/^/      /' || echo "      (log file is empty)"
else
    echo "   ⚠ No daily sync log file yet (will be created on first run)"
fi

if docker exec $CONTAINER_NAME test -f "/app/logs/ga4_token.log"; then
    echo "   ✓ GA4 token log file exists"
    echo "   Last 3 lines:"
    docker exec $CONTAINER_NAME tail -n 3 /app/logs/ga4_token.log 2>/dev/null | sed 's/^/      /' || echo "      (log file is empty)"
else
    echo "   ⚠ No GA4 token log file yet (will be created on first run)"
fi
echo ""

# Check database for recent sync jobs
echo "6. Recent Sync Jobs in Database:"
RECENT_JOBS=$(docker exec mcraes-postgres psql -U postgres -d postgres -t -c \
    "SELECT COUNT(*) FROM sync_jobs WHERE created_at > NOW() - INTERVAL '24 hours';" 2>/dev/null || echo "0")
echo "   Jobs in last 24 hours: $RECENT_JOBS"
echo ""

echo "=== Validation Complete ==="
echo ""
echo "Cron Jobs Summary:"
CRON_JOBS=$(docker exec $CONTAINER_NAME crontab -l 2>/dev/null || echo "")
if echo "$CRON_JOBS" | grep -q "generate_ga4_token.py"; then
    echo "  ✓ GA4 Token Generation: Every hour"
fi
if echo "$CRON_JOBS" | grep -q "daily_sync_job.py"; then
    echo "  ✓ Daily Sync: 18:30 UTC (11:30 PM IST)"
fi
if [ -z "$CRON_JOBS" ] || (! echo "$CRON_JOBS" | grep -q "generate_ga4_token.py" && ! echo "$CRON_JOBS" | grep -q "daily_sync_job.py"); then
    echo "  ✗ No cron jobs configured"
fi

