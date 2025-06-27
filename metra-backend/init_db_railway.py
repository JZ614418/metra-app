#!/usr/bin/env python3
"""
Initialize database for Railway deployment
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.models.user import User
from app.core.config import settings

async def init_db():
    """Initialize database with tables"""
    # Get DATABASE_URL from settings
    database_url = settings.DATABASE_URL
    
    # Handle Railway's postgres:// URL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    print(f"Connecting to database...")
    
    # Create engine
    engine = create_async_engine(
        database_url,
        echo=True,
        pool_pre_ping=True
    )
    
    async with engine.begin() as conn:
        # Create all tables
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db()) 