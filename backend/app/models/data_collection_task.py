"""
Data Collection Task Model - 用户数据收集任务管理
解决硬编码jobId和数据丢失问题
"""
from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import uuid
from datetime import datetime

if TYPE_CHECKING:
    pass

class DataCollectionTask(Base):
    """数据收集任务模型 - 与用户绑定的任务管理"""
    __tablename__ = "data_collection_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 任务标识
    job_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 用户关联
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)  # 注意：User模型的id是String类型
    user = relationship("User", back_populates="data_tasks")
    
    # 任务信息
    task_name = Column(String(200), nullable=False)
    task_description = Column(Text)
    task_type = Column(String(50))  # classification, generation, etc.
    task_info = Column(JSON)  # 完整的任务定义
    
    # 收集配置
    target_count = Column(Integer, nullable=False)
    quality_mode = Column(String(20), default="balanced")  # speed, balanced, quality
    selected_model = Column(JSON)  # 选择的模型信息
    
    # 任务状态
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    collected_count = Column(Integer, default=0)
    
    # 时间记录
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 性能统计
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 数据质量
    average_confidence = Column(Float, default=0.0)
    data_sources = Column(JSON)  # 数据来源统计
    
    # 收集的数据（一对多关系）
    collected_data = relationship("CollectedDataSample", back_populates="task", cascade="all, delete-orphan")


class CollectedDataSample(Base):
    """收集的数据样本"""
    __tablename__ = "collected_data_samples"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联任务
    task_id = Column(Integer, ForeignKey("data_collection_tasks.id"), nullable=False, index=True)
    task = relationship("DataCollectionTask", back_populates="collected_data")
    
    # 样本数据
    text = Column(Text, nullable=False)
    label = Column(String(100), nullable=True)  # for classification
    input_text = Column(Text, nullable=True)    # for generation
    output_text = Column(Text, nullable=True)   # for generation
    
    # 质量信息
    confidence = Column(Float, default=0.0)
    source = Column(String(500))  # 数据来源URL
    source_type = Column(String(20))  # web, ai_generated, uploaded
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 额外元数据
    meta_data = Column(JSON, nullable=True)


# 添加到用户模型的关系
# 需要在 app/models/user.py 中添加：
# data_tasks = relationship("DataCollectionTask", back_populates="user")