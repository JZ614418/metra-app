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
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./metra.db")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Data Collection APIs
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_CX_ID: str = os.getenv("GOOGLE_CX_ID", "")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    SCRAPINGBEE_API_KEY: str = os.getenv("SCRAPINGBEE_API_KEY", "")
    
    # Email Service
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    
    # GPU Training Services
    RUNPOD_API_KEY: str = os.getenv("RUNPOD_API_KEY", "")
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")
    HUGGINGFACE_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://metratraining.com", 
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8083",
        "http://localhost:8084",
        "https://metra-r7irxtk4-jz614418s-projects.vercel.app"
    ]
    
    class Config:
        case_sensitive = True


settings = Settings() 