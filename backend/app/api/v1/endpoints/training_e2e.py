"""
End-to-End Training API - Complete workflow from task definition to deployed model
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import json
import logging

from app.api import deps
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.db.supabase_client import supabase_service
from app.services.training_service import training_service
from app.api.v1.endpoints.data_builder import run_optimized_collection, DataCollectionRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response models
class E2ETrainingRequest(BaseModel):
    task_name: str = Field(..., description="Name of the training task")
    task_description: str = Field(..., description="Description of what the model should do")
    task_info: Dict[str, Any] = Field(..., description="Task configuration (type, language, labels, etc.)")
    selected_model: Dict[str, Any] = Field(..., description="Selected base model information")
    data_count: int = Field(default=10000, ge=100, le=100000, description="Number of training samples to collect")
    quality_mode: str = Field(default="balanced", description="Data quality mode: speed/balanced/quality")
    training_config: Optional[Dict[str, Any]] = Field(None, description="Optional training configuration")

class E2ETrainingResponse(BaseModel):
    job_id: str
    status: str
    message: str
    data_collection_job_id: Optional[str] = None
    training_job_id: Optional[str] = None
    estimated_time_minutes: int
    steps: List[Dict[str, Any]]

class E2EProgressResponse(BaseModel):
    job_id: str
    status: str
    current_step: str
    progress: int
    data_collection_progress: Dict[str, Any]
    training_progress: Dict[str, Any]
    message: str
    errors: List[str]

# In-memory storage for E2E jobs (will be moved to Supabase later)
e2e_jobs = {}

@router.post("/start", response_model=E2ETrainingResponse)
async def start_e2e_training(
    request: E2ETrainingRequest,
    background_tasks: BackgroundTasks,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """
    Start complete end-to-end training workflow:
    1. Data collection and processing
    2. Model training
    3. Model export (optional)
    """
    
    # Generate E2E job ID
    job_id = f"e2e_{datetime.utcnow().timestamp()}"
    
    # Initialize E2E job
    e2e_job = {
        'job_id': job_id,
        'user_id': '1',  # Hardcoded for testing
        'task_name': request.task_name,
        'task_description': request.task_description,
        'status': 'initializing',
        'current_step': 'data_collection',
        'progress': 0,
        'data_collection_job_id': None,
        'training_job_id': None,
        'data_collection_progress': {},
        'training_progress': {},
        'errors': [],
        'created_at': datetime.utcnow().isoformat(),
        'config': request.dict(),
        'steps': [
            {'name': 'data_collection', 'status': 'pending', 'progress': 0},
            {'name': 'data_processing', 'status': 'pending', 'progress': 0},
            {'name': 'model_training', 'status': 'pending', 'progress': 0},
            {'name': 'model_export', 'status': 'pending', 'progress': 0}
        ]
    }
    
    e2e_jobs[job_id] = e2e_job
    
    # Start background E2E process
    background_tasks.add_task(
        run_e2e_training,
        job_id,
        request,
        '1'  # Hardcoded user ID for testing
    )
    
    return E2ETrainingResponse(
        job_id=job_id,
        status="started",
        message=f"End-to-end training started for {request.task_name}",
        estimated_time_minutes=estimate_total_time(request.data_count, request.selected_model),
        steps=e2e_job['steps']
    )

async def run_e2e_training(job_id: str, request: E2ETrainingRequest, user_id: str):
    """Background task for complete E2E training workflow"""
    job = e2e_jobs[job_id]
    
    try:
        # Step 1: Data Collection
        logger.info(f"Starting data collection for E2E job {job_id}")
        job['status'] = 'data_collection'
        job['current_step'] = 'data_collection'
        job['progress'] = 10
        job['steps'][0]['status'] = 'running'
        
        # Create data collection request
        data_request = DataCollectionRequest(
            task_info=request.task_info,
            selected_model=request.selected_model,
            data_count=request.data_count,
            quality_mode=request.quality_mode,
            use_recommendation=True
        )
        
        # Run data collection
        data_job_id = f"collect_{user_id}_{datetime.utcnow().timestamp()}"
        job['data_collection_job_id'] = data_job_id
        
        await run_optimized_collection(data_job_id, data_request, int(user_id))
        
        # Poll for data collection completion
        max_polls = 60  # 10 minutes maximum
        poll_count = 0
        
        while poll_count < max_polls:
            poll_count += 1
            
            # Get data collection progress
            try:
                data_job = await supabase_service.get_data_collection_job(data_job_id)
                if not data_job:
                    # Fallback to checking progress another way
                    await asyncio.sleep(10)
                    continue
                
                job['data_collection_progress'] = {
                    'status': data_job['status'],
                    'progress': data_job['progress'],
                    'collected_count': data_job.get('collected_count', 0),
                    'message': data_job.get('message', '')
                }
                
                if data_job['status'] == 'completed':
                    job['steps'][0]['status'] = 'completed'
                    job['steps'][0]['progress'] = 100
                    break
                elif data_job['status'] == 'failed':
                    raise Exception(f"Data collection failed: {data_job.get('message', 'Unknown error')}")
                    
                # Update E2E progress based on data collection
                data_progress = data_job.get('progress', 0)
                job['progress'] = 10 + (data_progress * 0.4)  # Data collection is 40% of total
                
            except Exception as e:
                logger.error(f"Error checking data collection progress: {e}")
                
            await asyncio.sleep(10)
        
        if poll_count >= max_polls:
            raise Exception("Data collection timed out")
        
        # Step 2: Get collected data for training
        logger.info(f"Getting collected data for training in E2E job {job_id}")
        job['current_step'] = 'data_processing'
        job['progress'] = 50
        job['steps'][1]['status'] = 'running'
        
        # Get collected data from Supabase
        collected_data = await supabase_service.get_collected_data(data_job_id, skip=0, limit=request.data_count)
        
        if not collected_data:
            raise Exception("No data collected for training")
        
        job['steps'][1]['status'] = 'completed'
        job['steps'][1]['progress'] = 100
        
        # Step 3: Model Training
        logger.info(f"Starting model training for E2E job {job_id}")
        job['current_step'] = 'model_training'
        job['progress'] = 60
        job['steps'][2]['status'] = 'running'
        
        # Start training
        training_response = await training_service.start_training(
            task_name=request.task_name,
            task_description=request.task_description,
            base_model=request.selected_model.get('model_id', 'meta/llama-2-7b-chat'),
            training_data=collected_data,
            user_id=user_id,
            training_config=request.training_config
        )
        
        training_job_id = training_response['job_id']
        job['training_job_id'] = training_job_id
        
        # Poll for training completion
        max_training_polls = 180  # 30 minutes maximum
        training_poll_count = 0
        
        while training_poll_count < max_training_polls:
            training_poll_count += 1
            
            # Get training progress
            try:
                training_status = await training_service.get_job_status(training_job_id)
                
                if training_status.get('error'):
                    raise Exception(f"Training job error: {training_status['error']}")
                
                job['training_progress'] = {
                    'status': training_status['status'],
                    'progress': training_status['progress'],
                    'message': training_status.get('logs', [])[-1].get('message', '') if training_status.get('logs') else ''
                }
                
                if training_status['status'] == 'completed':
                    job['steps'][2]['status'] = 'completed'
                    job['steps'][2]['progress'] = 100
                    break
                elif training_status['status'] == 'failed':
                    raise Exception(f"Training failed: {training_status.get('error', 'Unknown error')}")
                    
                # Update E2E progress based on training
                training_progress = training_status.get('progress', 0)
                job['progress'] = 60 + (training_progress * 0.3)  # Training is 30% of total
                
            except Exception as e:
                logger.error(f"Error checking training progress: {e}")
                
            await asyncio.sleep(10)
        
        if training_poll_count >= max_training_polls:
            raise Exception("Training timed out")
        
        # Step 4: Model Export (optional)
        logger.info(f"Starting model export for E2E job {job_id}")
        job['current_step'] = 'model_export'
        job['progress'] = 90
        job['steps'][3]['status'] = 'running'
        
        # Export model in PyTorch format
        export_response = await training_service.export_model(training_job_id, "pytorch")
        
        job['steps'][3]['status'] = 'completed'
        job['steps'][3]['progress'] = 100
        
        # Complete E2E job
        job['status'] = 'completed'
        job['progress'] = 100
        job['current_step'] = 'completed'
        
        logger.info(f"E2E training completed successfully for job {job_id}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"E2E training failed for job {job_id}: {error_msg}")
        
        job['status'] = 'failed'
        job['errors'].append(error_msg)
        
        # Mark current step as failed
        for step in job['steps']:
            if step['status'] == 'running':
                step['status'] = 'failed'
                break

@router.get("/job/{job_id}/progress", response_model=E2EProgressResponse)
async def get_e2e_progress(
    job_id: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get progress of end-to-end training job"""
    if job_id not in e2e_jobs:
        raise HTTPException(status_code=404, detail="E2E job not found")
    
    job = e2e_jobs[job_id]
    
    return E2EProgressResponse(
        job_id=job_id,
        status=job['status'],
        current_step=job['current_step'],
        progress=job['progress'],
        data_collection_progress=job.get('data_collection_progress', {}),
        training_progress=job.get('training_progress', {}),
        message=f"Current step: {job['current_step']} ({job['progress']}%)",
        errors=job.get('errors', [])
    )

