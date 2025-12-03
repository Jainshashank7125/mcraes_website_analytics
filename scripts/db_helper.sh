#!/bin/bash
# =====================================================
# Database Management Helper Script
# =====================================================
# This script provides common database management commands
# for the local PostgreSQL database running in Docker
# =====================================================

set -e

# Configuration
DB_CONTAINER="mcraes-postgres"
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="postgres"
MIGRATIONS_DIR="migrations"
V1_MIGRATIONS_DIR="$MIGRATIONS_DIR/v1"
V2_MIGRATIONS_DIR="$MIGRATIONS_DIR/v2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to check if container is running
check_container() {
    if ! docker ps | grep -q "$DB_CONTAINER"; then
        echo -e "${RED}Error: Container '$DB_CONTAINER' is not running${NC}"
        echo "Start it with: docker compose up -d postgres"
        exit 1
    fi
}

# Helper function to execute SQL
execute_sql() {
    local sql="$1"
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<EOF
$sql
EOF
}

# Helper function to execute SQL file
execute_sql_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: File '$file' not found${NC}"
        return 1
    fi
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$file"
}

# Show usage
show_usage() {
    echo -e "${BLUE}Database Management Helper${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  migrate-v1              Run all v1 migrations (complete_schema.sql)"
    echo "  migrate-v2              Run all v2 migrations"
    echo "  migrate-v2-file <file>  Run a specific v2 migration file"
    echo "  drop-db                 Drop and recreate the database"
    echo "  reset-db                Drop database, recreate, and run all migrations"
    echo "  list-tables             List all tables in the database"
    echo "  describe-table <table>  Show table structure"
    echo "  select <table>          Select all rows from a table (limit 100)"
    echo "  select <table> <limit>  Select rows with custom limit"
    echo "  count <table>           Count rows in a table"
    echo "  query <sql>             Execute custom SQL query"
    echo "  backup                  Create a database backup"
    echo "  restore <file>          Restore database from backup"
    echo "  psql                    Open interactive psql session"
    echo "  help                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 migrate-v2"
    echo "  $0 select users"
    echo "  $0 select agency_analytics_campaigns 10"
    echo "  $0 count refresh_tokens"
    echo "  $0 query \"SELECT id, email FROM users LIMIT 5\""
    echo "  $0 describe-table brands"
}

# Run v1 migrations
migrate_v1() {
    echo -e "${BLUE}Running v1 migrations...${NC}"
    check_container
    
    local schema_file="$V1_MIGRATIONS_DIR/complete_schema.sql"
    if [ ! -f "$schema_file" ]; then
        echo -e "${RED}Error: Schema file '$schema_file' not found${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Executing: $schema_file${NC}"
    execute_sql_file "$schema_file"
    echo -e "${GREEN}✓ V1 migrations completed${NC}"
}

# Run v2 migrations
migrate_v2() {
    echo -e "${BLUE}Running v2 migrations...${NC}"
    check_container
    
    if [ ! -d "$V2_MIGRATIONS_DIR" ]; then
        echo -e "${RED}Error: V2 migrations directory not found${NC}"
        return 1
    fi
    
    # Get all SQL files in v2 directory, sorted
    local files=$(find "$V2_MIGRATIONS_DIR" -name "*.sql" | sort)
    
    if [ -z "$files" ]; then
        echo -e "${YELLOW}No migration files found in $V2_MIGRATIONS_DIR${NC}"
        return 0
    fi
    
    for file in $files; do
        echo -e "${YELLOW}Executing: $file${NC}"
        execute_sql_file "$file"
        echo -e "${GREEN}✓ Completed: $(basename $file)${NC}"
    done
    
    echo -e "${GREEN}✓ All v2 migrations completed${NC}"
}

# Run specific v2 migration file
migrate_v2_file() {
    local file="$1"
    if [ -z "$file" ]; then
        echo -e "${RED}Error: Please specify a migration file${NC}"
        echo "Usage: $0 migrate-v2-file <file>"
        return 1
    fi
    
    # If file doesn't have path, assume it's in v2 directory
    if [[ ! "$file" == *"/"* ]]; then
        file="$V2_MIGRATIONS_DIR/$file"
    fi
    
    echo -e "${BLUE}Running migration: $file${NC}"
    check_container
    execute_sql_file "$file"
    echo -e "${GREEN}✓ Migration completed${NC}"
}

