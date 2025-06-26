from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    # 使用字符串类型的 UUID，兼容 SQLite
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Free tier limits
    models_created_this_month = Column(Integer, default=0)
    api_calls_this_month = Column(Integer, default=0)
    training_minutes_this_month = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Subscription info (for future)
    subscription_tier = Column(String, default="free")
    subscription_expires_at = Column(DateTime(timezone=True)) 