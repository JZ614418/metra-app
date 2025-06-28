from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, Field
import os

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Metra API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./test.db",
        env="DATABASE_URL"
    )
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Redis
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None
    
    # API Keys
    OPENAI_API_KEY: str = Field(
        default="",
        env="OPENAI_API_KEY"
    )
    OPENAI_ORG_ID: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
    SCRAPINGBEE_API_KEY: Optional[str] = None
    
    # Email
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: str = "noreply@metratraining.com"
    RESEND_FROM_NAME: str = "Metra"
    
    # Inngest
    INNGEST_EVENT_KEY: Optional[str] = None
    INNGEST_SIGNING_KEY: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    # Cloudflare
    CLOUDFLARE_API_TOKEN: Optional[str] = None
    CLOUDFLARE_ZONE_ID: Optional[str] = None
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None
    
    # Railway
    RAILWAY_TOKEN: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Free tier limits
    FREE_MODELS_PER_MONTH: int = 3
    FREE_API_CALLS_PER_MONTH: int = 1000
    FREE_TRAINING_MINUTES_PER_MONTH: int = 120
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 