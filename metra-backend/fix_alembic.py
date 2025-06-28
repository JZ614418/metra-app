#!/usr/bin/env python3
"""Fix alembic version table to mark migrations as already applied"""
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def fix_alembic():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set")
        return
    
    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        # Create alembic version table if it doesn't exist
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            )
        """))
        
        # Clear any existing versions
        await conn.execute(text("DELETE FROM alembic_version"))
        
        # Insert the latest migration version
        # This is the latest migration from your alembic/versions directory
        await conn.execute(text("""
            INSERT INTO alembic_version (version_num) VALUES ('add_phase2_models')
        """))
        
        print("Alembic version table fixed!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_alembic()) 