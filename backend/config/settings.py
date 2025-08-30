from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    openrouter_api_key: str
    courtlistener_api_key: str
    honcho_api_key: Optional[str] = None  # Optional for demo mode
    
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Flowglad Configuration
    flowglad_secret_key: str

    # Security
    secret_key: str
    
    # API URLs
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    courtlistener_base_url: str = "https://www.courtlistener.com/api/rest/v4"
    
    # Honcho Configuration
    honcho_environment: str = "demo"  # "demo" or "production"
    
    demand_notice_price: float = 0.0  # $0 for now

    # AI Model
    ai_model: str = "moonshotai/kimi-k2:free"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Feature flags
    enable_auth: bool = False
    enable_payments: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def model_post_init(self, __context) -> None:
        """Post-initialization to set feature flags"""
        self.enable_auth = bool(self.supabase_url and self.supabase_anon_key and self.supabase_service_role_key)
        self.enable_payments = bool(self.flowglad_secret_key)
    
    @property
    def auth_enabled(self) -> bool:
        """Check if authentication is properly configured"""
        return (self.enable_auth and 
                self.supabase_url and 
                self.supabase_anon_key and 
                self.supabase_service_role_key)
    
    @property
    def payments_enabled(self) -> bool:
        """Check if payments are properly configured"""
        return (self.enable_payments and 
                self.flowglad_secret_key)


settings = Settings()