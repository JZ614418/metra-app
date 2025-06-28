import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.models import User, InviteCode, Conversation, Message, TaskDefinition
from app.core.security import get_password_hash
import os

async def init_db():
    # 使用 SQLite 作为开发数据库
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    
    # 删除旧数据库
    if os.path.exists("test.db"):
        os.remove("test.db")
        print("Removed old database")
    
    # 创建引擎
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"check_same_thread": False}
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Created all tables")
    
    # 添加初始数据
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        # 创建初始邀请码
        invite_code = InviteCode(
            code="METRA2025",
            max_uses=100,
            times_used=0,
            is_active=True
        )
        session.add(invite_code)
        
        # 创建测试用户
        test_user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User",
            is_active=True,
            invite_code_used="METRA2025"
        )
        session.add(test_user)
        
        await session.commit()
        print("Added initial data")
    
    await engine.dispose()
    print("Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(init_db()) 