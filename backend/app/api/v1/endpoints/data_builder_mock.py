"""
Data Builder API endpoints - Mock implementation for testing
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import json
import random
import uuid

from app.api import deps
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

router = APIRouter()

# Request/Response models
class DataRecommendationRequest(BaseModel):
    task_info: Dict[str, Any] = Field(..., description="Task definition from step 1")
    selected_model: Dict[str, Any] = Field(..., description="Selected model from step 2")

class DataRecommendation(BaseModel):
    recommended_count: int
    min_count: int
    max_count: int
    collection_strategy: Dict[str, float]
    estimated_time_minutes: int
    quality_mode: str
    reasoning: str
    expected_performance: str
    data_sources: List[str]

class DataCollectionRequest(BaseModel):
    task_info: Dict[str, Any]
    selected_model: Dict[str, Any]
    data_count: int = Field(..., ge=100, le=1000000)
    quality_mode: str = Field("balanced", description="speed/balanced/quality")
    use_recommendation: bool = Field(True)

# In-memory storage
jobs = {}
data_storage = {}

@router.post("/recommend", response_model=DataRecommendation)
async def get_data_recommendation(
    request: DataRecommendationRequest,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get AI-powered recommendation for data collection"""
    
    # 根据任务类型返回合理的推荐
    task_type = request.task_info.get('type', 'classification')
    language = request.task_info.get('language', 'english')
    
    if task_type == 'recommendations' and language == 'chinese':
        return DataRecommendation(
            recommended_count=10000,
            min_count=5000,
            max_count=50000,
            collection_strategy={"web": 0.6, "ai": 0.4},
            estimated_time_minutes=40,
            quality_mode="balanced",
            reasoning="For Chinese recommendation systems, we suggest 10,000 samples with a mix of web data and AI-generated content to ensure diversity and quality.",
            expected_performance="Expected F1 Score: 0.85-0.90",
            data_sources=["Google", "Baidu", "Chinese Forums", "AI Generation"]
        )
    else:
        return DataRecommendation(
            recommended_count=10000,
            min_count=5000,
            max_count=50000,
            collection_strategy={"web": 0.7, "ai": 0.3},
            estimated_time_minutes=30,
            quality_mode="balanced",
            reasoning="Standard recommendation for classification tasks",
            expected_performance="Expected F1 Score: 0.80-0.85",
            data_sources=["Google", "Wikipedia", "AI Generation"]
        )

