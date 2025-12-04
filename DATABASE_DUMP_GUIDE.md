# Database Dump and Restore Guide

This guide explains how to create a complete database dump (schema + data) and restore it to production.

## Creating a Database Dump

### Option 1: Using the Script (Recommended)

```bash
# Create dump using the provided script
./scripts/create_database_dump.sh
```

The dump will be saved to `./dumps/mcraes_full_dump_YYYYMMDD_HHMMSS.dump`

### Option 2: Manual Command (Docker)

```bash
# Create dump from Docker container
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --no-owner \
    --no-acl \
    --blobs \
    --encoding=UTF8 \
    > dumps/mcraes_full_dump_$(date +%Y%m%d_%H%M%S).dump
```

### Option 3: Manual Command (Direct PostgreSQL)

```bash
# If connecting directly to PostgreSQL (not in Docker)
pg_dump \
    -U postgres \
    -d postgres \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --no-owner \
    --no-acl \
    --blobs \
    --encoding=UTF8 \
    -f dumps/mcraes_full_dump_$(date +%Y%m%d_%H%M%S).dump
```

### Dump Flags Explained

- `--verbose`: Show detailed progress
- `--clean`: Include DROP statements to clean existing objects
- `--if-exists`: Use IF EXISTS for DROP statements (safer)
- `--create`: Include CREATE DATABASE statement
- `--format=custom`: Custom format (compressed, faster restore)
- `--no-owner`: Don't restore ownership (use current user)
- `--no-acl`: Don't restore access privileges (grants)
- `--blobs`: Include large objects (BLOBs)
- `--encoding=UTF8`: Set encoding explicitly

## Restoring to Production

### Option 1: Using the Script (Recommended)

```bash
# Restore to local database
./scripts/restore_database_dump.sh dumps/mcraes_full_dump_20251204_120000.dump

# Restore to remote production database
./scripts/restore_database_dump.sh \
    dumps/mcraes_full_dump_20251204_120000.dump \
    production_db_name \
    postgres \
    production.example.com \
    5432
```

### Option 2: Manual Command (Local)

```bash
# Restore to local database
pg_restore \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --no-owner \
    --no-acl \
    --dbname=postgres \
    --host=localhost \
    --port=5432 \
    --username=postgres \
    dumps/mcraes_full_dump_20251204_120000.dump
```

### Option 3: Manual Command (Remote Production)

```bash
# Restore to remote production database
pg_restore \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --no-owner \
    --no-acl \
    --dbname=your_production_db \
    --host=your-production-host.com \
    --port=5432 \
    --username=postgres \
    dumps/mcraes_full_dump_20251204_120000.dump
```

### Option 4: Using psql (Plain SQL Format)

If you need a plain SQL dump instead of custom format:

```bash
# Create plain SQL dump
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    --clean \
    --if-exists \
    --create \
    --no-owner \
    --no-acl \
    --encoding=UTF8 \
    > dumps/mcraes_full_dump_$(date +%Y%m%d_%H%M%S).sql

# Restore plain SQL dump
psql -U postgres -h localhost -d postgres < dumps/mcraes_full_dump_20251204_120000.sql
```

## Production Restore Checklist

Before restoring to production:

1. **Backup Production Database First**
   ```bash
   # Create backup of current production database
   pg_dump -U postgres -d production_db --format=custom > production_backup_$(date +%Y%m%d_%H%M%S).dump
   ```

2. **Verify Dump File**
   ```bash
   # Check dump file size and integrity
   ls -lh dumps/mcraes_full_dump_*.dump
   pg_restore --list dumps/mcraes_full_dump_*.dump | head -20
   ```

3. **Test Restore on Staging First**
   ```bash
   # Always test on staging before production
   ./scripts/restore_database_dump.sh dumps/mcraes_full_dump_*.dump staging_db
   ```

4. **Schedule Maintenance Window**
   - Notify users of downtime
   - Plan for rollback if needed

5. **Restore to Production**
   ```bash
   # Restore during maintenance window
   ./scripts/restore_database_dump.sh \
       dumps/mcraes_full_dump_*.dump \
       production_db \
       postgres \
       production-host.com \
       5432
   ```

6. **Verify After Restore**
   ```bash
   # Connect to production and verify
   psql -U postgres -h production-host.com -d production_db
   
   # Check table counts
   SELECT schemaname, tablename, n_tup_ins as row_count 
   FROM pg_stat_user_tables 
   ORDER BY schemaname, tablename;
   
   # Check specific tables
   SELECT COUNT(*) FROM clients;
   SELECT COUNT(*) FROM brands;
   SELECT COUNT(*) FROM brand_kpi_selections;
   ```

## Troubleshooting

### Error: "database already exists"
The dump includes `CREATE DATABASE`, so if the database exists, you may need to:
```bash
# Drop existing database first (CAREFUL!)
psql -U postgres -h host -c "DROP DATABASE IF EXISTS production_db;"
```

### Error: "permission denied"
Make sure the user has proper permissions:
```bash
# Grant necessary permissions
psql -U postgres -h host -c "GRANT ALL PRIVILEGES ON DATABASE production_db TO postgres;"
```

### Error: "connection refused"
Check network connectivity and firewall:
```bash
# Test connection
psql -U postgres -h production-host.com -p 5432 -d postgres -c "SELECT version();"
```

### Large Database Performance
For very large databases, consider:
- Using `--jobs` flag for parallel restore (pg_restore only)
- Restoring during off-peak hours
- Using `--single-transaction` for plain SQL format

```bash
# Parallel restore (faster for large databases)
pg_restore \
    --jobs=4 \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --no-owner \
    --no-acl \
    --dbname=production_db \
    --host=production-host.com \
    --username=postgres \
    dumps/mcraes_full_dump_*.dump
```

## File Locations

- **Dump files**: `./dumps/`
- **Scripts**: `./scripts/create_database_dump.sh` and `./scripts/restore_database_dump.sh`
- **This guide**: `./DATABASE_DUMP_GUIDE.md`

## Quick Reference

```bash
# Create dump
./scripts/create_database_dump.sh

# Restore to local
./scripts/restore_database_dump.sh dumps/mcraes_full_dump_*.dump

# Restore to production
./scripts/restore_database_dump.sh dumps/mcraes_full_dump_*.dump prod_db postgres prod-host.com 5432
```

