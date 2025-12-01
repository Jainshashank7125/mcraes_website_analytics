# Database Migration Guide: Supabase → Local PostgreSQL

## Overview

This guide helps you migrate from Supabase (free plan) to a local PostgreSQL database to improve performance and reduce latency.

## Why Migrate?

**Supabase Free Plan Limitations:**
- Shared infrastructure (slower performance)
- Network latency (data travels over internet)
- Limited connections and resources
- Rate limiting

**Local PostgreSQL Benefits:**
- ⚡ **10-100x faster** (no network latency)
- 💰 **Free** (no upgrade costs)
- 🔒 **Full control** (your data, your server)
- 📈 **Better performance** (dedicated resources)

## Migration Strategy

### Option 1: Hybrid Approach (Recommended)
- **Local PostgreSQL** for all database operations (fast)
- **Keep Supabase** only for authentication (minimal changes)

### Option 2: Full Migration
- **Local PostgreSQL** for everything
- **Custom auth** implementation (more work)

## Step-by-Step Migration

### 1. Start Local PostgreSQL

The `docker-compose.yml` has been updated to include a PostgreSQL container:

```bash
cd /root/mcraes_website_analytics
docker compose up -d postgres
```

### 2. Export Data from Supabase

**Option A: Using Supabase REST API (via Python)**
```bash
docker compose exec backend python << EOF
from app.services.supabase_service import SupabaseService
import json

supabase = SupabaseService()

# Export each table
tables = ['brands', 'prompts', 'responses', 'ga4_tokens', 'sync_jobs', 'audit_logs']
for table in tables:
    try:
        data = supabase.client.table(table).select('*').execute().data
        with open(f'{table}_export.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Exported {len(data)} records from {table}")
    except Exception as e:
        print(f"⚠️  Could not export {table}: {e}")
EOF
```

**Option B: Using pg_dump (if you have direct access)**
```bash
pg_dump -h <supabase-host> -U postgres -d postgres > supabase_backup.sql
```

### 3. Run Migrations

Create all tables in local PostgreSQL:

```bash
# Run all migration files
for migration in migrations/v*.sql; do
    echo "Running $migration..."
    docker compose exec -T postgres psql -U postgres -d postgres < "$migration"
done
```

Or use the migration script:
```bash
./migrate_to_local_db.sh
```

### 4. Import Data

If you have a SQL backup:
```bash
docker compose exec -T postgres psql -U postgres -d postgres < supabase_backup.sql
```

Or import JSON exports:
```bash
docker compose exec backend python << EOF
# Import logic here
EOF
```

### 5. Update Environment Variables

Update your `.env` file:

```env
# Keep Supabase for Auth only
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Local PostgreSQL (for database operations)
SUPABASE_DB_HOST=postgres
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your_secure_password
```

**Important:** Change the default password in docker-compose.yml!

### 6. Restart Services

```bash
docker compose restart backend
docker compose logs -f backend
```

### 7. Verify Migration

```bash
# Check database connection
docker compose exec backend python -c "
from app.db.database import check_db_connection
check_db_connection()
"

# Test a query
docker compose exec backend python -c "
from app.db.database import get_db
from app.db.models import Brand
db = next(get_db())
brands = db.query(Brand).limit(5).all()
print(f'Found {len(brands)} brands')
"
```

## Performance Comparison

| Operation | Supabase (Free) | Local PostgreSQL |
|-----------|----------------|-----------------|
| Simple Query | 50-200ms | 1-5ms |
| Complex Query | 200-500ms | 5-20ms |
| Bulk Insert | 500-2000ms | 20-100ms |
| Connection Time | 100-300ms | <1ms |

**Expected improvement: 10-50x faster!**

## Backup Strategy

### Automated Backups

Create a backup script:

```bash
#!/bin/bash
# backup_db.sh
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U postgres postgres | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"
# Keep only last 7 days
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /root/mcraes_website_analytics/backup_db.sh
```

### Manual Backup

```bash
docker compose exec postgres pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql
```

## Rollback Plan

If you need to rollback:

1. Keep Supabase connection details in `.env.backup`
2. Revert environment variables
3. Restart backend: `docker compose restart backend`

## Troubleshooting

### Connection Issues

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Test connection
docker compose exec postgres psql -U postgres -d postgres -c "SELECT version();"
```

### Performance Issues

```bash
# Check database size
docker compose exec postgres psql -U postgres -d postgres -c "SELECT pg_size_pretty(pg_database_size('postgres'));"

# Check active connections
docker compose exec postgres psql -U postgres -d postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

## Security Considerations

1. **Change default password** in docker-compose.yml
2. **Use strong password** for POSTGRES_PASSWORD
3. **Backup regularly** (automated daily backups)
4. **Restrict access** (PostgreSQL only accessible from backend container)
5. **Monitor logs** for suspicious activity

## Maintenance

### Update PostgreSQL

```bash
docker compose pull postgres
docker compose up -d postgres
```

### Vacuum Database (optimize)

```bash
docker compose exec postgres psql -U postgres -d postgres -c "VACUUM ANALYZE;"
```

## Next Steps

1. ✅ Set up local PostgreSQL
2. ✅ Export data from Supabase
3. ✅ Run migrations
4. ✅ Import data
5. ✅ Update environment variables
6. ✅ Test application
7. ✅ Set up automated backups
8. ✅ Monitor performance

## Support

If you encounter issues:
- Check logs: `docker compose logs postgres backend`
- Verify connection: Test database queries
- Check environment variables: Ensure all settings are correct

