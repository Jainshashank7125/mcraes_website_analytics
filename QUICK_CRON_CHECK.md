# Quick Cron Check for Docker

## Fastest Way to Check Cron Status

```bash
./validate_cron_docker.sh
```

## Fastest Way to Setup Cron

```bash
./check_and_setup_cron_docker.sh
```

## One-Liner Commands

### Check if cron is active:
```bash
docker exec mcraes-backend crontab -l && echo "✓ Cron configured" || echo "✗ No cron jobs"
```

### Check if cron service is running:
```bash
docker exec mcraes-backend pgrep -x cron && echo "✓ Cron running" || echo "✗ Cron not running"
```

### Setup cron quickly:
```bash
docker exec mcraes-backend bash -c "apt-get update && apt-get install -y cron && service cron start && mkdir -p /app/logs && (echo '0 * * * * cd /app && python3 generate_ga4_token.py >> /app/logs/ga4_token.log 2>&1'; echo '30 18 * * * cd /app && python3 daily_sync_job.py >> /app/logs/daily_sync.log 2>&1') | crontab - && crontab -l"
```

## After Rebuilding Container

If you rebuild the container with the updated Dockerfile, cron will be automatically configured:

```bash
docker-compose build backend
docker-compose up -d backend
```

Then verify:
```bash
./validate_cron_docker.sh
```

