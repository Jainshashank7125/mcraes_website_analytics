from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # FastAPI Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Scrunch AI API Settings
    SCRUNCH_API_BASE_URL: str = "https://api.scrunchai.com/v1"
    SCRUNCH_API_TOKEN: Optional[str] = None  # Must be set via .env file
    BRAND_ID: int = 3230
    
    # Agency Analytics API Settings
    AGENCY_ANALYTICS_API_KEY: Optional[str] = None  # Can be overridden via .env
    
    # OpenAI API Settings
    OPENAI_API_KEY: Optional[str] = None  # Can be overridden via .env
    
    # Google Analytics 4 API Settings
    GA4_CREDENTIALS_PATH: Optional[str] = None  # Path to service account JSON file
    GA4_SCOPES: list = ["https://www.googleapis.com/auth/analytics.readonly"]
    
    # Supabase Settings (REST API)
    # These must be set via environment variables (.env file)
    SUPABASE_URL: Optional[str] = None  # Must be set via .env file
    SUPABASE_KEY: Optional[str] = None  # Must be set via .env file (anon key)
    # Note: Supabase JWT token expiration duration is configured in Supabase Dashboard
    # Go to: Authentication → Settings → JWT expiry time (default is 3600 seconds / 1 hour)
    
    # Supabase Database Settings
    # Note: Direct connection (db.xxx.supabase.co) is IPv6-only and may not work on Windows
    # Use Session Pooler for IPv4 compatibility: aws-0-<region>.pooler.supabase.com
    # Session Pooler (IPv4 compatible): Port 5432 for session mode
    # Transaction Pooler: Port 6543 for transaction mode
    # Check Supabase dashboard → Settings → Database → Connection Pooling for exact hostname
    # IMPORTANT: Environment variables (from docker-compose.yml) take precedence over .env file
    SUPABASE_DB_HOST: Optional[str] = None  # Set via environment variable or .env file
    SUPABASE_DB_PORT: int = 5432
    # Session Pooler format: aws-0-<region>.pooler.supabase.com:5432 (check your dashboard)
    SUPABASE_DB_NAME: str = "postgres"
    SUPABASE_DB_USER: str = "postgres"
    SUPABASE_DB_PASSWORD: Optional[str] = None  # Set via environment variable or .env file
    
    # For deployment: Use SUPABASE_DB_URL if provided (Railway/Render)
    SUPABASE_DB_URL: Optional[str] = None
    
    # JWT Settings for v2 Authentication
    JWT_SECRET_KEY: Optional[str] = None  # Must be set via environment variable
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 3  # 3 hours TTL for access tokens
    JWT_REFRESH_TOKEN_EXPIRE_HOURS: int = 15  # 15 hours TTL for refresh tokens
    JWT_REFRESH_TOKEN_MAX_USAGE: int = 4  # Maximum usage limit for refresh tokens
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        import logging
        import os
        logger = logging.getLogger(__name__)
        
        # Check if SUPABASE_DB_URL is set (this takes highest priority)
        if self.SUPABASE_DB_URL:
            logger.warning(
                f"⚠️  Using SUPABASE_DB_URL (this overrides SUPABASE_DB_HOST). "
                f"URL host: {self.SUPABASE_DB_URL.split('@')[1].split('/')[0] if '@' in self.SUPABASE_DB_URL else 'unknown'}"
            )
            # Check if it's pointing to Supabase
            if "supabase.co" in self.SUPABASE_DB_URL:
                logger.error(
                    "❌ SUPABASE_DB_URL is set to Supabase! "
                    "Unset SUPABASE_DB_URL environment variable to use local PostgreSQL."
                )
            return self.SUPABASE_DB_URL
        
        # Otherwise, construct from individual components
        # Validate required fields
        if not self.SUPABASE_DB_HOST:
            raise ValueError(
                "SUPABASE_DB_HOST must be set. "
                "For local PostgreSQL, set SUPABASE_DB_HOST=postgres in docker-compose.yml or .env file"
            )
        if not self.SUPABASE_DB_PASSWORD:
            raise ValueError(
                "SUPABASE_DB_PASSWORD must be set. "
                "For local PostgreSQL, set SUPABASE_DB_PASSWORD in docker-compose.yml or .env file"
            )
        
        # Log what values we're using
        logger.info(
            f"Constructing database URL from components - "
            f"Host: {self.SUPABASE_DB_HOST}, "
            f"Port: {self.SUPABASE_DB_PORT}, "
            f"Database: {self.SUPABASE_DB_NAME}, "
            f"User: {self.SUPABASE_DB_USER}"
        )
        
        # Use standard postgresql:// format (SQLAlchemy will use psycopg2 or psycopg3)
        # Properly URL encode password to handle special characters
        password = quote_plus(self.SUPABASE_DB_PASSWORD)
        database_url = f"postgresql://{self.SUPABASE_DB_USER}:{password}@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
        
        # Log the constructed URL (without password for security)
        safe_url = f"postgresql://{self.SUPABASE_DB_USER}:***@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
        logger.info(f"Database URL: {safe_url}")
        
        # Double-check the host
        if "supabase.co" in database_url:
            logger.error(
                f"❌ ERROR: Database URL contains Supabase host!\n"
                f"   URL: {safe_url}\n"
                f"   SUPABASE_DB_HOST value: {self.SUPABASE_DB_HOST}\n"
                f"   Environment SUPABASE_DB_HOST: {os.getenv('SUPABASE_DB_HOST', 'NOT SET')}\n"
                f"   This means .env file is overriding environment variables!"
            )
        
        return database_url
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables (like VITE_API_BASE_URL which is frontend-only)
        # Environment variables take precedence over .env file values
        # This ensures docker-compose.yml environment variables override .env file
        # Priority order: 1) Environment variables, 2) .env file, 3) Default values

settings = Settings()

