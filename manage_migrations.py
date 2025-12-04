#!/usr/bin/env python3
"""
Migration Manager - Django-like migration system for PostgreSQL

Usage:
    python manage_migrations.py migrate          # Run all pending migrations
    python manage_migrations.py migrate --fake   # Mark migrations as run without executing
    python manage_migrations.py showmigrations   # Show migration status
    python manage_migrations.py migrate <name>  # Run specific migration
"""

import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, get_db_url

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations similar to Django's migration system"""
    
    def __init__(self, db: Session):
        self.db = db
        self.migrations_dir = Path(__file__).parent / "migrations"
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        try:
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS django_migrations (
                    id SERIAL PRIMARY KEY,
                    app VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    applied TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    UNIQUE(app, name)
                );
            """))
            self.db.commit()
            logger.info("Migrations table ready")
        except Exception as e:
            logger.error(f"Error creating migrations table: {str(e)}")
            self.db.rollback()
            raise
    
    def _get_migration_files(self) -> List[Tuple[str, Path, int]]:
        """
        Get all migration files sorted by version number.
        Returns: List of (migration_name, file_path, version_number) tuples
        """
        migrations = []
        
        # Get root level migrations (v{N}__description.sql)
        root_pattern = re.compile(r'^v(\d+)__(.+)\.sql$')
        for file in self.migrations_dir.glob('v*__*.sql'):
            match = root_pattern.match(file.name)
            if match:
                version = int(match.group(1))
                name = file.name
                migrations.append((name, file, version))
        
        # Get v2/ directory migrations ({N}__description.sql)
        v2_dir = self.migrations_dir / "v2"
        if v2_dir.exists():
            v2_pattern = re.compile(r'^(\d+)_(.+)\.sql$')
            for file in v2_dir.glob('*__*.sql'):
                match = v2_pattern.match(file.name)
                if match:
                    # Use 2000 + number to ensure v2 migrations come after v20
                    version = 2000 + int(match.group(1))
                    name = f"v2/{file.name}"
                    migrations.append((name, file, version))
        
        # Sort by version number
        migrations.sort(key=lambda x: x[2])
        return migrations
    
    def _get_applied_migrations(self) -> set:
        """Get set of applied migration names"""
        try:
            result = self.db.execute(text("""
                SELECT app, name FROM django_migrations
            """))
            applied = set()
            for row in result:
                # Store as "app/name" or just "name" for root migrations
                if row[0] == "root":
                    applied.add(row[1])
                else:
                    applied.add(f"{row[0]}/{row[1]}")
            return applied
        except Exception as e:
            logger.error(f"Error getting applied migrations: {str(e)}")
            return set()
    
    def _record_migration(self, app: str, name: str):
        """Record that a migration has been applied"""
        try:
            self.db.execute(text("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES (:app, :name, NOW())
                ON CONFLICT (app, name) DO NOTHING
            """), {"app": app, "name": name})
            self.db.commit()
        except Exception as e:
            logger.error(f"Error recording migration: {str(e)}")
            self.db.rollback()
            raise
    
    def _run_migration_file(self, file_path: Path) -> bool:
        """Execute a migration SQL file"""
        try:
            logger.info(f"Reading migration file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # PostgreSQL can execute multiple statements in one go
            # Just execute the entire file content
            if sql_content.strip():
                logger.debug(f"Executing migration file: {file_path.name}")
                self.db.execute(text(sql_content))
                self.db.commit()
                logger.info(f"Successfully executed migration: {file_path.name}")
                return True
            else:
                logger.warning(f"Migration file is empty: {file_path.name}")
                return True
            
        except Exception as e:
            logger.error(f"Error running migration {file_path}: {str(e)}")
            self.db.rollback()
            return False
    
    def show_migrations(self):
        """Show migration status (like Django's showmigrations)"""
        migrations = self._get_migration_files()
        applied = self._get_applied_migrations()
        
        print("\nMigration Status:")
        print("=" * 80)
        print(f"{'App':<10} {'Migration Name':<50} {'Status':<10} {'Version':<10}")
        print("-" * 80)
        
        for name, file_path, version in migrations:
            # Determine app
            if name.startswith("v2/"):
                app = "v2"
                migration_name = name.replace("v2/", "")
            else:
                app = "root"
                migration_name = name
            
            # Check if applied
            if name in applied:
                status = "[X]"
            else:
                status = "[ ]"
            
            print(f"{app:<10} {migration_name:<50} {status:<10} {version:<10}")
        
        print("=" * 80)
        print(f"Total migrations: {len(migrations)}")
        print(f"Applied: {len(applied)}")
        print(f"Pending: {len(migrations) - len(applied)}")
    
    def migrate(self, migration_name: Optional[str] = None, fake: bool = False):
        """
        Run migrations.
        
        Args:
            migration_name: Specific migration to run (optional)
            fake: If True, mark as applied without running
        """
        migrations = self._get_migration_files()
        applied = self._get_applied_migrations()
        
        if migration_name:
            # Run specific migration
            target_migrations = [m for m in migrations if migration_name in m[0]]
            if not target_migrations:
                logger.error(f"Migration '{migration_name}' not found")
                return False
        else:
            # Run all pending migrations
            target_migrations = [m for m in migrations if m[0] not in applied]
        
        if not target_migrations:
            logger.info("No migrations to apply")
            return True
        
        logger.info(f"Found {len(target_migrations)} migration(s) to apply")
        
        for name, file_path, version in target_migrations:
            # Determine app
            if name.startswith("v2/"):
                app = "v2"
                migration_name_only = name.replace("v2/", "")
            else:
                app = "root"
                migration_name_only = name
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Applying migration: {name} (version {version})")
            logger.info(f"{'='*80}")
            
            if fake:
                logger.info(f"[FAKE] Marking {name} as applied without executing")
                self._record_migration(app, migration_name_only)
            else:
                if self._run_migration_file(file_path):
                    self._record_migration(app, migration_name_only)
                    logger.info(f"✓ Migration {name} applied successfully")
                else:
                    logger.error(f"✗ Migration {name} failed")
                    return False
        
        logger.info("\n" + "="*80)
        logger.info("All migrations completed successfully!")
        return True


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    db = SessionLocal()
    
    try:
        manager = MigrationManager(db)
        
        if command == "migrate":
            migration_name = sys.argv[2] if len(sys.argv) > 2 else None
            fake = "--fake" in sys.argv or "-f" in sys.argv
            success = manager.migrate(migration_name, fake=fake)
            sys.exit(0 if success else 1)
        
        elif command == "showmigrations":
            manager.show_migrations()
            sys.exit(0)
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

