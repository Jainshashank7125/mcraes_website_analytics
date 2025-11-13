from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

supabase: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global supabase
    if supabase is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be set in environment variables")
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized")
    return supabase

def init_db():
    """Initialize database tables if they don't exist"""
    # Note: Supabase tables should be created manually in Supabase dashboard
    # or via migrations. This function can be used to verify connection.
    try:
        client = get_supabase_client()
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

