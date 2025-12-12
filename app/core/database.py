from supabase import create_client, Client
from app.core.config import settings
import logging
import httpx

logger = logging.getLogger(__name__)

supabase: Client = None
supabase_service_role: Client = None

def get_supabase_client() -> Client:
    """
    Get or create Supabase client for AUTHENTICATION ONLY.
    
    NOTE: For database operations, use SQLAlchemy via app.db.database.get_db()
    This client is kept only for Supabase Auth (login, signup, token verification).
    All database read/write operations should use SQLAlchemy with local PostgreSQL.
    """
    global supabase
    if supabase is None:
        url = settings.SUPABASE_URL or ""
        key = settings.SUPABASE_KEY or ""
        
        if not url or not key:
            error_msg = (
                f"Supabase URL and Key must be set for authentication. "
                f"URL: {'SET' if url else 'NOT SET'}, "
                f"KEY: {'SET' if key else 'NOT SET'}. "
                f"Please check your .env file or config.py"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create Supabase client for authentication only
        # Note: The supabase-py library uses httpx internally, but timeout configuration
        # may need to be set via environment variables or client options
        try:
            supabase = create_client(url, key)
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            raise
        logger.info("Supabase client initialized for authentication")
    return supabase

def get_supabase_service_role_client() -> Client:
    """
    Get or create Supabase client with SERVICE ROLE KEY for storage operations.
    
    This client bypasses RLS (Row Level Security) and should ONLY be used for:
    - Storage operations (file uploads/downloads)
    - Admin operations that require elevated permissions
    
    WARNING: Never use this client for user-facing operations or expose it to the frontend.
    """
    global supabase_service_role
    if supabase_service_role is None:
        url = settings.SUPABASE_URL or ""
        key = settings.SUPABASE_SERVICE_ROLE_KEY or ""
        
        if not url or not key:
            error_msg = (
                f"Supabase URL and Service Role Key must be set for storage operations. "
                f"URL: {'SET' if url else 'NOT SET'}, "
                f"SERVICE_ROLE_KEY: {'SET' if key else 'NOT SET'}. "
                f"Please check your .env file or config.py"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            supabase_service_role = create_client(url, key)
        except Exception as e:
            logger.error(f"Failed to create Supabase service role client: {e}")
            raise
        logger.info("Supabase service role client initialized for storage operations")
    return supabase_service_role

def init_db():
    """
    Initialize database tables if they don't exist.
    NOTE: This now uses SQLAlchemy to connect to local PostgreSQL.
    Use app.db.database.init_db() for database initialization.
    """
    # This function is kept for backward compatibility
    # Actual database initialization should use app.db.database.init_db()
    try:
        from app.db.database import init_db as sqlalchemy_init_db
        sqlalchemy_init_db()
        logger.info("Database connection verified via SQLAlchemy")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

