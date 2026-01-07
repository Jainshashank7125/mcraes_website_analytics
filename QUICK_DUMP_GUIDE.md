# Quick Guide: Create Database Dump from Docker PostgreSQL

## Recommended Method (Custom Format)

### Step 1: Create the Dump
```bash
# Create dump directory if it doesn't exist
mkdir -p dumps

# Create dump in custom format (RECOMMENDED - handles JSON/data better)
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
```

### Step 2: Restore Locally
```bash
# Restore the dump to your local database
docker compose exec -T postgres pg_restore \
    -U postgres \
    -d postgres \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    < dumps/backup_YYYYMMDD_HHMMSS.dump
```

## Alternative: Using the Script

### Create Dump
```bash
./scripts/create_database_dump.sh
```
This will create: `./dumps/mcraes_full_dump_YYYYMMDD_HHMMSS.dump`

### Restore Dump
```bash
./scripts/restore_database_dump.sh dumps/mcraes_full_dump_YYYYMMDD_HHMMSS.dump
```

## Plain SQL Format (Alternative)

### Create SQL Dump
```bash
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --encoding=UTF8 \
    > dumps/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore SQL Dump
```bash
docker compose exec -T postgres psql \
    -U postgres \
    -d postgres \
    < dumps/backup_YYYYMMDD_HHMMSS.sql
```

## Why Custom Format is Recommended

✅ **Better JSON/JSONB handling** - Avoids errors with complex JSON data  
✅ **Compressed** - Smaller file sizes  
✅ **Faster restore** - More efficient than plain SQL  
✅ **Selective restore** - Can restore specific tables if needed  
✅ **More reliable** - Handles special characters and data types better  

## Quick Commands

```bash
# Create dump (one-liner)
mkdir -p dumps && docker compose exec -T postgres pg_dump -U postgres -d postgres --format=custom --clean --if-exists --no-owner --no-acl --blobs --encoding=UTF8 > dumps/backup_$(date +%Y%m%d_%H%M%S).dump

# List recent dumps
ls -lh dumps/*.dump | tail -5

# Restore latest dump
LATEST_DUMP=$(ls -t dumps/*.dump | head -1) && docker compose exec -T postgres pg_restore -U postgres -d postgres --clean --if-exists --no-owner --no-acl < "$LATEST_DUMP"
```

## Troubleshooting

### If you get "permission denied" errors:
```bash
# Make sure dumps directory exists and is writable
mkdir -p dumps
chmod 755 dumps
```

### If restore fails with "database already exists":
```bash
# Drop and recreate (CAREFUL - this deletes existing data!)
docker compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS postgres;"
docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE postgres;"
```

### Check dump file integrity:
```bash
# List contents of dump file
docker compose exec -T postgres pg_restore --list dumps/backup_file.dump | head -20
```

