from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    openrouter_api_key: str
    courtlistener_api_key: str
    honcho_api_key: Optional[str] = None  # Optional for demo mode
    
    # Security
    secret_key: str
    
    # API URLs
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    courtlistener_base_url: str = "https://www.courtlistener.com/api/rest/v4"
    
    # Honcho Configuration
    honcho_environment: str = "demo"  # "demo" or "production"
    
    # AI Model
    ai_model: str = "moonshotai/kimi-k2:free"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()