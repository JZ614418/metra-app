from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.services.deployment_service import DeploymentService
from app.schemas.user import User
from pydantic import BaseModel

router = APIRouter()
deployment_service = DeploymentService()

class DeploymentRequest(BaseModel):
    model_id: str
    type: str  # api, widget, export
    config: Dict[str, Any] = {}

class TestDeploymentRequest(BaseModel):
    test_input: Dict[str, Any]

@router.get("/models/trained", response_model=List[Dict[str, Any]])
def get_trained_models(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Get list of trained models available for deployment"""
    return deployment_service.get_trained_models(str(current_user.id))

@router.post("/deploy", response_model=Dict[str, Any])
async def deploy_model(
    deployment_request: DeploymentRequest,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Deploy a trained model"""
    deployment = await deployment_service.deploy_model(
        user_id=str(current_user.id),
        model_id=deployment_request.model_id,
        deployment_type=deployment_request.type,
        config=deployment_request.config
    )
    return deployment

@router.get("/", response_model=List[Dict[str, Any]])
def get_deployments(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Get all deployments for the current user"""
    return deployment_service.get_deployments(str(current_user.id))

@router.get("/{deployment_id}", response_model=Dict[str, Any])
def get_deployment(
    deployment_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Get a specific deployment"""
    deployment = deployment_service.get_deployment(deployment_id, str(current_user.id))
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment

@router.put("/{deployment_id}", response_model=Dict[str, Any])
def update_deployment(
    deployment_id: str,
    updates: Dict[str, Any] = Body(...),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Update deployment configuration"""
    deployment = deployment_service.update_deployment(
        deployment_id, str(current_user.id), updates
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment

@router.delete("/{deployment_id}")
def delete_deployment(
    deployment_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Delete a deployment"""
    success = deployment_service.delete_deployment(deployment_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return {"status": "deleted"}

@router.post("/{deployment_id}/start")
def start_deployment(
    deployment_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Start a stopped deployment"""
    success = deployment_service.start_deployment(deployment_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return {"status": "started"}

@router.post("/{deployment_id}/stop")
def stop_deployment(
    deployment_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Stop an active deployment"""
    success = deployment_service.stop_deployment(deployment_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return {"status": "stopped"}

@router.post("/{deployment_id}/test", response_model=Dict[str, Any])
def test_deployment(
    deployment_id: str,
    request: TestDeploymentRequest,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Test a deployment with sample input"""
    result = deployment_service.test_deployment(
        deployment_id, str(current_user.id), request.test_input
    )
    return result

@router.get("/{deployment_id}/metrics", response_model=Dict[str, Any])
def get_deployment_metrics(
    deployment_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Get detailed metrics for a deployment"""
    deployment = deployment_service.get_deployment(deployment_id, str(current_user.id))
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Return enhanced metrics
    return {
        "deployment_id": deployment_id,
        "status": deployment["status"],
        "metrics": deployment["metrics"],
        "usage_today": {
            "requests": deployment["metrics"]["api_calls"] % 1000,  # Mock daily usage
            "errors": deployment["metrics"]["errors"] % 10,
            "avg_response_time": deployment["metrics"]["avg_response_time"]
        },
        "usage_this_month": {
            "requests": deployment["metrics"]["total_requests"],
            "errors": deployment["metrics"]["errors"],
            "uptime": deployment["metrics"]["uptime"]
        }
    } 