@router.post("/collect")
async def start_data_collection(
    request: DataCollectionRequest,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Start unified data collection"""
    
    # job_id = f"collect_{current_user.id}_{uuid.uuid4().hex[:8]}"
    job_id = f"collect_1_{uuid.uuid4().hex[:8]}" # Hardcoded user ID 1
    
    # Initialize job
    jobs[job_id] = {
        'job_id': job_id,
        # 'user_id': current_user.id,
        'user_id': 1, # Hardcoded user ID 1
        'status': 'collecting',
        'progress': 0,
        'total_count': request.data_count,
        'collected_count': 0,
        'sources_progress': {
            'web': 0,
            'ai': 0
        },
        'errors': [],
        'created_at': datetime.utcnow().isoformat(),
        'config': request.dict()
    }
    
    # Generate mock data immediately
    asyncio.create_task(generate_mock_data(job_id, request.data_count))
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "Data collection started",
        "estimated_time_minutes": request.data_count // 250
    }

async def generate_mock_data(job_id: str, target_count: int):
    """Generate mock data asynchronously"""
    
    job = jobs[job_id]
    data = []
    
    # 从job配置中获取任务信息
    task_info = job['config'].get('task_info', {})
    task_name = task_info.get('task', 'General Task')
    task_type = task_info.get('type', 'classification')
    language = task_info.get('language', 'english')
    description = task_info.get('description', '')
    
    # 根据任务类型生成相应的模板和数据
    if '中医' in task_name or 'TCM' in task_name or 'Chinese Medicine' in task_name:
        # 中医相关数据
        templates = [
            "体质为{体质}的人，{季节}应该多吃{食物}，有助于{功效}。",
            "{症状}的患者，建议食用{食物}，因为其具有{属性}的特性。",
            "根据中医理论，{食物}性{属性}，适合{体质}体质的人食用。",
            "{季节}养生，推荐{食物}，可以{功效}。",
            "中医认为{食物}入{经络}经，对{器官}有益。"
        ]
        variables = {
            '体质': ["平和质", "气虚质", "阳虚质", "阴虚质", "痰湿质", "湿热质", "血瘀质", "气郁质", "特禀质"],
            '季节': ["春季", "夏季", "秋季", "冬季"],
            '食物': ["山药", "枸杞", "红枣", "百合", "莲子", "薏米", "黑芝麻", "核桃", "银耳", "菊花"],
            '功效': ["补气养血", "滋阴润燥", "健脾和胃", "清热解毒", "活血化瘀", "温阳补肾"],
            '属性': ["寒", "凉", "平", "温", "热"],
            '症状': ["失眠多梦", "食欲不振", "疲劳乏力", "口干舌燥", "手脚冰凉"],
            '经络': ["肺", "脾", "肾", "肝", "心"],
            '器官': ["肺", "脾", "肾", "肝", "心"]
        }
        labels = ["饮食建议", "体质调理", "季节养生"]
    elif task_type == 'sentiment' or 'sentiment' in task_name.lower():
        # 情感分析数据
        templates = [
            "This {product} is {quality}. I {feeling} recommend it.",
            "The {service} was {experience}. {reaction}",
            "I'm {emotion} with this {item}. {verdict}",
            "{opinion} about the {aspect}. {rating}"
        ]
        variables = {
            'product': ["phone", "laptop", "camera", "headphones", "tablet"],
            'quality': ["excellent", "terrible", "average", "outstanding", "disappointing"],
            'feeling': ["would", "wouldn't", "might", "definitely", "never"],
            'service': ["customer support", "delivery", "installation", "warranty", "refund process"],
            'experience': ["amazing", "horrible", "satisfactory", "exceptional", "unacceptable"],
            'reaction': ["Will use again!", "Never again.", "It's okay.", "Highly impressed!", "Very disappointed."],
            'emotion': ["happy", "frustrated", "satisfied", "delighted", "angry"],
            'item': ["purchase", "product", "service", "experience", "company"],
            'verdict': ["Worth every penny!", "Complete waste.", "It's decent.", "Best ever!", "Worst mistake."],
            'opinion': ["Great", "Terrible", "Mixed feelings", "Excellent", "Poor"],
            'aspect': ["quality", "price", "features", "support", "design"],
            'rating': ["5 stars!", "1 star.", "3 stars.", "Perfect 10!", "Zero stars if I could."]
        }
        labels = ["positive", "negative", "neutral"]
    else:
        # 通用分类数据
        templates = [
            "This is a {category} example: {content}",
            "Sample text for {category}: {content}",
            "{content} - classified as {category}",
            "Example of {category} data: {content}"
        ]
        variables = {
            'category': ["class A", "class B", "class C"],
            'content': [
                "general example text",
                "sample data point",
                "test instance",
                "mock data entry",
                "placeholder content"
            ]
        }
        labels = ["class A", "class B", "class C"]
    
    # 分批生成数据
    batch_size = min(100, target_count)
    for i in range(0, target_count, batch_size):
        batch_count = min(batch_size, target_count - i)
        
        for j in range(batch_count):
            template = random.choice(templates)
            
            # 动态替换模板中的变量
            text = template
            for var_name in variables:
                placeholder = f"{{{var_name}}}"
                if placeholder in text:
                    text = text.replace(placeholder, random.choice(variables[var_name]))
            
            data.append({
                "id": f"{job_id}_{i+j}",
                "text": text,
                "label": random.choice(labels),
                "source": "web" if random.random() > 0.4 else "ai",
                "confidence": round(random.uniform(0.8, 0.95), 2),
                "created_at": datetime.utcnow().isoformat()
            })
        
        # 更新进度
        collected = i + batch_count
        progress = int((collected / target_count) * 100)
        
        job['collected_count'] = collected
        job['progress'] = progress
        job['sources_progress']['web'] = progress + random.randint(-5, 5)
        job['sources_progress']['ai'] = progress + random.randint(-5, 5)
        
        # 模拟延迟
        await asyncio.sleep(0.5)
    
    # 完成
    job['status'] = 'completed'
    job['progress'] = 100
    job['collected_count'] = len(data)
    job['total_count'] = len(data)
    data_storage[job_id] = data

@router.get("/job/{job_id}/progress")
async def get_job_progress(
    job_id: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get real-time progress of data collection"""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    # if job['user_id'] != current_user.id:
    #     raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "job_id": job_id,
        "status": job['status'],
        "progress": job['progress'],
        "collected_count": job.get('collected_count', 0),
        "total_count": job.get('total_count', 0),
        "sources_progress": job.get('sources_progress', {}),
        "message": job.get('message', ''),
        "errors": job.get('errors', [])
    }

@router.get("/job/{job_id}/data")
async def get_collected_data(
    job_id: str,
    skip: int = 0,
    limit: int = 100,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get collected data with filtering options"""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    # if job['user_id'] != current_user.id:
    #     raise HTTPException(status_code=403, detail="Access denied")
    
    # Get data
    data = data_storage.get(job_id, [])
    
    # Paginate
    total = len(data)
    paginated_data = data[skip:skip + limit]
    
    # Calculate statistics
    label_dist = {}
    source_dist = {}
    for item in data:
        label = item.get('label', 'unknown')
        source = item.get('source', 'unknown')
        label_dist[label] = label_dist.get(label, 0) + 1
        source_dist[source] = source_dist.get(source, 0) + 1
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": paginated_data,
        "statistics": {
            "label_distribution": label_dist,
            "source_distribution": source_dist,
            "average_confidence": sum(d.get('confidence', 0) for d in data) / len(data) if data else 0
        }
    } 