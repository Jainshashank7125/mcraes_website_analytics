import logging
import sys
from app.core.config import settings

def setup_logging():
    """Configure logging for the application"""
    # Use DEBUG level if DEBUG mode is enabled, otherwise INFO
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Enable DEBUG logging for data API module
    logging.getLogger("app.api.data").setLevel(logging.DEBUG)

