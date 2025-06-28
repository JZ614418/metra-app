from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
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
    
    # Invite code relationships
    invite_code_used = Column(String, ForeignKey("invite_codes.code"), nullable=True)
    
    # Relationships
    used_invite_code = relationship("InviteCode", foreign_keys=[invite_code_used], back_populates="used_by_users")
    created_invite_codes = relationship("InviteCode", foreign_keys="InviteCode.created_by", back_populates="creator")
    conversations = relationship("Conversation", back_populates="user")
    task_definitions = relationship("TaskDefinition", back_populates="user")


class InviteCode(Base):
    __tablename__ = "invite_codes"
    
    code = Column(String, primary_key=True, unique=True, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)  # null for system-generated codes
    max_uses = Column(Integer, default=1)
    times_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_invite_codes")
    used_by_users = relationship("User", foreign_keys="User.invite_code_used", back_populates="used_invite_code") 