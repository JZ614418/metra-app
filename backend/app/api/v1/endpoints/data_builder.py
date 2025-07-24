"""
Data Builder API endpoints - Unified intelligent data collection
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import json

from app.api import deps
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.data_collection import data_collection_service
from app.services.data_generation import data_generation_service
from app.services.data_collection_optimizer import OptimizedDataCollector
from app.services.async_data_collector import async_data_collector
from app.services.simple_ai_collector import simple_ai_collector
from app.db.supabase_client import supabase_service
from openai import AsyncOpenAI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
optimizer = OptimizedDataCollector()

# Request/Response models
class DataRecommendationRequest(BaseModel):
    task_info: Dict[str, Any] = Field(..., description="Task definition from step 1")
    selected_model: Dict[str, Any] = Field(..., description="Selected model from step 2")
    user_data_volume: Optional[int] = Field(None, description="User's preferred data volume from task definition")

class DataRecommendation(BaseModel):
    recommended_count: int
    min_count: int
    max_count: int
    collection_strategy: Dict[str, float]  # e.g., {"web": 0.6, "ai": 0.4}
    estimated_time_minutes: int
    quality_mode: str  # "speed", "balanced", "quality"
    reasoning: str
    expected_performance: str
    data_sources: List[str]

class DataCollectionRequest(BaseModel):
    task_info: Dict[str, Any]
    selected_model: Dict[str, Any]
    data_count: int = Field(..., ge=100, le=1000000)
    quality_mode: str = Field("balanced", description="speed/balanced/quality")
    use_recommendation: bool = Field(True, description="Whether to use AI recommendation")

class DataAnalysisRequest(BaseModel):
    job_id: str
    query: str = Field(..., description="Natural language query about the data")

class DataModificationRequest(BaseModel):
    job_id: str
    action: str = Field(..., description="Action to perform: filter, augment, balance, etc.")
    parameters: Dict[str, Any] = Field(..., description="Action parameters")

# Legacy in-memory storage for backward compatibility (will be phased out)
jobs = {}
data_storage = {}

# Initialize Supabase on startup
async def init_supabase():
    """Initialize Supabase tables"""
    try:
        await supabase_service.ensure_tables_exist()
        logger.info("Supabase tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase tables: {e}")

# Note: Supabase initialization moved to startup event in main.py

@router.post("/recommend", response_model=DataRecommendation)
async def get_data_recommendation(
    request: DataRecommendationRequest,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """
    Get AI-powered recommendation for data collection based on task and model
    """
    task_info = request.task_info
    model_info = request.selected_model
    
    # Extract user preferences
    user_data_volume = request.user_data_volume
    task_name = task_info.get('task', 'Unknown task')
    task_description = task_info.get('description', '')
    
    # Create enhanced prompt for recommendation
    prompt = f"""You are an AI training data expert. Analyze this specific task and provide personalized recommendations:

TASK ANALYSIS:
Task Name: {task_name}
Task Type: {task_info.get('type', 'classification')}
Language: {task_info.get('language', 'english')}
Labels: {task_info.get('labels', [])}
Full Description: {task_description}

USER PREFERENCES:
Preferred Data Volume: {user_data_volume if user_data_volume else 'Not specified'}

SELECTED MODEL:
Model: {model_info.get('name', 'Unknown')}
Type: {model_info.get('modelType', 'Unknown')}
Size: {model_info.get('size', 'base')}

DOMAIN-SPECIFIC ANALYSIS:
For this specific task "{task_name}" with description "{task_description}":
1. What domain expertise is required? (medical, legal, technical, etc.)
2. What data quality challenges are expected?
3. What specialized data sources would be most valuable?

PERSONALIZED RECOMMENDATIONS:
Based on the user's preference for {user_data_volume if user_data_volume else '10000-50000'} samples:
1. Recommended data count (respect user preference if provided)
2. Optimal collection strategy (web vs AI generation percentages)
3. Domain-specific data sources
4. Quality vs speed trade-offs
5. Expected training time and model performance

