from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.db.models import Base
import logging
import os

logger = logging.getLogger(__name__)

# Log database configuration for debugging
db_host = settings.SUPABASE_DB_HOST or os.getenv("SUPABASE_DB_HOST", "NOT SET")
logger.info(f"Database configuration - Host: {db_host}, Port: {settings.SUPABASE_DB_PORT}, Database: {settings.SUPABASE_DB_NAME}")

# Warn if connecting to Supabase instead of local PostgreSQL
if db_host and "supabase.co" in db_host:
    logger.warning(
        f"⚠️  WARNING: Connecting to Supabase ({db_host}) instead of local PostgreSQL. "
        f"Set SUPABASE_DB_HOST=postgres in environment variables or docker-compose.yml to use local PostgreSQL."
    )
elif db_host == "postgres" or db_host == "localhost" or db_host == "127.0.0.1":
    logger.info(f"✅ Using local PostgreSQL database at {db_host}")

# Get database URL and log it (for debugging)
try:
    database_url = settings.database_url
    # Log safe URL (without password)
    safe_url = database_url.split("@")[1] if "@" in database_url else database_url
    logger.info(f"Creating database engine with URL: postgresql://***@{safe_url}")
    
    # Double-check the host in the URL
    if "supabase.co" in database_url:
        logger.error(
            f"❌ ERROR: Database URL contains Supabase host! URL: postgresql://***@{safe_url}\n"
            f"   This means SUPABASE_DB_HOST in .env file is overriding docker-compose.yml.\n"
            f"   Current SUPABASE_DB_HOST value: {settings.SUPABASE_DB_HOST}\n"
            f"   Environment variable SUPABASE_DB_HOST: {os.getenv('SUPABASE_DB_HOST', 'NOT SET')}"
        )
        raise ValueError(
            "Database URL is pointing to Supabase instead of local PostgreSQL. "
            "Please update .env file or ensure SUPABASE_DB_HOST=postgres is set in environment variables."
        )
except Exception as e:
    logger.error(f"Failed to get database URL: {e}")
    raise

# Create database engine with optimized connection pooling for low latency
# Note: For Supabase, if IPv6 causes issues, you might need to use IPv4 or connection pooler
engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=20,  # Increased from 5 to 20 for better concurrency
    max_overflow=30,  # Increased from 10 to 30 for peak loads
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
    pool_reset_on_return='commit',  # Reset connections on return for better performance
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    connect_args={
        "connect_timeout": 10,  # 10 second timeout
        "application_name": "mcraes_analytics",  # Help identify connections in pg_stat_activity
        # Force IPv4 if IPv6 causes issues
        # "host": "db.dvmakvtrtjvffceujlfm.supabase.co",
    },
    # Optimize for read-heavy workloads
    execution_options={
        "isolation_level": "READ COMMITTED",  # Default, but explicit for clarity
        "autocommit": False
    }
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency function to get database session.
    Use this in FastAPI route dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    This should be run after migrations for production.
    """
    from sqlalchemy import text
    try:
        # Test connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        
        # Create all tables (use Alembic migrations for production)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection is successful, False otherwise.
    """
    from sqlalchemy import text
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection check: SUCCESS")
        return True
    except Exception as e:
        logger.error(f"Database connection check: FAILED - {e}")
        return False

