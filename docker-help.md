# Docker Compose Commands Reference

This document provides a comprehensive list of Docker Compose commands for managing the MacRAE's Website Analytics application.

## Table of Contents
- [Service Management](#service-management)
- [Accessing Services](#accessing-services)
- [Database Operations](#database-operations)
- [Logs and Monitoring](#logs-and-monitoring)
- [Backup and Restore](#backup-and-restore)
- [Migrations](#migrations)
- [Cron Jobs and Sync Jobs](#cron-jobs-and-sync-jobs)
- [Troubleshooting](#troubleshooting)
- [Development Commands](#development-commands)

---

## Service Management

### Start Services
```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d backend
docker compose up -d frontend
docker compose up -d postgres
```

### Stop Services
```bash
# Stop all services
docker compose down

# Stop services but keep volumes
docker compose down

# Stop and remove volumes (⚠️ WARNING: Deletes all data)
docker compose down -v
```

### Restart Services
```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart frontend
docker compose restart postgres
```

### Rebuild Services
```bash
# Rebuild all services
docker compose build

# Rebuild specific service
docker compose build backend
docker compose build frontend

# Rebuild and restart
docker compose up -d --build
```

### View Service Status
```bash
# List all running containers
docker compose ps

# View detailed status
docker compose ps -a
```

---

## Accessing Services

### Backend Service (Python/FastAPI)

#### Access Bash Shell
```bash
docker compose exec backend bash
# or
docker exec -it mcraes-backend bash
```

#### Access Python Shell
```bash
docker compose exec backend python
# or
docker exec -it mcraes-backend python
```

#### Run Python Scripts
```bash
# Run a script in the backend container
docker compose exec backend python /app/script_name.py

# Example: Run database verification
docker compose exec backend python /app/verify_synced_data.py
```

#### Check Backend Health
```bash
# Check if backend is responding
docker compose exec backend curl http://localhost:8000/health

# Or from host machine
curl http://localhost:8000/health
```

### Frontend Service (Node.js/React)

#### Access Bash Shell
```bash
docker compose exec frontend sh
# or
docker exec -it mcraes-frontend sh
```

#### Access Node.js Shell
```bash
docker compose exec frontend node
```

#### Install Frontend Dependencies
```bash
docker compose exec frontend npm install
```

#### Run Frontend Build
```bash
docker compose exec frontend npm run build
```

### Database Service (PostgreSQL)

#### Access PostgreSQL Shell (psql)
```bash
# Interactive psql shell
docker compose exec postgres psql -U postgres -d postgres
# or
docker exec -it mcraes-postgres psql -U postgres -d postgres
```

#### Run SQL Commands Directly
```bash
# Execute a single SQL command
docker compose exec postgres psql -U postgres -d postgres -c "SELECT version();"

# Execute SQL from a file
docker compose exec -T postgres psql -U postgres -d postgres < /path/to/script.sql

# Example: Check audit logs
docker compose exec postgres psql -U postgres -d postgres -c "SELECT id, action, user_email, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10;"
```

#### Database Connection Info
- **Host**: `localhost` (from host) or `postgres` (from other containers)
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: `postgres` (default, check docker-compose.yml)

---

## Database Operations

### Common psql Commands (Inside psql shell)
```sql
-- List all databases
\l

-- Connect to a database
\c database_name

-- List all tables
\dt

-- Describe a table structure
\d table_name

-- List all columns of a table
\d+ table_name

-- Show table size
SELECT pg_size_pretty(pg_total_relation_size('table_name'));

-- Quit psql
\q
```

### Database Backup

#### Quick Backup (Recommended - Custom Format)
```bash
# Create dump in custom format (best for local restore - handles JSON/data better)
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    --format=custom \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --blobs \
    --encoding=UTF8 \
    > dumps/backup_$(date +%Y%m%d_%H%M%S).dump

# Or use the provided script (automatically creates in ./dumps/)
./scripts/create_database_dump.sh
```

#### Plain SQL Backup (Alternative)
```bash
# Create plain SQL backup file
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --encoding=UTF8 \
    > dumps/backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed SQL backup
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --encoding=UTF8 \
    | gzip > dumps/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### Backup Specific Table
```bash
# Backup single table
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    -t table_name \
    --format=custom \
    > dumps/table_name_backup_$(date +%Y%m%d_%H%M%S).dump

# Backup multiple tables
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    -t table1 -t table2 \
    --format=custom \
    > dumps/tables_backup_$(date +%Y%m%d_%H%M%S).dump
```

#### Backup Format Comparison
- **Custom Format (`.dump`)** - Recommended
  - ✅ Better handling of JSON/JSONB data
  - ✅ Compressed (smaller file size)
  - ✅ Faster restore
  - ✅ Allows selective restore
  - ✅ More reliable for complex data types
  - Restore with: `pg_restore`

- **Plain SQL (`.sql`)**
  - ✅ Human-readable
  - ✅ Can be edited manually
  - ❌ Larger file size
  - ❌ May have issues with JSON/JSONB
  - ❌ Slower restore
  - Restore with: `psql`

### Database Restore

#### Restore from SQL File
```bash
# Restore from SQL file
docker compose exec -T postgres psql -U postgres -d postgres < backup_file.sql

# Or from host
cat backup_file.sql | docker compose exec -T postgres psql -U postgres -d postgres

# If you encounter JSON errors, continue past them (restores what it can)
docker compose exec -T postgres psql -U postgres -d postgres -v ON_ERROR_STOP=0 < backup_file.sql

# Or use single transaction mode (rolls back on error, but safer)
docker compose exec -T postgres psql -U postgres -d postgres --single-transaction < backup_file.sql
```

#### Restore from Custom Format (Recommended)
```bash
# Restore from custom format dump (best option)
docker compose exec -T postgres pg_restore \
    -U postgres \
    -d postgres \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    < dumps/backup_file.dump

# Or use the provided script
./scripts/restore_database_dump.sh dumps/backup_file.dump

# Restore to different database
docker compose exec -T postgres pg_restore \
    -U postgres \
    -d target_database_name \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    < dumps/backup_file.dump
```

### Database Maintenance

#### Vacuum Database
```bash
# Run VACUUM (reclaim storage)
docker compose exec postgres psql -U postgres -d postgres -c "VACUUM;"

# VACUUM ANALYZE (update statistics)
docker compose exec postgres psql -U postgres -d postgres -c "VACUUM ANALYZE;"
```

#### Check Database Size
```bash
docker compose exec postgres psql -U postgres -d postgres -c "SELECT pg_size_pretty(pg_database_size('postgres'));"
```

#### List All Tables with Sizes
```bash
docker compose exec postgres psql -U postgres -d postgres -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

---

## Logs and Monitoring

### View Logs

#### All Services
```bash
# Follow all logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100
```

#### Specific Service
```bash
# Backend logs
docker compose logs -f backend

# Frontend logs
docker compose logs -f frontend

# Database logs
docker compose logs -f postgres
```

#### Logs with Timestamps
```bash
docker compose logs -f -t backend
```

#### Search Logs
```bash
# Search for errors in backend logs
docker compose logs backend | grep -i error

# Search for specific text
docker compose logs backend | grep "audit log"
```

### Resource Usage

#### Container Stats
```bash
# Real-time stats for all containers
docker stats

# Stats for specific container
docker stats mcraes-backend
docker stats mcraes-frontend
docker stats mcraes-postgres
```

#### Disk Usage
```bash
# Check Docker disk usage
docker system df

# Check volume usage
docker volume ls
docker volume inspect mcraes_website_analytics_postgres_data
```

---

## Backup and Restore

### Volume Backup

#### Backup PostgreSQL Volume
```bash
# Stop the postgres service
docker compose stop postgres

# Create a backup of the volume
docker run --rm -v mcraes_website_analytics_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

# Restart postgres
docker compose start postgres
```

#### Restore PostgreSQL Volume
```bash
# ⚠️ WARNING: This will overwrite existing data
docker compose stop postgres

# Restore from backup
docker run --rm -v mcraes_website_analytics_postgres_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/postgres_data_backup.tar.gz --strip 1"

# Restart postgres
docker compose start postgres
```

### Application Data Backup Script
```bash
#!/bin/bash
# Create a comprehensive backup

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Database backup
docker compose exec postgres pg_dump -U postgres postgres | gzip > "$BACKUP_DIR/database.sql.gz"

# Volume backup (if needed)
docker run --rm -v mcraes_website_analytics_postgres_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/postgres_volume.tar.gz /data

echo "Backup completed: $BACKUP_DIR"
```

---

## Migrations

### Django-like Migration System

The project includes a Django-like migration manager that automatically tracks and runs migrations.

#### Show Migration Status
```bash
# Show all migrations and their status
docker compose exec backend python manage_migrations.py showmigrations
```

#### Run All Pending Migrations
```bash
# Run all pending migrations (like Django's migrate)
docker compose exec backend python manage_migrations.py migrate
```

#### Run Specific Migration
```bash
# Run a specific migration by name
docker compose exec backend python manage_migrations.py migrate v20__add_is_active_to_clients
```

#### Fake Migration (Mark as Applied Without Running)
```bash
# Mark a migration as applied without executing it
docker compose exec backend python manage_migrations.py migrate --fake
```

### Manual Migration Execution

#### Execute a Single Migration File
```bash
# Execute a migration file manually
docker compose exec -T postgres psql -U postgres -d postgres < migrations/v20__add_is_active_to_clients.sql
```

#### Execute All Migrations in a Directory
```bash
# Execute all migrations in root directory
for file in migrations/v*.sql; do
    echo "Running $file..."
    docker compose exec -T postgres psql -U postgres -d postgres < "$file"
done

# Execute all migrations in v2 directory
for file in migrations/v2/*.sql; do
    echo "Running $file..."
    docker compose exec -T postgres psql -U postgres -d postgres < "$file"
done
```

### Check Migration Status

#### Using Migration Manager
```bash
# Show migration status (recommended)
docker compose exec backend python manage_migrations.py showmigrations
```

#### Manual Checks
```bash
# Check if migrations table exists
docker compose exec postgres psql -U postgres -d postgres -c "\d django_migrations"

# View applied migrations
docker compose exec postgres psql -U postgres -d postgres -c "SELECT app, name, applied FROM django_migrations ORDER BY applied;"

# Check if a table exists
docker compose exec postgres psql -U postgres -d postgres -c "\d table_name"

# List all tables
docker compose exec postgres psql -U postgres -d postgres -c "\dt"

# Check specific columns
docker compose exec postgres psql -U postgres -d postgres -c "\d+ clients"
```

---

## Cron Jobs and Sync Jobs

### Check Cron Status

#### Quick Validation
```bash
# Run validation script to check cron setup
./validate_cron_docker.sh
```

#### Check if Cron Service is Running
```bash
# Check if cron process is running
docker exec mcraes-backend pgrep -x cron

# Check cron service status
docker exec mcraes-backend service cron status
```

#### View Configured Cron Jobs
```bash
# List all cron jobs in container
docker exec mcraes-backend crontab -l

# Check if daily sync job is configured
docker exec mcraes-backend crontab -l | grep daily_sync_job.py
```

### Setup Cron Jobs

#### Automatic Setup Script
```bash
# Run comprehensive setup/check script
./check_and_setup_cron_docker.sh
```

#### Manual Setup
```bash
# Install cron (if not installed)
docker exec mcraes-backend apt-get update && \
  docker exec mcraes-backend apt-get install -y cron && \
  docker exec mcraes-backend rm -rf /var/lib/apt/lists/*

# Start cron service
docker exec mcraes-backend service cron start

# Create logs directory
docker exec mcraes-backend mkdir -p /app/logs

# Add daily sync cron job (runs at 18:30 UTC = 11:30 PM IST)
docker exec mcraes-backend bash -c \
  'echo "30 18 * * * cd /app && python3 daily_sync_job.py >> /app/logs/daily_sync.log 2>&1" | crontab -'

# Verify cron job was added
docker exec mcraes-backend crontab -l
```

### Validate Cron is Working

#### Check Cron Process
```bash
# Verify cron is running
docker exec mcraes-backend ps aux | grep cron

# Check cron PID
docker exec mcraes-backend pgrep -x cron
```

#### Test Sync Script Manually
```bash
# Run the daily sync script manually to test
docker exec mcraes-backend python3 /app/daily_sync_job.py
```

#### View Sync Logs

**Note:** Log files are persisted on the host at `./logs/` directory and are also accessible inside the container at `/app/logs/`.

```bash
# View recent sync logs (from host)
tail -n 50 logs/daily_sync.log

# Or from inside container
docker exec mcraes-backend tail -n 50 /app/logs/daily_sync.log

# Follow sync logs in real-time (from host)
tail -f logs/daily_sync.log

# Or from inside container
docker exec mcraes-backend tail -f /app/logs/daily_sync.log

# Search for errors in logs (from host)
grep -i error logs/daily_sync.log

# Or from inside container
docker exec mcraes-backend grep -i error /app/logs/daily_sync.log

# If log file doesn't exist yet (job hasn't run), check:
# 1. Verify logs directory exists on host
ls -la logs/

# 2. Verify logs directory exists in container
docker exec mcraes-backend ls -la /app/logs

# 3. Check if cron job is configured
docker exec mcraes-backend crontab -l | grep daily_sync

# 4. Check Docker container logs for sync-related errors
docker logs mcraes-backend --tail 100 | grep -i -E "(sync|error|daily)"

# 5. Manually test the sync job (creates log file)
docker exec mcraes-backend python3 /app/daily_sync_job.py

# 6. Check for errors after manual run (from host)
grep -i error logs/daily_sync.log 2>/dev/null || echo "No errors found or log file not created"
```

### Check Sync Jobs via API

#### Get All Sync Jobs
```bash
# Get all sync jobs (requires authentication token)
curl -X GET "http://localhost:8000/api/v1/sync/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by status
curl -X GET "http://localhost:8000/api/v1/sync/jobs?status=running" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by sync type
curl -X GET "http://localhost:8000/api/v1/sync/jobs?sync_type=agency_analytics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Sync Status Summary
```bash
curl -X GET "http://localhost:8000/api/v1/sync/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Sync Jobs in Database

#### View Recent Sync Jobs
```bash
# View all sync jobs
docker exec mcraes-postgres psql -U postgres -d postgres -c \
  "SELECT job_id, sync_type, status, created_at FROM sync_jobs ORDER BY created_at DESC LIMIT 10;"

# View running jobs
docker exec mcraes-postgres psql -U postgres -d postgres -c \
  "SELECT job_id, sync_type, status, progress, current_step FROM sync_jobs WHERE status = 'running';"

# View recent completed jobs
docker exec mcraes-postgres psql -U postgres -d postgres -c \
  "SELECT job_id, sync_type, status, completed_at FROM sync_jobs WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 10;"

# Count jobs in last 24 hours
docker exec mcraes-postgres psql -U postgres -d postgres -c \
  "SELECT COUNT(*) FROM sync_jobs WHERE created_at > NOW() - INTERVAL '24 hours';"
```

### Cron Job Schedules

#### GA4 Token Generation (Hourly)
- **Schedule**: `0 * * * *` (Every hour at minute 0)
- **Script**: `generate_ga4_token.py`
- **Logs**: `./logs/ga4_token.log` (on host) or `/app/logs/ga4_token.log` (in container)
- **Purpose**: Ensures GA4 access token is always fresh (tokens expire after 1 hour)

#### Daily Sync Job
- **Schedule**: `30 18 * * *` (Daily at 18:30 UTC)
- **IST Time**: 11:30 PM IST (IST = UTC + 5:30)
- **Script**: `daily_sync_job.py`
- **Logs**: `./logs/daily_sync.log` (on host) or `/app/logs/daily_sync.log` (in container)
- **Note**: Token generation runs before sync (via hourly job or as part of sync script)
- **Persistence**: Log files are persisted on the host via volume mount, so they survive container restarts

### What Gets Synced

The daily sync job automatically syncs:
1. **AgencyAnalytics**: All active clients (Complete mode)
2. **GA4**: All clients with GA4 property ID mapped (Complete mode)
3. **Scrunch AI**: All clients linked to Scrunch (Complete mode)

### Troubleshooting Cron

#### Cron Not Running
```bash
# Check if cron is installed
docker exec mcraes-backend which cron

# Install cron if missing
docker exec mcraes-backend apt-get update && \
  docker exec mcraes-backend apt-get install -y cron

# Start cron service
docker exec mcraes-backend service cron start

# Verify cron is running
docker exec mcraes-backend pgrep -x cron
```

#### Cron Job Not Executing
```bash
# Verify cron job is configured
docker exec mcraes-backend crontab -l

# Check script permissions
docker exec mcraes-backend ls -la /app/daily_sync_job.py

# Test script manually
docker exec mcraes-backend python3 /app/daily_sync_job.py

# Check logs for errors (from host)
tail -n 100 logs/daily_sync.log

# Or from container
docker exec mcraes-backend tail -n 100 /app/logs/daily_sync.log
```

#### Rebuild Container with Cron Support
```bash
# Rebuild backend container (includes cron auto-setup)
docker compose build backend

# Restart container
docker compose up -d backend

# Verify cron is configured
./validate_cron_docker.sh
```

---

## Troubleshooting

### Container Issues

#### View Container Details
```bash
# Inspect container
docker inspect mcraes-backend

# View container environment variables
docker compose exec backend env
```

#### Restart Failed Container
```bash
# Check container status
docker compose ps

# Restart specific container
docker compose restart backend

# Recreate container (removes and recreates)
docker compose up -d --force-recreate backend
```

#### Access Container Files
```bash
# Copy file from container to host
docker compose cp backend:/app/file.py ./file.py

# Copy file from host to container
docker compose cp ./file.py backend:/app/file.py

# List files in container
docker compose exec backend ls -la /app
```

### Database Connection Issues

#### Test Database Connection
```bash
# From backend container
docker compose exec backend python -c "
from app.db.database import SessionLocal
db = SessionLocal()
print('Database connection successful!')
db.close()
"

# From host machine
psql -h localhost -p 5432 -U postgres -d postgres
```

#### Reset Database (⚠️ DANGER: Deletes all data)
```bash
# Stop services
docker compose down

# Remove volume
docker volume rm mcraes_website_analytics_postgres_data

# Start services (creates new volume)
docker compose up -d
```

### Network Issues

#### Check Network Connectivity
```bash
# List networks
docker network ls

# Inspect network
docker network inspect mcraes_website_analytics_mcraes-network

# Test connectivity between containers
docker compose exec backend ping postgres
docker compose exec backend ping frontend
```

### Clean Up

#### Remove Unused Resources
```bash
# Remove stopped containers
docker compose rm

# Remove unused images
docker image prune

# Remove unused volumes (⚠️ Be careful!)
docker volume prune

# Full cleanup (⚠️ Removes all unused resources)
docker system prune -a
```

---

## Development Commands

### Backend Development

#### Run Tests
```bash
# If you have pytest configured
docker compose exec backend pytest

# Run specific test file
docker compose exec backend pytest tests/test_file.py
```

#### Install Python Dependencies
```bash
# Install new package
docker compose exec backend pip install package_name

# Update requirements.txt
docker compose exec backend pip freeze > requirements.txt
```

#### Access Backend Logs in Real-time
```bash
docker compose logs -f backend | grep -i error
```

### Frontend Development

#### Watch Mode (if configured)
```bash
# If you have watch mode in package.json
docker compose exec frontend npm run dev
```

#### Rebuild Frontend
```bash
# Rebuild frontend container
docker compose build frontend

# Restart frontend
docker compose restart frontend
```

### Database Development

#### Create Test Data
```bash
# Run a Python script to create test data
docker compose exec backend python /app/scripts/create_test_data.py
```

#### Query Specific Data
```bash
# Example: Get all clients
docker compose exec postgres psql -U postgres -d postgres -c "SELECT id, company_name, is_active FROM clients LIMIT 10;"

# Example: Get audit logs
docker compose exec postgres psql -U postgres -d postgres -c "SELECT id, action, user_email, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 20;"

# Example: Count records in a table
docker compose exec postgres psql -U postgres -d postgres -c "SELECT COUNT(*) FROM clients;"
```

---

## Quick Reference

### Most Common Commands

```bash
# Start everything
docker compose up -d

# View logs
docker compose logs -f backend

# Access database
docker compose exec postgres psql -U postgres -d postgres

# Access backend shell
docker compose exec backend bash

# Restart a service
docker compose restart backend

# Backup database
docker compose exec postgres pg_dump -U postgres postgres > backup.sql

# Restore database
docker compose exec -T postgres psql -U postgres -d postgres < backup.sql
```

### Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Backend Health**: http://localhost:8000/health
- **PostgreSQL**: localhost:5432

### Container Names

- **Backend**: `mcraes-backend`
- **Frontend**: `mcraes-frontend`
- **PostgreSQL**: `mcraes-postgres`

### Volume Names

- **PostgreSQL Data**: `mcraes_website_analytics_postgres_data`

---

## Notes

- All commands should be run from the project root directory (where `docker-compose.yml` is located)
- Use `docker compose` (with space) for newer Docker Compose versions, or `docker-compose` (with hyphen) for older versions
- Database password is `postgres` by default (check `docker-compose.yml` for actual value)
- Always backup before running destructive operations
- Use `-T` flag with `exec` when piping input to avoid TTY allocation issues

---

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