Return as JSON with fields: recommended_count, min_count, max_count, collection_strategy, estimated_time_minutes, quality_mode, reasoning, expected_performance, data_sources."""

    try:
        # Get AI recommendation
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data science expert helping users collect training data for language models."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        recommendation_data = json.loads(response.choices[0].message.content)
        
        # Use user preference if provided, otherwise use AI recommendation
        default_count = user_data_volume if user_data_volume else 10000
        
        # Ensure all required fields
        recommendation = DataRecommendation(
            recommended_count=recommendation_data.get("recommended_count", default_count),
            min_count=recommendation_data.get("min_count", max(default_count // 5, 1000)),
            max_count=recommendation_data.get("max_count", default_count * 2),
            collection_strategy=recommendation_data.get("collection_strategy", {"web": 0.6, "ai": 0.4}),
            estimated_time_minutes=recommendation_data.get("estimated_time_minutes", 40),
            quality_mode=recommendation_data.get("quality_mode", "balanced"),
            reasoning=recommendation_data.get("reasoning", f"AI analysis based on task '{task_name}' and user preferences"),
            expected_performance=recommendation_data.get("expected_performance", "F1 Score: 0.85+"),
            data_sources=recommendation_data.get("data_sources", ["Google", "Wikipedia", "AI Generation"])
        )
        
        return recommendation
        
    except Exception as e:
        # Use user preference even in fallback
        fallback_count = user_data_volume if user_data_volume else 10000
        
        # Fallback recommendation with user preferences
        return DataRecommendation(
            recommended_count=fallback_count,
            min_count=max(fallback_count // 5, 1000),
            max_count=fallback_count * 2,
            collection_strategy={"web": 0.6, "ai": 0.4},
            estimated_time_minutes=40,
            quality_mode="balanced",
            reasoning=f"Fallback recommendation based on task '{task_name}' - AI analysis temporarily unavailable",
            expected_performance="Expected F1 Score: 0.80-0.85",
            data_sources=["Google Search", "Wikipedia", "AI Generation"]
        )

@router.post("/collect")
async def start_data_collection(
    request: DataCollectionRequest,
    background_tasks: BackgroundTasks,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """
    Start data collection with SIMPLE AI SPLITTING - NO QUEUE TIMEOUTS!
    AI处理完直接推送数据，不走队列等待
    """
    job_id = f"simple_collect_{int(datetime.utcnow().timestamp())}"
    user_id = "1"  # Hardcoded for testing
    
    # Initialize job status
    jobs[job_id] = {
        "job_id": job_id,
        "user_id": user_id,
        "status": "started", 
        "collected_count": 0,
        "total_count": request.data_count,
        "progress": 0,
        "message": "Starting simple AI collection - no timeouts!",
        "errors": [],
        "data": []
    }
    
    # Start simple AI collection in background
    background_tasks.add_task(
        run_simple_ai_collection,
        job_id,
        request
    )
    
    return {
        "job_id": job_id,
        "status": "started", 
        "message": "Simple AI collection started - AI will push data when ready!",
        "estimated_time_minutes": max(request.data_count // 20, 3)  # More realistic estimate
    }

async def run_simple_ai_collection(job_id: str, request: DataCollectionRequest):
    """
    Simple AI collection - no queue, direct push
    AI处理完直接更新job状态，不需要队列等待
    """
    
    async def progress_callback(progress_data):
        """Update job progress directly"""
        if job_id in jobs:
            jobs[job_id].update({
                "status": progress_data["status"],
                "collected_count": progress_data["collected"],
                "progress": int((progress_data["collected"] / progress_data["total"]) * 100),
                "message": progress_data.get("message", "Processing..."),
                "updated_at": datetime.utcnow().isoformat()
            })
            logger.info(f"Job {job_id} progress: {progress_data['message']}")
    
    try:
        logger.info(f"🚀 Starting simple AI collection for job {job_id}")
        
        # Use simple AI collector - no queue timeouts!
        collected_data = await simple_ai_collector.collect_with_ai_splitting(
            task_info=request.task_info,
            target_count=request.data_count,
            job_id=job_id,
            progress_callback=progress_callback
        )
        
        # Update final job status
        if job_id in jobs:
            jobs[job_id].update({
                "status": "completed",
                "collected_count": len(collected_data),
                "progress": 100,
                "message": f"Completed! Collected {len(collected_data)} AI-enhanced samples",
                "data": collected_data,
                "completed_at": datetime.utcnow().isoformat()
            })
            
        # Store in data_storage for compatibility
        data_storage[job_id] = collected_data
        
        logger.info(f"✅ Simple AI collection completed for job {job_id}: {len(collected_data)} samples")
        
    except Exception as e:
        logger.error(f"Simple AI collection failed for job {job_id}: {e}")
        if job_id in jobs:
            jobs[job_id].update({
                "status": "failed",
                "message": f"Collection failed: {str(e)}",
                "errors": [str(e)],
                "updated_at": datetime.utcnow().isoformat()
            })

async def run_optimized_collection(job_id: str, request: DataCollectionRequest, user_id: int):
    """Background task for optimized data collection with Supabase storage"""
    # Create job record in memory first
    job_record = {
        'job_id': job_id,
        'user_id': user_id,
        'status': 'started',
        'progress': 0,
        'collected_count': 0,
        'total_count': request.data_count,
        'created_at': datetime.utcnow().isoformat(),
        'message': 'Initializing data collection'
    }
    jobs[job_id] = job_record
    
    # Try to get job from Supabase, fallback to in-memory
    job = await supabase_service.get_data_collection_job(job_id)
    if not job:
        job = jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in Supabase or memory")
            return
    
    async def update_job_progress(updates):
        """Helper to update job progress in Supabase"""
        try:
            await supabase_service.update_data_collection_job(job_id, updates)
            # Also update in-memory for compatibility
            if job_id in jobs:
                jobs[job_id].update(updates)
        except Exception as e:
            logger.error(f"Failed to update job progress: {e}")
            # Fallback to in-memory update
            if job_id in jobs:
                jobs[job_id].update(updates)
    
    try:
        await update_job_progress({
            'status': 'collecting',
            'progress': 10,
            'message': 'Starting data collection'
        })
        
        # Simplified collection - just use Google Search + ScrapingBee
        from app.services.data_collection import DataCollectionService
        
        service = DataCollectionService()
        collected_data = []
        
        # Generate search queries based on task
        task_type = request.task_info.get('type', 'classification')
        task_description = request.task_info.get('task', '')
        
        # Generate comprehensive search queries for large-scale collection
        base_queries = []
        
        # Task-specific queries
        if "中医" in task_description:
            base_queries.extend([
                "中医诊断案例", "中医治疗方法", "中医病例分析", "中医症状诊断",
                "中医临床经验", "中医方剂配伍", "中医治疗原则", "中医辨证论治",
                "中医脏腑辨证", "中医经络治疗", "中医药物治疗", "中医针灸治疗",
                "中医推拿治疗", "中医食疗方案", "中医养生保健", "中医体质调理",
                "中医疾病预防", "中医康复治疗", "中医内科诊疗", "中医外科治疗",
                "中医妇科调理", "中医儿科治疗", "中医老年保健", "中医急救处理",
                "中医慢性病管理", "中医亚健康调理", "中医情志调摄", "中医时令养生"
            ])
        
        # Generic queries for any task
        base_queries.extend([
            f"{task_description} 案例", f"{task_description} 实例", f"{task_description} 例子",
            f"{task_description} 经验", f"{task_description} 方法", f"{task_description} 技巧",
            f"{task_description} 问答", f"{task_description} 咨询", f"{task_description} 指导",
            f"{task_description} 建议", f"{task_description} 解答", f"{task_description} 回复",
            f"{task_type} {task_description}", f"{task_description} {task_type}",
            f"{task_description} examples", f"{task_description} samples"
        ])
        
        # Remove duplicates and expand for large-scale collection
        base_queries = list(set(base_queries))
        
        # For large-scale collection, generate more queries dynamically
        if request.data_count >= 5000:
            # Add numerical and temporal variations
            variations = []
            for query in base_queries[:20]:  # Take top 20 base queries
                variations.extend([
                    f"{query} 2023", f"{query} 2024", f"{query} 最新",
                    f"{query} 详细", f"{query} 完整", f"{query} 全面",
                    f"{query} 专业", f"{query} 深入", f"{query} 系统",
                    f"{query} 实践", f"{query} 应用", f"{query} 临床"
                ])
            base_queries.extend(variations)
            
        # For very large collections, don't limit query count
        if request.data_count >= 10000:
            max_queries = min(len(base_queries), 500)  # Up to 500 queries for 10k+ data
        else:
            max_queries = min(len(base_queries), 100)  # Up to 100 queries for smaller collections
            
        base_queries = base_queries[:max_queries]
        
        await update_job_progress({
            'progress': 20,
            'message': f'Generated {len(base_queries)} search queries'
        })
        
        # Collect from Google Search with more aggressive approach
        for i, query in enumerate(base_queries):
            try:
                # Get search results - Google API limit is 10 per request
                results = await service.search_google(query, 10)  # Get up to 10 results per query
                
                # Process each result 
                for result in results:
                    if len(collected_data) >= request.data_count:
                        break
                        
                    url = result.get('url', '')
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    
                    # Always add the search result data first
                    if snippet:
                        collected_data.append({
                            'text': snippet,
                            'title': title,
                            'url': url,
                            'source': 'google_search',
                            'label': 'unknown'
                        })
                    
                    # Try to get enhanced content if whitelisted
                    if url and service._is_whitelisted(url):
                        try:
                            enhanced = await service.scrape_with_scrapingbee(url)
                            if enhanced and enhanced.get('content'):
                                # Add enhanced content as separate data point
                                collected_data.append({
                                    'text': enhanced.get('content', ''),
                                    'title': enhanced.get('title', title),
                                    'url': url,
                                    'source': 'scrapingbee_enhanced',
                                    'label': 'unknown'
                                })
                        except Exception as scrape_error:
                            print(f"ScrapingBee error for {url}: {scrape_error}")
                            # Continue with snippet data we already added
                    
                    # Check if we have enough data
                    if len(collected_data) >= request.data_count:
                        break
                
                # Update progress more frequently
                progress = 20 + (i + 1) * 50 // len(base_queries)
                await update_job_progress({
                    'progress': min(progress, 75),
                    'collected_count': len(collected_data),
                    'message': f'Processed query {i+1}/{len(base_queries)}, collected {len(collected_data)} samples'
                })
                
                # Break if we have enough data
                if len(collected_data) >= request.data_count:
                    break
                    
            except Exception as e:
                print(f"Error processing query '{query}': {e}")
                continue
        
        # If we still need more data, use AI generation to fill the gap
        if len(collected_data) < request.data_count:
            remaining_needed = request.data_count - len(collected_data)
            await update_job_progress({
                'progress': 70,
                'message': f'Collected {len(collected_data)} from web, generating {remaining_needed} more with AI'
            })
            
            # Use AI to generate additional training data
            await generate_ai_data(collected_data, remaining_needed, request.task_info)
        
        # Store collected data in Supabase and memory (for redundancy)
        try:
            await supabase_service.store_collected_data(job_id, collected_data)
            logger.info(f"Stored {len(collected_data)} items in Supabase for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to store data in Supabase: {e}")
        
        # Always store in memory as backup
        data_storage[job_id] = collected_data
        logger.info(f"Stored {len(collected_data)} items in memory storage for job {job_id}")
        
        # Process data through DFE for training readiness
        await update_job_progress({
            'status': 'processing_dfe',
            'progress': 80,
            'message': 'Processing data through DFE for training readiness'
        })
        
        processed_data = await process_with_dfe(collected_data, request.task_info)
        
        # Update with processed data in Supabase
        try:
            # Delete old data and store new processed data
            await supabase_service.delete_collected_data(job_id)
            await supabase_service.store_collected_data(job_id, processed_data)
            logger.info(f"Stored {len(processed_data)} processed items in Supabase")
        except Exception as e:
            logger.error(f"Failed to store processed data in Supabase: {e}")
        
        # Always store processed data in memory as backup
        data_storage[job_id] = processed_data
        logger.info(f"Stored {len(processed_data)} processed items in memory storage for job {job_id}")
        
        # Mark job as completed
        await update_job_progress({
            'status': 'completed',
            'progress': 100,
            'total_count': len(processed_data),
            'collected_count': len(processed_data),
            'message': f'Successfully collected and processed {len(processed_data)} samples'
        })
        
    except Exception as e:
        error_message = f"Collection failed: {str(e)}"
        await update_job_progress({
            'status': 'failed',
            'errors': [str(e)],
            'message': error_message
        })
        logger.error(f"Job {job_id} failed: {str(e)}")

@router.get("/job/{job_id}/progress")
async def get_job_progress(
    job_id: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get real-time progress - supports both simple and async collectors!"""
    
    # Check simple collector first (for new jobs)
    if job_id in jobs:
        job = jobs[job_id]
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job.get("progress", 0),
            "collected_count": job.get("collected_count", 0),
            "total_count": job.get("total_count", 0),
            "sources_progress": {},
            "message": job.get("message", "Processing..."),
            "errors": job.get("errors", [])
        }
    
    # Fallback to async collector for older jobs
    job_status = await async_data_collector.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job_status["status"],
        "progress": job_status["progress_percentage"],
        "collected_count": job_status["collected_count"],
        "total_count": job_status["total_count"],
        "sources_progress": {},
        "message": f"Async processing: {job_status['status']}",
        "errors": job_status.get("errors", [])
    }
    
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
    label: Optional[str] = None,
    source: Optional[str] = None,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get collected data from async job - ALWAYS WORKS!"""
    
    # Try to get data from multiple sources
    result = None
    
    # First try: async_data_collector (for new v2 jobs)
    try:
        result = await async_data_collector.get_collected_data(job_id, skip, limit)
        if result and result["data"]:
            logger.info(f"Found data via async_data_collector: {len(result['data'])} items")
    except Exception as e:
        logger.warning(f"async_data_collector failed: {e}")
    
    # Second try: Check if data exists in memory storage (for v1 jobs)
    if not result or not result["data"]:
        if job_id in data_storage and data_storage[job_id]:
            stored_data = data_storage[job_id]
            result = {
                "data": stored_data[skip:skip+limit],
                "total": len(stored_data),
                "skip": skip,
                "limit": limit
            }
            logger.info(f"Found data in memory storage: {len(stored_data)} items")
    
    # Third try: Direct database query
    if not result or not result["data"]:
        try:
            from app.db.supabase_client import supabase_service
            db_result = await supabase_service.get_collected_data(job_id, skip, limit)
            if db_result and db_result.get("data"):
                result = db_result
                logger.info(f"Found data in database: {len(db_result['data'])} items")
        except Exception as e:
            logger.warning(f"Database query failed: {e}")
    
    # If still no data, check job status
    if not result or not result["data"]:
        job_status = await async_data_collector.get_job_status(job_id)
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        elif job_status["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Job status: {job_status['status']} - not completed yet")
        else:
            raise HTTPException(status_code=404, detail="Job completed but no data found - data may not have been saved properly")
    
    data = result["data"]
    
    # Apply filters
    if label:
        data = [d for d in data if d.get('label') == label]
    if source:
        data = [d for d in data if d.get('source') == source]
    
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

@router.post("/job/{job_id}/analyze")
async def analyze_data_with_ai(
    job_id: str,
    request: DataAnalysisRequest,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Use AI to analyze collected data based on natural language query"""
    if job_id not in jobs or job_id not in data_storage:
        raise HTTPException(status_code=404, detail="Job or data not found")
    
    job = jobs[job_id]
    # if job['user_id'] != current_user.id:
    #     raise HTTPException(status_code=403, detail="Access denied")
    
    data = data_storage[job_id]
    
    # Prepare data summary for AI
    data_summary = {
        "total_samples": len(data),
        "label_distribution": {},
        "source_distribution": {},
        "sample_examples": data[:5] if len(data) > 5 else data
    }
    
    for item in data:
        label = item.get('label', 'unknown')
        source = item.get('source', 'unknown')
        data_summary['label_distribution'][label] = data_summary['label_distribution'].get(label, 0) + 1
        data_summary['source_distribution'][source] = data_summary['source_distribution'].get(source, 0) + 1
    
    # Create prompt
    prompt = f"""Analyze the following dataset based on the user query:

User Query: {request.query}

Dataset Summary:
{json.dumps(data_summary, indent=2)}

Provide actionable insights and recommendations. If the user asks for specific operations (like filtering, balancing, etc.), suggest the exact parameters needed."""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Data AI assistant helping users analyze and improve their training datasets. Respond in English."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        analysis = response.choices[0].message.content
        
        if not analysis:
            analysis = "Data analysis completed. Your dataset contains useful training samples, recommend proceeding with training."
        
        # Check if any actions are suggested
        suggested_actions = []
        if "filter" in request.query.lower():
            suggested_actions.append({
                "action": "filter",
                "description": "Filter low-quality data",
                "parameters": {"min_confidence": 0.8}
            })
        if "balance" in request.query.lower():
            suggested_actions.append({
                "action": "balance",
                "description": "Balance label distribution",
                "parameters": {"target_distribution": "equal"}
            })
        
        return {
            "analysis": analysis,
            "suggested_actions": suggested_actions,
            "current_stats": data_summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/job/{job_id}/modify")
async def modify_dataset(
    job_id: str,
    request: DataModificationRequest,
    background_tasks: BackgroundTasks,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Modify dataset based on AI recommendations or user requests"""
    if job_id not in jobs or job_id not in data_storage:
        raise HTTPException(status_code=404, detail="Job or data not found")
    
    job = jobs[job_id]
    # if job['user_id'] != current_user.id:
    #     raise HTTPException(status_code=403, detail="Access denied")
    
    data = data_storage[job_id]
    
    if request.action == "filter":
        # Filter data based on confidence or other criteria
        min_confidence = request.parameters.get("min_confidence", 0.8)
        filtered_data = [d for d in data if d.get('confidence', 0) >= min_confidence]
        data_storage[job_id] = filtered_data
        
        return {
            "action": "filter",
            "result": f"Filtered dataset from {len(data)} to {len(filtered_data)} samples",
            "removed": len(data) - len(filtered_data)
        }
    
    elif request.action == "balance":
        # Balance label distribution
        target = request.parameters.get("target_distribution", "equal")
        
        # Count current distribution
        label_counts = {}
        for item in data:
            label = item.get('label', 'unknown')
            label_counts[label] = label_counts.get(label, 0) + 1
        
        if target == "equal":
            # Find minimum count
            min_count = min(label_counts.values())
            balanced_data = []
            
            for label in label_counts:
                label_data = [d for d in data if d.get('label') == label]
                balanced_data.extend(label_data[:min_count])
            
            data_storage[job_id] = balanced_data
            
            return {
                "action": "balance",
                "result": f"Balanced dataset to {len(balanced_data)} samples",
                "distribution": {label: min_count for label in label_counts}
            }
    
    elif request.action == "augment":
        # Generate more data for specific labels
        target_label = request.parameters.get("label")
        count = request.parameters.get("count", 1000)
        
        # Start background augmentation
        background_tasks.add_task(
            augment_data,
            job_id,
            target_label,
            count,
            job['config']['task_info']
        )
        
        return {
            "action": "augment",
            "result": f"Started generating {count} more samples for label '{target_label}'",
            "status": "processing"
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

@router.get("/job/{job_id}/export")
async def export_processed_data(
    job_id: str,
    format: str = "jsonl",  # jsonl, csv, json
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Export processed data in training-ready format"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    # if job['user_id'] != current_user.id:
    #     raise HTTPException(status_code=403, detail="Access denied")
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Get processed data
    data = data_storage.get(job_id, [])
    
    if format == "jsonl":
        # Export as JSONL format (one JSON object per line)
        lines = []
        for item in data:
            # Create training-ready format
            training_item = {
                "text": item.get("text", ""),
                "label": item.get("label", "unknown"),
                "metadata": {
                    "title": item.get("title", ""),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "task_type": item.get("task_type", ""),
                    "processed_at": item.get("processed_at", "")
                }
            }
            lines.append(json.dumps(training_item, ensure_ascii=False))
        
        return {
            "format": "jsonl",
            "total_samples": len(lines),
            "content": "\n".join(lines)
        }
    
    elif format == "csv":
        # Export as CSV format
        import io
        output = io.StringIO()
        
        # Write header
        output.write("text,label,title,source,url,task_type,processed_at\n")
        
        # Write data rows
        for item in data:
            # Escape commas and quotes in text
            text = str(item.get("text", "")).replace('"', '""')
            label = str(item.get("label", "unknown"))
            title = str(item.get("title", "")).replace('"', '""')
            source = str(item.get("source", ""))
            url = str(item.get("url", ""))
            task_type = str(item.get("task_type", ""))
            processed_at = str(item.get("processed_at", ""))
            
            output.write(f'"{text}","{label}","{title}","{source}","{url}","{task_type}","{processed_at}"\n')
        
        return {
            "format": "csv",
            "total_samples": len(data),
            "content": output.getvalue()
        }
    
    elif format == "json":
        # Export as JSON array
        training_data = []
        for item in data:
            training_item = {
                "text": item.get("text", ""),
                "label": item.get("label", "unknown"),
                "metadata": {
                    "title": item.get("title", ""),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "task_type": item.get("task_type", ""),
                    "processed_at": item.get("processed_at", "")
                }
            }
            training_data.append(training_item)
        
        return {
            "format": "json",
            "total_samples": len(training_data),
            "data": training_data
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Supported formats: jsonl, csv, json")

async def generate_ai_data(collected_data: List[Dict], count_needed: int, task_info: Dict):
    """Generate additional training data using AI when web collection is insufficient"""
    from app.core.config import settings
    from openai import AsyncOpenAI
    
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Analyze existing data to understand patterns
        sample_data = collected_data[:10] if collected_data else []
        task_type = task_info.get('type', 'classification')
        task_description = task_info.get('task', '')
        language = task_info.get('language', 'chinese')
        
        # Create generation prompt based on task type and existing data
        generation_prompt = f"""
You are a data generation expert. I need you to generate {min(count_needed, 100)} high-quality training samples for this task:

Task: {task_description}
Type: {task_type}
Language: {language}

{"Based on these existing samples:" if sample_data else ""}
{chr(10).join([f"- {item.get('text', '')[:100]}..." for item in sample_data[:3]])}

Generate diverse, high-quality training data in JSON format:
[
  {{"text": "sample text content", "label": "appropriate_label", "source": "ai_generated"}},
  ...
]

Requirements:
1. Generate exactly {min(count_needed, 100)} samples
2. Ensure high diversity and quality
3. Make content realistic and useful for training
4. Use appropriate labels for the task type
5. Content should be in {language}
"""

        # Generate data in batches
        batch_size = 100
        generated_count = 0
        
        while generated_count < count_needed:
            current_batch_size = min(batch_size, count_needed - generated_count)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a training data generation expert. Always return valid JSON."},
                    {"role": "user", "content": generation_prompt.replace(str(min(count_needed, 100)), str(current_batch_size))}
                ],
                temperature=0.8,  # Higher temperature for diversity
                response_format={"type": "json_object"}
            )
            
            try:
                generated_data = json.loads(response.choices[0].message.content)
                if isinstance(generated_data, dict) and 'samples' in generated_data:
                    batch_samples = generated_data['samples']
                elif isinstance(generated_data, list):
                    batch_samples = generated_data
                else:
                    batch_samples = [generated_data]
                
                # Add generated samples to collected_data
                for item in batch_samples:
                    if generated_count >= count_needed:
                        break
                    if isinstance(item, dict) and 'text' in item:
                        item['source'] = 'ai_generated'
                        item['url'] = ''
                        item['title'] = f"AI Generated Sample {generated_count + 1}"
                        collected_data.append(item)
                        generated_count += 1
                        
            except json.JSONDecodeError:
                print(f"Failed to parse AI generated data: {response.choices[0].message.content[:200]}")
                break
                
        print(f"Generated {generated_count} AI samples to supplement web collection")
        
    except Exception as e:
        print(f"AI data generation error: {e}")

def calculate_data_quality(item: Dict) -> float:
    """Calculate data quality score (0.0 to 1.0) based on multiple factors"""
    score = 0.0
    
    text = item.get('text', '')
    title = item.get('title', '')
    url = item.get('url', '')
    source = item.get('source', '')
    
    # Text length quality (optimal range: 50-1000 characters)
    text_len = len(text)
    if text_len >= 50:
        if text_len <= 500:
            score += 0.3  # Perfect length
        elif text_len <= 1000:
            score += 0.25  # Good length
        elif text_len <= 2000:
            score += 0.2   # Acceptable length
        else:
            score += 0.1   # Too long but has content
    elif text_len >= 20:
        score += 0.15  # Short but usable
    
    # Content relevance (simple keyword matching)
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in ['中医', '治疗', '诊断', '症状', '方剂', '药物', '针灸', '推拿']):
        score += 0.25  # Relevant medical content
    elif any(keyword in text_lower for keyword in ['医学', '健康', '疾病', '病症', '疗法']):
        score += 0.2   # Related medical content
    elif any(keyword in text_lower for keyword in ['保健', '养生', '体质', '调理']):
        score += 0.15  # Health-related content
    
    # Title quality
    if title and len(title) > 10:
        score += 0.15
    elif title:
        score += 0.1
    
    # Source reliability
    if source == 'scrapingbee_enhanced':
        score += 0.15  # Enhanced extraction
    elif source == 'google_search':
        score += 0.1   # Standard search result
    
    # URL quality (authoritative domains)
    if url:
        if any(domain in url for domain in ['.gov.cn', '.edu.cn', '.org']):
            score += 0.15  # Authoritative source
        elif any(domain in url for domain in ['.com', '.net']):
            score += 0.1   # Standard domain
        else:
            score += 0.05  # Has URL
    
    # Cap at 1.0 and ensure minimum of 0.1 for valid data
    return min(max(score, 0.1), 1.0)

async def process_with_dfe(collected_data: List[Dict], task_info: Dict) -> List[Dict]:
    """Process collected data through DFE for training readiness"""
    try:
        # Create field alignment mapping based on task type
        task_type = task_info.get('type', 'classification')
        task_labels = task_info.get('labels', [])
        
        # Define field alignment for different task types
        field_alignment = {
            'text': ['content', 'text', 'snippet', 'main_content', 'body', 'description'],
            'title': ['title', 'name', 'subject', 'headline'],
            'url': ['url', 'link', 'source_url'],
            'source': ['source', 'origin', 'provider']
        }
        
        # Add task-specific fields
        if task_type == 'classification':
            field_alignment['label'] = ['label', 'category', 'class', 'type']
        elif task_type == 'sentiment':
            field_alignment['sentiment'] = ['sentiment', 'emotion', 'feeling', 'mood']
        elif task_type == 'ner':
            field_alignment['entities'] = ['entities', 'named_entities', 'tags']
        elif task_type == 'qa':
            field_alignment['question'] = ['question', 'query', 'q']
            field_alignment['answer'] = ['answer', 'response', 'a']
        
        processed_data = []
        
        for item in collected_data:
            # Apply field alignment
            aligned_item = {}
            
            # Map fields according to alignment rules
            for target_field, source_fields in field_alignment.items():
                for source_field in source_fields:
                    if source_field in item and item[source_field]:
                        aligned_item[target_field] = item[source_field]
                        break
                else:
                    # Set default values for missing fields
                    if target_field == 'label':
                        # For classification tasks, set initial label as 'unknown'
                        aligned_item[target_field] = 'unknown'
                    elif target_field == 'sentiment':
                        aligned_item[target_field] = 'neutral'
                    elif target_field == 'entities':
                        aligned_item[target_field] = []
            
            # Ensure text field exists (required for all tasks)
            if 'text' not in aligned_item or not aligned_item['text']:
                aligned_item['text'] = item.get('snippet', item.get('content', ''))
            
            # Clean and normalize text
            if aligned_item.get('text'):
                # Remove extra whitespace and normalize
                aligned_item['text'] = ' '.join(aligned_item['text'].split())
                
                # Truncate if too long for training
                if len(aligned_item['text']) > 2000:
                    aligned_item['text'] = aligned_item['text'][:2000]
                
                # Calculate data quality score based on content
                quality_score = calculate_data_quality(aligned_item)
                aligned_item['confidence'] = quality_score
            else:
                # Set default low quality for items without text
                aligned_item['confidence'] = 0.1
            
            # Add metadata
            aligned_item['processed_at'] = datetime.utcnow().isoformat()
            aligned_item['task_type'] = task_type
            aligned_item['processed_by'] = 'dfe'
            
            # Keep original data for reference
            aligned_item['_original'] = item
            
            processed_data.append(aligned_item)
        
        return processed_data
        
    except Exception as e:
        print(f"DFE processing error: {e}")
        # Return original data if processing fails
        return collected_data

async def augment_data(job_id: str, target_label: str, count: int, task_info: Dict):
    """Background task to augment data with more samples"""
    try:
        # Generate more data
        generated = await data_generation_service.generate_training_data(
            task_type=task_info.get('type', 'classification'),
            task_description=f"Generate {target_label} examples for {task_info.get('task', '')}",
            count=count,
            labels=[target_label],
            style="diverse"
        )
        
        # Add to existing data
        if job_id in data_storage:
            data_storage[job_id].extend(generated)
            
    except Exception as e:
        print(f"Augmentation failed: {e}") 