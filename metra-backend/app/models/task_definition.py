from sqlalchemy import Column, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class TaskDefinition(Base):
    __tablename__ = "task_definitions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), unique=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Task metadata
    name = Column(String, nullable=False)  # 任务名称
    description = Column(Text)  # 任务描述
    
    # Generated schema
    json_schema = Column(JSON, nullable=False)  # 生成的JSON Schema
    
    # Model recommendation (for future RAG implementation)
    recommended_models = Column(JSON)  # 推荐的模型列表
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="task_definition", uselist=False)
    user = relationship("User", back_populates="task_definitions") 