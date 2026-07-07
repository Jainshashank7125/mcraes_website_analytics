from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, Table, MetaData, select, update, insert, delete, and_, or_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.database import get_db
from app.db.models import Brand, Prompt, Response, Citation, AuditLog, Client, DashboardLink
from app.core.database import get_supabase_client
import logging
import re
import threading
import unicodedata
import uuid
from urllib.parse import urlparse
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)

_GLOBAL_TABLE_CACHE: dict = {}
_TABLE_CACHE_LOCK = threading.Lock()


class BaseDB:
    """Base database class with constructor and all private helpers"""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize service with database session.
        If db is None, will get a new session (for backward compatibility).
        """
        if db is None:
            # Get a new session for backward compatibility
            self.db = next(get_db())
            self._close_db = True
        else:
            self.db = db
            self._close_db = False
        self._supabase_client = None  # Lazy-loaded for backward compatibility

    @property
    def client(self):
        """
        DEPRECATED: Supabase REST API client for backward compatibility.
        This property is kept for methods that haven't been migrated to SQLAlchemy yet.
        New code should use SQLAlchemy methods directly.
        """
        if self._supabase_client is None:
            logger.warning(
                "Using deprecated Supabase REST API client. "
                "This method should be migrated to use SQLAlchemy. "
                "The Supabase client is only kept for backward compatibility during migration."
            )
            try:
                self._supabase_client = get_supabase_client()
            except Exception as e:
                logger.error(f"Failed to create Supabase client for backward compatibility: {e}")
                raise
        return self._supabase_client

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._close_db:
            self.db.close()

    def _execute_text(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute raw SQL query"""
        return self.db.execute(text(query), params or {})

    def _get_table(self, table_name: str) -> Table:
        """Get table object using reflection (process-level cache; reflects once per table per process)"""
        if table_name not in _GLOBAL_TABLE_CACHE:
            with _TABLE_CACHE_LOCK:
                if table_name not in _GLOBAL_TABLE_CACHE:
                    metadata = MetaData()
                    metadata.reflect(bind=self.db.bind, only=[table_name])
                    _GLOBAL_TABLE_CACHE[table_name] = metadata.tables[table_name]
        return _GLOBAL_TABLE_CACHE[table_name]

    def _table_select(self, table_name: str, filters: Optional[Dict] = None, limit: Optional[int] = None, offset: Optional[int] = None, order_by: Optional[str] = None, desc: bool = False) -> List[Dict]:
        """Helper method to select from any table using SQLAlchemy Core"""
        try:
            table = self._get_table(table_name)
            query = select(table)

            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if value is not None:
                        conditions.append(table.c[key] == value)
                if conditions:
                    query = query.where(and_(*conditions))

            # Apply ordering
            if order_by:
                col = table.c[order_by]
                query = query.order_by(col.desc() if desc else col.asc())

            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            result = self.db.execute(query)
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error selecting from {table_name}: {str(e)}")
            raise

    def _table_insert(self, table_name: str, records: List[Dict], on_conflict: Optional[str] = None) -> int:
        """Helper method to insert into any table using SQLAlchemy Core"""
        try:
            if not records:
                return 0

            table = self._get_table(table_name)

            # Use PostgreSQL INSERT ... ON CONFLICT if specified
            if on_conflict:
                # This is a simplified version - for complex cases, use raw SQL
                stmt = pg_insert(table).values(records)
                stmt = stmt.on_conflict_do_update(set_=records[0])
                result = self.db.execute(stmt)
            else:
                stmt = insert(table).values(records)
                result = self.db.execute(stmt)

            self.db.commit()
            return len(records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error inserting into {table_name}: {str(e)}")
            raise

    def _table_update(self, table_name: str, data: Dict, filters: Dict) -> int:
        """Helper method to update any table using SQLAlchemy Core"""
        try:
            table = self._get_table(table_name)
            conditions = [table.c[key] == value for key, value in filters.items()]
            stmt = update(table).where(and_(*conditions)).values(**data)
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {table_name}: {str(e)}")
            raise

    def _table_delete(self, table_name: str, filters: Dict) -> int:
        """Helper method to delete from any table using SQLAlchemy Core"""
        try:
            table = self._get_table(table_name)
            conditions = [table.c[key] == value for key, value in filters.items()]
            stmt = delete(table).where(and_(*conditions))
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting from {table_name}: {str(e)}")
            raise

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats (string, datetime, None)"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Try ISO format first
                if 'T' in value or ' ' in value:
                    # Remove timezone info if present (e.g., '+00:00')
                    value_clean = value.split('+')[0].rstrip()
                    # Try common formats
                    for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(value_clean, fmt)
                        except ValueError:
                            continue
                    # Fallback to dateutil parser if available
                    try:
                        from dateutil import parser
                        return parser.parse(value)
                    except (ImportError, ValueError):
                        pass
                return None
            except Exception:
                return None
        return None