@router.get("/job/{job_id}/result")
async def get_e2e_result(
    job_id: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get result of completed end-to-end training job"""
    if job_id not in e2e_jobs:
        raise HTTPException(status_code=404, detail="E2E job not found")
    
    job = e2e_jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"E2E job is {job['status']}, not completed")
    
    # Get training result
    training_result = None
    if job['training_job_id']:
        training_result = await training_service.get_job_result(job['training_job_id'])
    
    # Get export info
    export_info = None
    if job['training_job_id']:
        export_info = await training_service.get_export_download_url(job['training_job_id'])
    
    return {
        "job_id": job_id,
        "task_name": job['task_name'],
        "status": job['status'],
        "progress": job['progress'],
        "data_collection_job_id": job['data_collection_job_id'],
        "training_job_id": job['training_job_id'],
        "data_samples_collected": job.get('data_collection_progress', {}).get('collected_count', 0),
        "training_result": training_result,
        "export_info": export_info,
        "created_at": job['created_at'],
        "steps": job['steps']
    }

@router.post("/job/{job_id}/test")
async def test_e2e_model(
    job_id: str,
    test_input: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Test the trained model from E2E job"""
    if job_id not in e2e_jobs:
        raise HTTPException(status_code=404, detail="E2E job not found")
    
    job = e2e_jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"E2E job is {job['status']}, not completed")
    
    if not job['training_job_id']:
        raise HTTPException(status_code=400, detail="No training job found")
    
    # Test the model
    test_result = await training_service.test_model(job['training_job_id'], test_input)
    
    return {
        "job_id": job_id,
        "test_input": test_input,
        "test_result": test_result,
        "model_info": {
            "task_name": job['task_name'],
            "training_job_id": job['training_job_id']
        }
    }

def estimate_total_time(data_count: int, selected_model: Dict) -> int:
    """Estimate total time for E2E training"""
    # Data collection time
    data_time = max(10, data_count // 250)  # ~4 samples per minute
    
    # Training time estimation
    if data_count < 1000:
        training_time = 15
    elif data_count < 5000:
        training_time = 30
    elif data_count < 10000:
        training_time = 60
    else:
        training_time = 120
    
    # Export time
    export_time = 5
    
    return data_time + training_time + export_time