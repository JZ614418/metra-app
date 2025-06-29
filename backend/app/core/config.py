from typing import List, Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Metra Backend"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["https://metratraining.com", "http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        case_sensitive = True


settings = Settings() 