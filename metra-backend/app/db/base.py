from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import settings

# 动态选择数据库
database_url = settings.DATABASE_URL

# 处理 Railway 的 postgres:// URL
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif not database_url:
    # 开发环境使用 SQLite
    database_url = "sqlite+aiosqlite:///./test.db"

# Create async engine
if database_url.startswith("sqlite"):
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        future=True,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True  # 添加连接池预检查
    )

# Create async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Import all models here to ensure they are registered with Base
from app.models.user import User  # noqa 