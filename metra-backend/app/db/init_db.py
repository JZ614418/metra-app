from app.db.base import Base, engine
from app.models import *  # Import all models to register them

async def init_db():
    """Initialize database - create tables if they don't exist"""
    async with engine.begin() as conn:
        # In production, use Alembic migrations instead
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all) 