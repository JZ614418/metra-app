"""
Data Collection API endpoints
Handles web scraping, AI generation, and file uploads
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import asyncio
import os
import csv
import io
from pydantic import BaseModel, Field

from app.api import deps
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.data_collection import data_collection_service
from app.services.data_generation import data_generation_service

router = APIRouter()

# Request/Response models
class WebScrapingRequest(BaseModel):
    query: str = Field(..., description="Search query or topic")
    urls: Optional[List[str]] = Field(None, description="Specific URLs to scrape")
    max_results: int = Field(10000, description="Maximum number of results", ge=100, le=1000000)
    include_full_content: bool = Field(True, description="Whether to fetch full page content (uses ScrapingBee)")
    sources: Optional[List[str]] = Field(None, description="Specific sources to use")
    batch_size: int = Field(1000, description="Number of results per batch", ge=100, le=5000)

class AIGenerationRequest(BaseModel):
    task_type: str = Field(..., description="Type of task (e.g., 'sentiment', 'classification')")
    task_description: str = Field(..., description="Detailed description of the task")
    count: int = Field(10000, description="Number of samples to generate", ge=100, le=1000000)
    labels: Optional[List[str]] = Field(None, description="Labels for classification tasks")
    examples: Optional[List[Dict]] = Field(None, description="Example data for reference")
    style: str = Field("balanced", description="Generation style")
    batch_size: int = Field(100, description="Number of samples per generation batch", ge=10, le=1000)

class DataCollectionResponse(BaseModel):
    status: str
    message: str
    job_id: str
    total_count: int
    preview: Optional[List[Dict]] = None

class JobProgressResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    total_count: int
    message: Optional[str] = None
    errors: List[str] = []
    data: Optional[List[Dict]] = None

# In-memory job storage (in production, use Redis or database)
jobs = {}

async def process_web_scraping_job(job_id: str, request: WebScrapingRequest, user_id: int):
    """Background task to process web scraping"""
    job = jobs[job_id]
    
    try:
        job['status'] = 'processing'
        job['progress'] = 10
        
        # Collect data using the service
        data_points = await data_collection_service.collect_web_data(
            query=request.query,
            urls=request.urls,
            max_results=request.max_results,
            include_full_content=request.include_full_content,
            sources=request.sources
        )
        
        job['progress'] = 90
        job['data'] = data_points
        job['total_count'] = len(data_points)
        
        # Store in database (TODO: implement actual storage)
        # await store_collected_data(user_id, job_id, data_points)
        
        job['status'] = 'completed'
        job['progress'] = 100
        job['message'] = f"Successfully collected {len(data_points)} data points"
        
    except Exception as e:
        job['status'] = 'failed'
        job['errors'].append(str(e))
        job['message'] = f"Job failed: {str(e)}"

async def process_ai_generation_job(job_id: str, request: AIGenerationRequest, user_id: int):
    """Background task to process AI generation"""
    job = jobs[job_id]
    
    try:
        job['status'] = 'processing'
        job['progress'] = 10
        
        # Generate data using the service
        generated_data = await data_generation_service.generate_training_data(
            task_type=request.task_type,
            task_description=request.task_description,
            count=request.count,
            labels=request.labels,
            examples=request.examples,
            style=request.style
        )
        
        job['progress'] = 90
        job['data'] = generated_data
        job['total_count'] = len(generated_data)
        
        # Store in database (TODO: implement actual storage)
        # await store_generated_data(user_id, job_id, generated_data)
        
        job['status'] = 'completed'
        job['progress'] = 100
        job['message'] = f"Successfully generated {len(generated_data)} samples"
        
    except Exception as e:
        job['status'] = 'failed'
        job['errors'].append(str(e))
        job['message'] = f"Job failed: {str(e)}"

@router.post("/web-scraping", response_model=DataCollectionResponse)
async def start_web_scraping(
    request: WebScrapingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a web scraping job to collect data from various sources
    
    Sources include:
    - Google Search API
    - Serper API
    - Wikipedia
    - arXiv
    - ScrapingBee (for whitelisted domains)
    """
    # Generate job ID
    job_id = f"scrape_{current_user.id}_{datetime.utcnow().timestamp()}"
    
    # Initialize job
    jobs[job_id] = {
        'job_id': job_id,
        'user_id': current_user.id,
        'type': 'web_scraping',
        'status': 'pending',
        'progress': 0,
        'total_count': 0,
        'errors': [],
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Start background task
    background_tasks.add_task(
        process_web_scraping_job, 
        job_id, 
        request, 
        current_user.id
    )
    
    return DataCollectionResponse(
        status='started',
        message='Web scraping job started successfully',
        job_id=job_id,
        total_count=0
    )

@router.post("/ai-generate", response_model=DataCollectionResponse)
async def start_ai_generation(
    request: AIGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start an AI data generation job using OpenAI
    
    Generates high-quality training data based on:
    - Task type and description
    - Provided labels
    - Example data (if any)
    - Specified style preferences
    """
    # Generate job ID
    job_id = f"gen_{current_user.id}_{datetime.utcnow().timestamp()}"
    
    # Initialize job
    jobs[job_id] = {
        'job_id': job_id,
        'user_id': current_user.id,
        'type': 'ai_generation',
        'status': 'pending',
        'progress': 0,
        'total_count': 0,
        'errors': [],
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Start background task
    background_tasks.add_task(
        process_ai_generation_job,
        job_id,
        request,
        current_user.id
    )
    
    return DataCollectionResponse(
        status='started',
        message='AI data generation started successfully',
        job_id=job_id,
        total_count=0
    )

@router.post("/file-upload", response_model=DataCollectionResponse)
async def upload_data_file(
    file: UploadFile = File(...),
    task_type: str = Form(...),
    has_labels: bool = Form(False),
    label_column: Optional[str] = Form(None),
    content_column: Optional[str] = Form(None),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a data file (CSV, JSON, TXT) for training
    
    Supported formats:
    - CSV: Must specify content column and optionally label column
    - JSON: Array of objects or JSONL format
    - TXT: One sample per line (no labels)
    """
    # Validate file type
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['csv', 'json', 'jsonl', 'txt']:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload CSV, JSON, JSONL, or TXT files."
        )
    
    # Generate job ID
    job_id = f"upload_{current_user.id}_{datetime.utcnow().timestamp()}"
    
    try:
        # Read file content
        content = await file.read()
        data_points = []
        
        if file_extension == 'csv':
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
            
            for row in csv_reader:
                data_point = {
                    'content': row.get(content_column or 'content', ''),
                    'source': 'file_upload',
                    'file_name': file.filename
                }
                
                if has_labels and label_column:
                    data_point['label'] = row.get(label_column, '')
                
                data_points.append(data_point)
        
        elif file_extension in ['json', 'jsonl']:
            # Parse JSON/JSONL
            if file_extension == 'jsonl':
                # Parse line by line
                lines = content.decode('utf-8').strip().split('\n')
                for line in lines:
                    if line:
                        data_points.append(json.loads(line))
            else:
                # Parse as array
                data = json.loads(content.decode('utf-8'))
                if isinstance(data, list):
                    data_points = data
                else:
                    data_points = [data]
        
        elif file_extension == 'txt':
            # Parse text file (one sample per line)
            lines = content.decode('utf-8').strip().split('\n')
            data_points = [
                {
                    'content': line.strip(),
                    'source': 'file_upload',
                    'file_name': file.filename
                }
                for line in lines if line.strip()
            ]
        
        # Add metadata
        for i, point in enumerate(data_points):
            point['id'] = f"{job_id}_{i}"
            point['timestamp'] = datetime.utcnow().isoformat()
        
        # Store job data
        jobs[job_id] = {
            'job_id': job_id,
            'user_id': current_user.id,
            'type': 'file_upload',
            'status': 'completed',
            'progress': 100,
            'total_count': len(data_points),
            'data': data_points,
            'errors': [],
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Return first 5 samples as preview
        preview = data_points[:5] if len(data_points) > 5 else data_points
        
        return DataCollectionResponse(
            status='completed',
            message=f'Successfully uploaded {len(data_points)} data points from {file.filename}',
            job_id=job_id,
            total_count=len(data_points),
            preview=preview
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/job/{job_id}", response_model=JobProgressResponse)
async def get_job_progress(
    job_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Get progress and status of a data collection job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Verify user owns this job
    if job['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Include data only if job is completed
    include_data = job['status'] == 'completed'
    
    return JobProgressResponse(
        job_id=job_id,
        status=job['status'],
        progress=job['progress'],
        total_count=job['total_count'],
        message=job.get('message'),
        errors=job.get('errors', []),
        data=job.get('data') if include_data else None
    )

@router.get("/job/{job_id}/data")
async def get_job_data(
    job_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Get the collected/generated data from a completed job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Verify user owns this job
    if job['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if job is completed
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job['status']}"
        )
    
    # Get paginated data
    data = job.get('data', [])
    total = len(data)
    paginated_data = data[skip:skip + limit]
    
    return {
        'job_id': job_id,
        'total': total,
        'skip': skip,
        'limit': limit,
        'data': paginated_data
    }

@router.delete("/job/{job_id}")
async def delete_job(
    job_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a job and its associated data"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Verify user owns this job
    if job['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete job
    del jobs[job_id]
    
    return {"message": "Job deleted successfully"}

@router.get("/sources")
async def get_available_sources(
    current_user: User = Depends(deps.get_current_user)
):
    """Get list of available data sources and their capabilities"""
    return {
        "sources": [
            {
                "id": "google",
                "name": "Google Search",
                "description": "Search the web using Google Custom Search API",
                "capabilities": ["search", "snippets"],
                "free_quota": 100,
                "requires_key": True
            },
            {
                "id": "serper",
                "name": "Serper API",
                "description": "Advanced search API with rich results",
                "capabilities": ["search", "snippets", "images"],
                "free_quota": 2500,
                "requires_key": True
            },
            {
                "id": "wikipedia",
                "name": "Wikipedia",
                "description": "Free access to Wikipedia articles",
                "capabilities": ["search", "full_content"],
                "free_quota": "unlimited",
                "requires_key": False
            },
            {
                "id": "arxiv",
                "name": "arXiv",
                "description": "Scientific papers and research",
                "capabilities": ["search", "abstracts", "pdfs"],
                "free_quota": "unlimited",
                "requires_key": False
            },
            {
                "id": "pubmed",
                "name": "PubMed",
                "description": "Medical and life science literature",
                "capabilities": ["search", "abstracts"],
                "free_quota": "unlimited",
                "requires_key": False
            },
            {
                "id": "scrapingbee",
                "name": "ScrapingBee",
                "description": "Full page content extraction (whitelisted sites only)",
                "capabilities": ["full_content", "javascript_rendering"],
                "free_quota": 1000,
                "requires_key": True
            }
        ]
    } 