# Drop and recreate database
drop_db() {
    echo -e "${YELLOW}WARNING: This will drop the database and all its data!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled"
        return 0
    fi
    
    check_container
    
    echo -e "${BLUE}Dropping database...${NC}"
    execute_sql "DROP DATABASE IF EXISTS $DB_NAME;"
    
    echo -e "${BLUE}Creating database...${NC}"
    execute_sql "CREATE DATABASE $DB_NAME;"
    
    echo -e "${GREEN}✓ Database recreated${NC}"
}

# Reset database (drop, recreate, migrate)
reset_db() {
    echo -e "${YELLOW}WARNING: This will drop the database, recreate it, and run all migrations!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled"
        return 0
    fi
    
    drop_db
    migrate_v1
    migrate_v2
    echo -e "${GREEN}✓ Database reset complete${NC}"
}

# List all tables
list_tables() {
    check_container
    echo -e "${BLUE}Tables in database '$DB_NAME':${NC}"
    execute_sql "\dt"
}

# Describe table structure
describe_table() {
    local table="$1"
    if [ -z "$table" ]; then
        echo -e "${RED}Error: Please specify a table name${NC}"
        echo "Usage: $0 describe-table <table>"
        return 1
    fi
    
    check_container
    echo -e "${BLUE}Structure of table '$table':${NC}"
    execute_sql "\d $table"
}

# Select from table
select_table() {
    local table="$1"
    local limit="${2:-100}"
    
    if [ -z "$table" ]; then
        echo -e "${RED}Error: Please specify a table name${NC}"
        echo "Usage: $0 select <table> [limit]"
        return 1
    fi
    
    check_container
    echo -e "${BLUE}Selecting from table '$table' (limit: $limit):${NC}"
    execute_sql "SELECT * FROM $table LIMIT $limit;"
}

# Count rows in table
count_table() {
    local table="$1"
    if [ -z "$table" ]; then
        echo -e "${RED}Error: Please specify a table name${NC}"
        echo "Usage: $0 count <table>"
        return 1
    fi
    
    check_container
    echo -e "${BLUE}Row count for table '$table':${NC}"
    execute_sql "SELECT COUNT(*) as count FROM $table;"
}

# Execute custom SQL query
execute_query() {
    local query="$1"
    if [ -z "$query" ]; then
        echo -e "${RED}Error: Please provide a SQL query${NC}"
        echo "Usage: $0 query \"<sql query>\""
        return 1
    fi
    
    check_container
    echo -e "${BLUE}Executing query:${NC}"
    echo -e "${YELLOW}$query${NC}"
    execute_sql "$query"
}

# Backup database
backup_db() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    check_container
    
    echo -e "${BLUE}Creating backup: $backup_file${NC}"
    docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" > "$backup_file"
    echo -e "${GREEN}✓ Backup created: $backup_file${NC}"
}

# Restore database from backup
restore_db() {
    local backup_file="$1"
    if [ -z "$backup_file" ]; then
        echo -e "${RED}Error: Please specify a backup file${NC}"
        echo "Usage: $0 restore <backup_file>"
        return 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}Error: Backup file '$backup_file' not found${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}WARNING: This will restore the database from backup!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled"
        return 0
    fi
    
    check_container
    echo -e "${BLUE}Restoring from: $backup_file${NC}"
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$backup_file"
    echo -e "${GREEN}✓ Database restored${NC}"
}

# Open interactive psql session
open_psql() {
    check_container
    echo -e "${BLUE}Opening interactive psql session...${NC}"
    echo -e "${YELLOW}Type '\\q' to exit${NC}"
    docker exec -it "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"
}

# Main command handler
main() {
    local command="${1:-help}"
    
    case "$command" in
        migrate-v1)
            migrate_v1
            ;;
        migrate-v2)
            migrate_v2
            ;;
        migrate-v2-file)
            migrate_v2_file "$2"
            ;;
        drop-db)
            drop_db
            ;;
        reset-db)
            reset_db
            ;;
        list-tables)
            list_tables
            ;;
        describe-table)
            describe_table "$2"
            ;;
        select)
            select_table "$2" "$3"
            ;;
        count)
            count_table "$2"
            ;;
        query)
            execute_query "$2"
            ;;
        backup)
            backup_db
            ;;
        restore)
            restore_db "$2"
            ;;
        psql)
            open_psql
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

