from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Metra Backend"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-replace-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./metra.db")
    USE_SUPABASE: bool = os.getenv("USE_SUPABASE", "false").lower() == "true"
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "YOUR_SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "YOUR_SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "YOUR_SUPABASE_SERVICE_KEY")
    
    # AI APIs
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
    TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY", "YOUR_TOGETHER_API_KEY")
    
    # Data Collection APIs
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
    GOOGLE_CX_ID: str = os.getenv("GOOGLE_CX_ID", "YOUR_GOOGLE_CX_ID")
    
    # DataBuilder V3 Search Engine APIs
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "YOUR_GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_CX: str = os.getenv("GOOGLE_SEARCH_CX", "YOUR_GOOGLE_SEARCH_CX")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "YOUR_SERPER_API_KEY")
    SCRAPINGBEE_API_KEY: str = os.getenv("SCRAPINGBEE_API_KEY", "YOUR_SCRAPINGBEE_API_KEY")
    
    # Email Service
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    
    # GPU Training Services
    RUNPOD_API_KEY: str = os.getenv("RUNPOD_API_KEY", "")
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "YOUR_REPLICATE_API_TOKEN")
    HUGGINGFACE_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "YOUR_HUGGINGFACE_TOKEN")

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
        "https://your-frontend-domain.vercel.app"
    ]
    
    # Environment and Performance Settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Data Collection Timeouts (SUPER PATIENT for AI processing)
    QUEUE_TIMEOUT: int = 300 if os.getenv("ENVIRONMENT") == "production" else 120  # 5分钟 vs 2分钟
    MAX_CONSECUTIVE_TIMEOUTS: int = 10 if os.getenv("ENVIRONMENT") == "production" else 8  # 更多容忍
    API_REQUEST_TIMEOUT: int = 180 if os.getenv("ENVIRONMENT") == "production" else 90  # 3分钟 vs 1.5分钟
    BATCH_SIZE: int = 2  # 减少批量大小，避免单次处理太久
    MAX_RETRIES: int = 5  # 更多重试
    RETRY_DELAY_BASE: int = 3  # 更长重试间隔
    
    # AI Processing specific timeouts
    AI_PROCESSING_TIMEOUT: int = 600  # AI处理单篇文章最多10分钟
    TOTAL_JOB_TIMEOUT: int = 3600  # 整个任务最多1小时
    
    # Health Check Settings
    HEALTH_CHECK_TIMEOUT: int = 5
    
    class Config:
        case_sensitive = True


settings = Settings()