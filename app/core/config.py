from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # FastAPI Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Scrunch AI API Settings
    SCRUNCH_API_BASE_URL: str = "https://api.scrunchai.com/v1"
    SCRUNCH_API_TOKEN: str = "c62a3e304839aec08441e87b727f14880d297f7713d26005c4e667e729f3bb4a"
    BRAND_ID: int = 3230
    
    # Supabase Settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

