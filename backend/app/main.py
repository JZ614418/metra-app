from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Metra Backend API"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    from datetime import datetime
    from app.db.database_manager import get_db_status, db_manager
    
    # Check database health
    db_status = get_db_status()
    db_healthy = await db_manager.health_check() if db_manager.is_initialized else False
    
    overall_status = "healthy" if db_healthy else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": {
            **db_status,
            "healthy": db_healthy
        }
    }

# Configure logging for production
import logging
import sys

# Set up logging based on environment
if settings.ENVIRONMENT == "production":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Add startup event for monitoring
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application started successfully!")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"CORS origins: {settings.BACKEND_CORS_ORIGINS}")
    logger.info(f"API version: {settings.API_V1_STR}")
    logger.info(f"Queue timeout: {settings.QUEUE_TIMEOUT}s")
    logger.info(f"Max consecutive timeouts: {settings.MAX_CONSECUTIVE_TIMEOUTS}")
    
    # Initialize database
    try:
        from app.db.database_manager import init_database
        await init_database()
        logger.info("🎉 Database initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Continue running - app can still function with basic features
    
    # Initialize Supabase tables
    try:
        from app.db.supabase_client import supabase_service
        await supabase_service.ensure_tables_exist()
        logger.info("🎉 Supabase tables initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Supabase initialization failed: {e}")
        # Continue running - app can still function without Supabase 