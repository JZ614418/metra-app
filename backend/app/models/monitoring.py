"""
Monitoring and Analytics Database Models
生产级监控和分析数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from app.db.base_class import Base

class APICallLog(Base):
    """API调用日志表 - 记录每一次API调用的详细信息"""
    __tablename__ = "api_call_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    deployment_id = Column(String, index=True, nullable=True)
    user_id = Column(String, index=True)
    
    # 请求信息
    method = Column(String(10))  # GET, POST, PUT, DELETE
    endpoint = Column(String(255))
    request_size = Column(Integer, default=0)  # bytes
    
    # 响应信息
    status_code = Column(Integer)
    response_size = Column(Integer, default=0)  # bytes
    response_time_ms = Column(Float)  # milliseconds
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 请求内容（可选，用于调试）
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    # 地理和设备信息
    ip_address = Column(String(45))
    user_agent = Column(Text, nullable=True)
    country = Column(String(10), nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

class DeploymentMetrics(Base):
    """部署指标表 - 聚合的部署性能指标"""
    __tablename__ = "deployment_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(String, index=True, nullable=True)
    
    # 时间窗口
    date = Column(DateTime, index=True)  # 数据所属的日期/小时
    window_type = Column(String(10), index=True)  # hour, day, week, month
    
    # 基础指标
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # 性能指标
    avg_response_time = Column(Float, default=0.0)
    min_response_time = Column(Float, default=0.0)
    max_response_time = Column(Float, default=0.0)
    p95_response_time = Column(Float, default=0.0)
    p99_response_time = Column(Float, default=0.0)
    
    # 流量指标
    total_bytes_in = Column(BigInteger, default=0)
    total_bytes_out = Column(BigInteger, default=0)
    
    # 错误分析
    error_rate = Column(Float, default=0.0)  # 错误率百分比
    timeout_count = Column(Integer, default=0)
    rate_limit_count = Column(Integer, default=0)
    
    # 用户指标
    unique_users = Column(Integer, default=0)
    unique_ips = Column(Integer, default=0)
    
    # 地理分布
    top_countries = Column(JSON, nullable=True)  # {"US": 100, "CN": 50}
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)

class UsageStatistics(Base):
    """使用量统计表 - 用户和系统级别的使用统计"""
    __tablename__ = "usage_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    
    # 时间维度
    date = Column(DateTime, index=True)
    period_type = Column(String(10), index=True)  # daily, weekly, monthly
    
    # API使用量
    api_calls_count = Column(Integer, default=0)
    api_calls_success = Column(Integer, default=0)
    api_calls_failed = Column(Integer, default=0)
    
    # 数据处理量
    data_collected_samples = Column(Integer, default=0)
    data_processed_samples = Column(Integer, default=0)
    data_quality_score = Column(Float, default=0.0)
    
    # 模型训练
    models_trained = Column(Integer, default=0)
    training_time_minutes = Column(Float, default=0.0)
    training_cost_usd = Column(Float, default=0.0)
    
    # 部署使用
    models_deployed = Column(Integer, default=0)
    deployment_uptime_minutes = Column(Float, default=0.0)
    
    # 成本分析
    total_cost_usd = Column(Float, default=0.0)
    cost_breakdown = Column(JSON, nullable=True)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemMetrics(Base):
    """系统指标表 - 整个平台的健康状态指标"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 系统性能
    cpu_usage_percent = Column(Float, default=0.0)
    memory_usage_percent = Column(Float, default=0.0)
    disk_usage_percent = Column(Float, default=0.0)
    
    # 服务状态
    services_status = Column(JSON)  # {"api": "healthy", "db": "healthy"}
    
    # 数据库性能
    db_connection_count = Column(Integer, default=0)
    db_query_avg_time = Column(Float, default=0.0)
    db_slow_queries = Column(Integer, default=0)
    
    # 外部服务状态
    openai_api_status = Column(String(20))  # healthy, degraded, down
    replicate_api_status = Column(String(20))
    openai_response_time = Column(Float, default=0.0)
    replicate_response_time = Column(Float, default=0.0)
    
    # 活跃用户
    active_users_count = Column(Integer, default=0)
    active_deployments_count = Column(Integer, default=0)
    active_training_jobs = Column(Integer, default=0)
    
    # 错误统计
    error_count_last_hour = Column(Integer, default=0)
    critical_errors = Column(Integer, default=0)
    warnings = Column(Integer, default=0)

class AlertEvent(Base):
    """告警事件表 - 记录系统告警历史"""
    __tablename__ = "alert_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 告警基本信息
    alert_type = Column(String(50), index=True)  # error_rate, response_time, system_down
    severity = Column(String(20), index=True)  # critical, warning, info
    title = Column(String(255))
    message = Column(Text)
    
    # 相关资源
    resource_type = Column(String(50))  # deployment, system, user
    resource_id = Column(String(100), index=True)
    
    # 指标信息
    metric_name = Column(String(100))
    metric_value = Column(Float)
    threshold_value = Column(Float)
    
    # 状态管理
    status = Column(String(20), default="open")  # open, acknowledged, resolved
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # 时间戳
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 通知状态
    notifications_sent = Column(JSON, nullable=True)  # {"slack": True, "email": False}

class ModelPerformanceMetrics(Base):
    """模型性能指标"""
    __tablename__ = 'model_performance_metrics'

    id = Column(BigInteger, primary_key=True, index=True)
    deployment_id = Column(String, nullable=True, index=True)
    user_id = Column(String, index=True)
    
    # 模型基本信息
    model_name = Column(String(255))
    base_model = Column(String(100))
    task_type = Column(String(50))
    
    # 训练指标
    training_accuracy = Column(Float, nullable=True)
    validation_accuracy = Column(Float, nullable=True)
    training_loss = Column(Float, nullable=True)
    validation_loss = Column(Float, nullable=True)
    training_time_minutes = Column(Float, nullable=True)
    training_cost_usd = Column(Float, nullable=True)
    
    # 数据指标
    training_samples_count = Column(Integer, default=0)
    data_quality_score = Column(Float, nullable=True)
    
    # 推理性能（生产环境）
    avg_inference_time = Column(Float, nullable=True)
    throughput_requests_per_second = Column(Float, nullable=True)
    
    # 业务指标
    user_satisfaction_score = Column(Float, nullable=True)  # 1-5评分
    prediction_confidence_avg = Column(Float, nullable=True)
    
    # 时间戳
    training_completed_at = Column(DateTime, nullable=True)
    deployment_started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 额外元数据
    metrics_metadata = Column(JSON, nullable=True)