# Database Management Helper Script

A convenient command-line tool for managing the local PostgreSQL database.

## Quick Start

```bash
# Make sure the script is executable
chmod +x scripts/db_helper.sh

# Run any command
./scripts/db_helper.sh [command]
```

## Available Commands

### Migration Commands

#### Run all v2 migrations
```bash
./scripts/db_helper.sh migrate-v2
```

#### Run a specific v2 migration file
```bash
./scripts/db_helper.sh migrate-v2-file 001_users_and_refresh_tokens.sql
```

#### Run v1 migrations (complete schema)
```bash
./scripts/db_helper.sh migrate-v1
```

### Database Management

#### Drop and recreate database
```bash
./scripts/db_helper.sh drop-db
```
⚠️ **Warning**: This will delete all data!

#### Reset database (drop, recreate, and run all migrations)
```bash
./scripts/db_helper.sh reset-db
```
⚠️ **Warning**: This will delete all data and recreate everything!

### Query Commands

#### List all tables
```bash
./scripts/db_helper.sh list-tables
```

#### Show table structure
```bash
./scripts/db_helper.sh describe-table users
./scripts/db_helper.sh describe-table agency_analytics_campaigns
```

#### Select data from a table
```bash
# Default limit: 100 rows
./scripts/db_helper.sh select users

# Custom limit
./scripts/db_helper.sh select agency_analytics_campaigns 10
./scripts/db_helper.sh select refresh_tokens 5
```

#### Count rows in a table
```bash
./scripts/db_helper.sh count users
./scripts/db_helper.sh count agency_analytics_keywords
```

#### Execute custom SQL query
```bash
./scripts/db_helper.sh query "SELECT id, email FROM users LIMIT 5"
./scripts/db_helper.sh query "SELECT COUNT(*) FROM agency_analytics_campaigns"
```

### Backup & Restore

#### Create database backup
```bash
./scripts/db_helper.sh backup
```
Creates a file like: `backup_20241203_143022.sql`

#### Restore from backup
```bash
./scripts/db_helper.sh restore backup_20241203_143022.sql
```
⚠️ **Warning**: This will overwrite current database!

### Interactive Access

#### Open interactive psql session
```bash
./scripts/db_helper.sh psql
```
Type `\q` to exit.

## Examples

### Common Workflows

#### 1. Check if migrations ran successfully
```bash
./scripts/db_helper.sh list-tables
./scripts/db_helper.sh describe-table users
./scripts/db_helper.sh describe-table refresh_tokens
```

#### 2. Verify agency_analytics tables were updated
```bash
./scripts/db_helper.sh describe-table agency_analytics_campaigns
# Check that 'id' column is now BIGINT
```

#### 3. Check user data
```bash
./scripts/db_helper.sh count users
./scripts/db_helper.sh select users
```

#### 4. Check refresh tokens
```bash
./scripts/db_helper.sh count refresh_tokens
./scripts/db_helper.sh select refresh_tokens
```

#### 5. Query specific data
```bash
./scripts/db_helper.sh query "SELECT id, email, created_at FROM users ORDER BY created_at DESC LIMIT 5"
```

## Configuration

The script uses these default settings (from `docker-compose.yml`):
- **Container**: `mcraes-postgres`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: `postgres`

To change these, edit the variables at the top of `scripts/db_helper.sh`.

## Troubleshooting

### Container not running
If you see "Container 'mcraes-postgres' is not running":
```bash
docker compose up -d postgres
```

### Permission denied
```bash
chmod +x scripts/db_helper.sh
```

### Migration file not found
Make sure you're running the script from the project root directory:
```bash
cd /path/to/mcraes_website_analytics
./scripts/db_helper.sh migrate-v2
```

## Notes

- All commands require the PostgreSQL container to be running
- The script uses `docker exec` to run commands inside the container
- SQL files are executed in order (sorted by filename)
- Backup files are created in the current directory

