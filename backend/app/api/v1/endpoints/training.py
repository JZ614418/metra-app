"""
Model Training API endpoints
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.api import deps
from app.services.training_service import training_service
from app.models.user import User

router = APIRouter()


@router.get("/jobs")
async def get_training_jobs(
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get all training jobs for the current user"""
    try:
        jobs = training_service.get_user_training_jobs(user_id="1")  # Hardcoded for testing
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_training(
    task_name: str = Body(..., description="Name of the task"),
    task_description: str = Body(..., description="Description of the task"),
    base_model: str = Body(..., description="Base model to fine-tune"),
    data_builder_job_id: str = Body(..., description="Data Builder job ID with processed data"),
    training_mode: Optional[str] = Body("standard", description="Training mode: light/standard/deep"),
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """
    Start a model training job
    
    Training modes:
    - light: Quick training with fewer epochs (testing)
    - standard: Recommended for most use cases
    - deep: Extended training for best quality
    """
    # Import here to avoid circular imports
    from app.api.v1.endpoints.data_builder import data_storage, jobs
    
    # Get training data from Data Builder
    if data_builder_job_id not in jobs:
        raise HTTPException(status_code=404, detail="Data Builder job not found")
    
    job = jobs[data_builder_job_id]
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Data Builder job not completed yet")
    
    training_data = data_storage.get(data_builder_job_id, [])
    if not training_data:
        raise HTTPException(status_code=400, detail="No training data found for this job")
    
    # Map training mode to config
    training_config = None
    if training_mode == "light":
        training_config = {
            "epochs": 1,
            "learning_rate": 3e-5,
            "batch_size": 4,
            "training_mode": "light"
        }
    elif training_mode == "deep":
        training_config = {
            "epochs": 5,
            "learning_rate": 1e-5,
            "batch_size": 8,
            "training_mode": "deep"
        }
    
    # Start training
    result = await training_service.start_training(
        task_name=task_name,
        task_description=task_description,
        base_model=base_model,
        training_data=training_data,
        user_id="1", # str(current_user.id), # Temporarily hardcoded for testing
        training_config=training_config
    )
    
    return result


@router.get("/status/{job_id}")
async def get_training_status(
    job_id: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """
    Get training job status
    
    Returns:
    - status: pending/preparing/training/completed/failed
    - progress: 0-100
    - logs: Recent training logs
    - metrics: Training metrics (if available)
    """
    status = await training_service.get_job_status(job_id)
    
    if "error" in status and status["error"] == "Job not found":
        raise HTTPException(status_code=404, detail="Training job not found")
    
    return status


@router.get("/result/{job_id}")
async def get_training_result(
    job_id: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """
    Get completed training job result
    
    Returns:
    - model_url: URL/ID of the trained model
    - metrics: Final training metrics
    - training_config: Configuration used
    """
    result = await training_service.get_job_result(job_id)
    
    if "error" in result:
        if result["error"] == "Job not found":
            raise HTTPException(status_code=404, detail="Training job not found")
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/test/{job_id}")
async def test_model(
    job_id: str,
    test_input: str = Body(..., description="Test input for the model"),
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """
    Test a trained model with sample input
    
    Example:
    ```json
    {
        "test_input": "What foods help with inflammation?"
    }
    ```
    """
    result = await training_service.test_model(job_id, test_input)
    
    if "error" in result:
        if result["error"] == "Job not found":
            raise HTTPException(status_code=404, detail="Training job not found")
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/estimate-cost")
async def estimate_training_cost(
    data_count: int,
    base_model: str,
    training_mode: str = "standard"
):
    """
    Estimate training cost based on data size and model
    
    Returns estimated time and cost
    """
    # Simple cost estimation
    base_costs = {
        "gpt-3.5-turbo": 0.0080,  # Per 1K tokens
        "llama-2-7b": 0.65,  # Per hour on T4
        "mistral-7b": 0.65   # Per hour on T4
    }
    
    # Estimate based on data count and mode
    if training_mode == "light":
        time_multiplier = 0.5
    elif training_mode == "deep":
        time_multiplier = 2.0
    else:
        time_multiplier = 1.0
    
    # Base time estimates (in minutes)
    if data_count < 1000:
        base_time = 15
    elif data_count < 5000:
        base_time = 30
    else:
        base_time = 60
    
    estimated_time = base_time * time_multiplier
    
    # Calculate cost
    if "gpt" in base_model:
        # OpenAI charges per token
        estimated_cost = (data_count * 100 * base_costs.get(base_model, 0.008)) / 1000
    else:
        # GPU services charge per hour
        hours = estimated_time / 60
        estimated_cost = hours * base_costs.get(base_model, 0.65)
    
    return {
        "estimated_time_minutes": int(estimated_time),
        "estimated_cost_usd": round(estimated_cost, 2),
        "base_model": base_model,
        "data_count": data_count,
        "training_mode": training_mode
    }

@router.post("/export/{job_id}")
async def export_model(
    job_id: str,
    export_format: str = Body(..., description="Export format: pytorch, gguf, openai"),
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """
    Export a trained model in various formats
    
    Supported formats:
    - pytorch: PyTorch model files (.pt)
    - gguf: GGUF format for llama.cpp
    - openai: OpenAI model ID (for API use)
    """
    result = await training_service.export_model(job_id, export_format)
    
    if "error" in result:
        if result["error"] == "Job not found":
            raise HTTPException(status_code=404, detail="Training job not found")
        elif "not completed" in result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/export/{job_id}/status")
async def get_export_status(
    job_id: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Get the status of a model export job"""
    result = await training_service.get_export_status(job_id)
    
    if "error" in result:
        if result["error"] == "Job not found":
            raise HTTPException(status_code=404, detail="Training job not found")
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/export/{job_id}/download")
async def download_exported_model(
    job_id: str,
    # current_user: User = Depends(deps.get_current_user) # Temporarily disabled for testing
):
    """Download the exported model file"""
    from fastapi.responses import FileResponse
    
    result = await training_service.get_export_download_url(job_id)
    
    if "error" in result:
        if result["error"] == "Job not found":
            raise HTTPException(status_code=404, detail="Training job not found")
        elif "not ready" in result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    # Return download URL or file response
    if result.get("download_url"):
        return {"download_url": result["download_url"]}
    elif result.get("file_path"):
        return FileResponse(
            result["file_path"],
            filename=result.get("filename", "model.zip"),
            media_type="application/zip"
        )
    else:
        raise HTTPException(status_code=500, detail="Export file not available") 