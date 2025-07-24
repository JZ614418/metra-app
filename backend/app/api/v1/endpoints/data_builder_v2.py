"""
Data Builder API v2 - 修复版本
解决核心问题：
1. 硬编码jobId -> 真实的用户任务管理
2. 收集太慢 -> 高速并发收集
3. 数据丢失 -> 数据库持久化
4. 无任务历史 -> 用户任务管理
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import uuid
import logging

from app.api import deps
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.data_collection_task import DataCollectionTask, CollectedDataSample
from app.services.fast_data_collector import fast_collector
from app.services.mock_data_collector import mock_collector
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class DataCollectionRequest(BaseModel):
    task_info: Dict[str, Any] = Field(..., description="任务定义信息")
    selected_model: Dict[str, Any] = Field(..., description="选择的模型")
    data_count: int = Field(..., description="目标数据数量", ge=10, le=50000)
    quality_mode: str = Field(default="balanced", description="质量模式")
    enhanced_mode: bool = Field(default=False, description="增强模式：全文处理，无上限提取")
    task_name: Optional[str] = Field(None, description="任务名称")

class TaskStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    collected_count: int
    total_count: int
    message: str
    duration_seconds: Optional[float] = None
    average_confidence: Optional[float] = None

class UserTasksResponse(BaseModel):
    tasks: List[Dict[str, Any]]
    total: int

@router.post("/collect-v2", response_model=Dict[str, str])
async def start_data_collection_v2(
    request: DataCollectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    启动数据收集任务 v2 - 修复版本
    
    修复的问题：
    1. 每个用户每次收集创建新的任务ID
    2. 任务与用户绑定，持久化存储
    3. 使用高速收集器，大幅提升速度
    """
    
    try:
        # 生成真实的任务ID（不再硬编码）
        job_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # 创建数据库任务记录
        task_name = request.task_name or f"{request.task_info.get('description', '数据收集任务')}"
        
        db_task = DataCollectionTask(
            job_id=job_id,
            user_id=current_user.id,
            task_name=task_name,
            task_description=request.task_info.get('description', ''),
            task_type=request.task_info.get('type', 'classification'),
            task_info=request.task_info,
            target_count=request.data_count,
            quality_mode=request.quality_mode,
            selected_model=request.selected_model,
            status="pending"
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        logger.info(f"✅ Created task {job_id} for user {current_user.id}")
        
        # 启动后台高速收集
        background_tasks.add_task(
            run_fast_collection_with_db,
            job_id=job_id,
            task_info=request.task_info,
            target_count=request.data_count,
            db_task_id=db_task.id,
            enhanced_mode=request.enhanced_mode
        )
        
        return {
            "job_id": job_id,
            "message": f"Fast data collection started, estimated {request.data_count} samples will be completed in {estimate_time(request.data_count)}",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start collection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start collection: {str(e)}")

@router.get("/task/{job_id}/status", response_model=TaskStatusResponse)
async def get_task_status_v2(
    job_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取任务状态 v2 - 从数据库获取真实状态
    """
    
    # 从数据库获取任务
    db_task = db.query(DataCollectionTask).filter(
        DataCollectionTask.job_id == job_id,
        DataCollectionTask.user_id == current_user.id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 计算持续时间
    duration = None
    if db_task.started_at:
        end_time = db_task.completed_at or datetime.utcnow()
        duration = (end_time - db_task.started_at).total_seconds()
    
    # 获取状态消息
    message = get_status_message(db_task.status, db_task.progress, db_task.collected_count)
    
    return TaskStatusResponse(
        job_id=job_id,
        status=db_task.status,
        progress=db_task.progress,
        collected_count=db_task.collected_count,
        total_count=db_task.target_count,
        message=message,
        duration_seconds=duration,
        average_confidence=db_task.average_confidence
    )

@router.get("/task/{job_id}/data")
async def get_task_data_v2(
    job_id: str,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取任务收集的数据 v2 - 从数据库获取
    """
    
    # 验证任务所有权
    db_task = db.query(DataCollectionTask).filter(
        DataCollectionTask.job_id == job_id,
        DataCollectionTask.user_id == current_user.id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 获取数据样本
    samples_query = db.query(CollectedDataSample).filter(
        CollectedDataSample.task_id == db_task.id
    ).offset(offset).limit(limit)
    
    samples = samples_query.all()
    total_count = db.query(CollectedDataSample).filter(
        CollectedDataSample.task_id == db_task.id
    ).count()
    
    # 转换为API格式
    data_list = []
    for sample in samples:
        data_item = {
            "id": sample.id,
            "text": sample.text,
            "confidence": sample.confidence,
            "source": sample.source,
            "source_type": sample.source_type,
            "created_at": sample.created_at.isoformat() if sample.created_at else None
        }
        
        # 添加任务特定字段
        if sample.label:
            data_item["label"] = sample.label
        if sample.input_text:
            data_item["input"] = sample.input_text
        if sample.output_text:
            data_item["output"] = sample.output_text
        if sample.meta_data:
            data_item["meta_data"] = sample.meta_data
            
        data_list.append(data_item)
    
    # 计算统计信息
    avg_confidence = db.query(CollectedDataSample.confidence).filter(
        CollectedDataSample.task_id == db_task.id
    ).all()
    
    if avg_confidence:
        avg_conf = sum(c[0] for c in avg_confidence if c[0]) / len(avg_confidence)
    else:
        avg_conf = 0.0
    
    return {
        "job_id": job_id,
        "data": data_list,
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "statistics": {
            "total_samples": total_count,
            "average_confidence": avg_conf,
            "task_status": db_task.status,
            "task_progress": db_task.progress
        }
    }

@router.get("/my-tasks", response_model=UserTasksResponse)
async def get_user_tasks(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的所有数据收集任务
    """
    
    query = db.query(DataCollectionTask).filter(
        DataCollectionTask.user_id == current_user.id
    )
    
    if status:
        query = query.filter(DataCollectionTask.status == status)
    
    query = query.order_by(DataCollectionTask.created_at.desc())
    
    total = query.count()
    tasks = query.offset(skip).limit(limit).all()
    
    task_list = []
    for task in tasks:
        duration = None
        if task.started_at:
            end_time = task.completed_at or datetime.utcnow()
            duration = (end_time - task.started_at).total_seconds()
        
        task_dict = {
            "job_id": task.job_id,
            "task_name": task.task_name,
            "task_description": task.task_description,
            "task_type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "collected_count": task.collected_count,
            "target_count": task.target_count,
            "quality_mode": task.quality_mode,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "duration_seconds": duration,
            "average_confidence": task.average_confidence,
            "error_message": task.error_message
        }
        task_list.append(task_dict)
    
    return UserTasksResponse(tasks=task_list, total=total)

@router.delete("/task/{job_id}")
async def delete_task(
    job_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户的数据收集任务"""
    
    db_task = db.query(DataCollectionTask).filter(
        DataCollectionTask.job_id == job_id,
        DataCollectionTask.user_id == current_user.id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    
    return {"message": f"Task {job_id} deleted"}

# Helper Functions
async def run_fast_collection_with_db(job_id: str, task_info: Dict, target_count: int, db_task_id: int, enhanced_mode: bool = False):
    """
    运行高速收集并保存到数据库
    """
    
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        # 更新任务状态为运行中
        db_task = db.query(DataCollectionTask).filter(
            DataCollectionTask.id == db_task_id
        ).first()
        
        if not db_task:
            logger.error(f"Task {db_task_id} not found in database")
            return
        
        db_task.status = "running"
        db_task.started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"🚀 Starting fast collection for task {job_id}")
        
        # 创建进度回调函数
        async def progress_callback(progress_data):
            try:
                db_task.status = progress_data.get("status", "running")
                db_task.progress = min(int(progress_data.get("collected", 0) / target_count * 100), 99)
                db_task.collected_count = progress_data.get("collected", 0)
                db.commit()
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
        
        # Run real high-speed AI collection - Remove test mode detection, ensure users get real AI analysis
        logger.info(f"🤖 Starting real AI data collection" + (" (Enhanced Mode)" if enhanced_mode else ""))
        collected_data = await fast_collector.collect_data_fast(
            task_info=task_info,
            target_count=target_count,
            job_id=job_id,
            progress_callback=progress_callback,
            enhanced_mode=enhanced_mode
        )
        
        # 保存收集的数据到数据库
        logger.info(f"💾 Saving {len(collected_data)} samples to database...")
        
        total_confidence = 0
        for i, sample in enumerate(collected_data):
            db_sample = CollectedDataSample(
                task_id=db_task.id,
                text=sample.get('text', ''),
                label=sample.get('label'),
                input_text=sample.get('input'),
                output_text=sample.get('output'),
                confidence=sample.get('confidence', 0.0),
                source=sample.get('source', ''),
                source_type=sample.get('source_type', 'web'),
                meta_data=sample.get('meta_data')  # 注意：字段名是meta_data，不是metadata
            )
            db.add(db_sample)
            total_confidence += sample.get('confidence', 0.0)
        
        # 更新任务完成状态
        db_task.status = "completed"
        db_task.progress = 100
        db_task.collected_count = len(collected_data)
        db_task.completed_at = datetime.utcnow()
        db_task.average_confidence = total_confidence / len(collected_data) if collected_data else 0.0
        
        if db_task.started_at:
            db_task.duration_seconds = (db_task.completed_at - db_task.started_at).total_seconds()
        
        db.commit()
        
        logger.info(f"✅ Task {job_id} completed successfully with {len(collected_data)} samples")
        
    except Exception as e:
        logger.error(f"Fast collection failed for task {job_id}: {e}")
        
        # 更新任务为失败状态
        try:
            db_task = db.query(DataCollectionTask).filter(
                DataCollectionTask.id == db_task_id
            ).first()
            if db_task:
                db_task.status = "failed"
                db_task.error_message = str(e)
                db_task.completed_at = datetime.utcnow()
                db.commit()
        except Exception as save_error:
            logger.error(f"Failed to save error state: {save_error}")
    
    finally:
        db.close()

def estimate_time(target_count: int) -> str:
    """Estimate collection time based on real performance"""
    # 基于实际速度：约1个样本/秒
    minutes = target_count / 60
    
    if target_count <= 100:
        return "2-3 minutes"
    elif target_count <= 500:
        return "8-12 minutes"
    elif target_count <= 1000:
        return "15-20 minutes"
    elif target_count <= 2000:
        return "30-40 minutes"
    elif target_count <= 5000:
        return "60-90 minutes"
    else:
        hours = minutes / 60
        return f"{int(hours)}-{int(hours * 1.5)} hours"

def get_status_message(status: str, progress: int, collected: int) -> str:
    """Get status message"""
    if status == "pending":
        return "Task waiting..."
    elif status == "running":
        return f"Fast collection in progress... ({progress}% completed, collected {collected} samples)"
    elif status == "completed":
        return f"Collection completed! Total collected: {collected} samples"
    elif status == "failed":
        return "Collection failed, please try again"
    else:
        return f"Status: {status}"