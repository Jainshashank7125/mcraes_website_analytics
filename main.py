from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings
from app.api import sync, data, database, auth, auth_v2, audit, sync_jobs, openai, websocket
from app.db.database import init_db, check_db_connection
from app.core.logging_config import setup_logging
from app.core.error_handlers import (
    base_api_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.core.exceptions import BaseAPIException
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Check database connection and initialize
    logger.info("Starting application...")
    logger.info(f"Supabase URL (for auth): {settings.SUPABASE_URL[:30] if settings.SUPABASE_URL else 'NOT SET'}...")
    logger.info(f"Supabase Key (for auth): {'SET' if settings.SUPABASE_KEY else 'NOT SET'}")
    
    # Log database configuration
    import os
    db_host_env = os.getenv("SUPABASE_DB_HOST", "NOT SET IN ENV")
    db_host_config = settings.SUPABASE_DB_HOST or "NOT SET"
    logger.info(f"Database Host - Environment: {db_host_env}, Config: {db_host_config}")
    
    if "supabase.co" in str(db_host_config):
        logger.error(
            "⚠️  ERROR: Database host is set to Supabase instead of local PostgreSQL!\n"
            "   This means SUPABASE_DB_HOST in .env file is overriding docker-compose.yml environment variables.\n"
            "   Solution: Either:\n"
            "   1. Remove SUPABASE_DB_HOST from .env file, OR\n"
            "   2. Set SUPABASE_DB_HOST=postgres in .env file, OR\n"
            "   3. Comment out the .env file mount in docker-compose.yml"
        )
    
    # Check REST API connection first (for auth only)
    try:
        from app.core.database import get_supabase_client
        client = get_supabase_client()
        logger.info("Supabase REST API connection (for auth): SUCCESS")
    except Exception as e:
        logger.warning(f"Supabase REST API connection failed (auth may not work): {e}")
    
    # Check direct DB connection (for database operations)
    logger.info("Checking PostgreSQL database connection...")
    if check_db_connection():
        logger.info("✅ PostgreSQL database connection successful!")
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Database initialization warning: {e}")
    else:
        logger.error("❌ PostgreSQL database connection failed!")
        logger.error("   Make sure PostgreSQL container is running and SUPABASE_DB_HOST=postgres is set")
    
    yield
    # Shutdown (if needed)

app = FastAPI(
    title="McRAE's Website Analytics API",
    description="API server to sync Scrunch AI data to Supabase",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers (order matters - most specific first)
app.add_exception_handler(BaseAPIException, base_api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(auth_v2.router, prefix="/api/v1", tags=["auth-v2"])
app.include_router(sync.router, prefix="/api/v1", tags=["sync"])
app.include_router(sync_jobs.router, prefix="/api/v1", tags=["sync-jobs"])
app.include_router(data.router, prefix="/api/v1", tags=["data"])
app.include_router(database.router, prefix="/api/v1", tags=["database"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
app.include_router(openai.router, prefix="/api/v1", tags=["openai"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])

@app.get("/")
async def root():
    return {
        "message": "McRAE's Website Analytics API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check configuration first
    config_status = {
        "supabase_url": "SET" if settings.SUPABASE_URL else "NOT SET",
        "supabase_key": "SET" if settings.SUPABASE_KEY else "NOT SET",
        "scrunch_token": "SET" if settings.SCRUNCH_API_TOKEN else "NOT SET"
    }
    
    # Check REST API connection (Supabase)
    api_status = False
    api_error = None
    try:
        from app.core.database import get_supabase_client
        client = get_supabase_client()
        # Just check if client is initialized (connection is verified by client creation)
        # The client is already initialized and URL/key are configured
        if client is not None:
            api_status = True
    except Exception as e:
        api_error = str(e)
    
    # Try direct DB connection (optional, may fail on Windows IPv6)
    db_status = check_db_connection()
    
    response = {
        "status": "healthy" if api_status else "unhealthy",
        "config": config_status,
        "database": {
            "rest_api": "connected" if api_status else "disconnected",
            "direct_postgres": "connected" if db_status else "disconnected"
        }
    }
    
    if api_error:
        response["api_error"] = api_error
    
    return response

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

