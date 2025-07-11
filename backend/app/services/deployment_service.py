import os
import uuid
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
from sqlalchemy.orm import Session
import json
import aiohttp
from fastapi import HTTPException
import replicate
from huggingface_hub import HfApi, create_repo, upload_file

logger = logging.getLogger(__name__)

class DeploymentService:
    """Service for managing model deployments"""
    
    def __init__(self):
        self.hf_api = HfApi()
        self.deployments_file = "deployments.json"
        self._load_deployments()
        
    def _load_deployments(self):
        """Load deployments from local storage"""
        if os.path.exists(self.deployments_file):
            with open(self.deployments_file, 'r') as f:
                self.deployments = json.load(f)
        else:
            self.deployments = {}
            
    def _save_deployments(self):
        """Save deployments to local storage"""
        with open(self.deployments_file, 'w') as f:
            json.dump(self.deployments, f, indent=2)
            
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"sk-metra-{secrets.token_urlsafe(32)}"
        
    def get_trained_models(self, user_id: str) -> List[Dict[str, Any]]:
        """Get list of trained models available for deployment"""
        # In production, this would query the database
        # For now, returning mock data based on training history
        models = []
        
        # Check for completed training tasks
        training_file = f"training_results_{user_id}.json"
        if os.path.exists(training_file):
            with open(training_file, 'r') as f:
                training_data = json.load(f)
                for task_id, result in training_data.items():
                    if result.get("status") == "completed":
                        models.append({
                            "id": task_id,
                            "name": result.get("model_name", "Untitled Model"),
                            "task_type": result.get("task_type", "classification"),
                            "base_model": result.get("base_model", "BERT"),
                            "accuracy": result.get("metrics", {}).get("accuracy", 0.85),
                            "trained_at": result.get("completed_at", datetime.now().isoformat()),
                            "status": "ready",
                            "size": result.get("model_size", "125MB")
                        })
                        
        # Add mock models for demo
        if not models:
            models = [
                {
                    "id": "model-1",
                    "name": "Customer Complaint Classifier",
                    "task_type": "classification",
                    "base_model": "BERT Base",
                    "accuracy": 0.945,
                    "trained_at": (datetime.now() - timedelta(days=2)).isoformat(),
                    "status": "ready",
                    "size": "125MB"
                },
                {
                    "id": "model-2",
                    "name": "Product Review Sentiment",
                    "task_type": "sentiment",
                    "base_model": "RoBERTa",
                    "accuracy": 0.923,
                    "trained_at": (datetime.now() - timedelta(days=5)).isoformat(),
                    "status": "ready",
                    "size": "498MB"
                }
            ]
            
        return models
        
    async def deploy_model(
        self,
        user_id: str,
        model_id: str,
        deployment_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy a trained model"""
        
        deployment_id = str(uuid.uuid4())
        api_key = self.generate_api_key()
        
        # Create deployment record
        deployment = {
            "id": deployment_id,
            "user_id": user_id,
            "model_id": model_id,
            "type": deployment_type,
            "status": "deploying",
            "api_key": api_key,
            "created_at": datetime.now().isoformat(),
            "config": config,
            "metrics": {
                "api_calls": 0,
                "total_requests": 0,
                "errors": 0,
                "avg_response_time": 0,
                "uptime": 100.0
            }
        }
        
        try:
            if deployment_type == "api":
                # Deploy as REST API
                endpoint = await self._deploy_api(model_id, deployment_id, config)
                deployment["endpoint"] = endpoint
                deployment["status"] = "active"
                
            elif deployment_type == "widget":
                # Generate embeddable widget code
                widget_code = self._generate_widget_code(deployment_id, api_key)
                deployment["widget_code"] = widget_code
                deployment["status"] = "active"
                
            elif deployment_type == "export":
                # Export model files
                export_url = await self._export_model(model_id, config.get("format", "onnx"))
                deployment["export_url"] = export_url
                deployment["status"] = "completed"
                
            else:
                raise ValueError(f"Unknown deployment type: {deployment_type}")
                
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            deployment["status"] = "failed"
            deployment["error"] = str(e)
            
        # Save deployment
        self.deployments[deployment_id] = deployment
        self._save_deployments()
        
        return deployment
        
    async def _deploy_api(self, model_id: str, deployment_id: str, config: Dict[str, Any]) -> str:
        """Deploy model as REST API endpoint"""
        # In production, this would deploy to a cloud service
        # For demo, we'll create a mock endpoint
        base_url = os.getenv("API_BASE_URL", "https://api.metra.ai")
        endpoint = f"{base_url}/v1/models/{deployment_id}/predict"
        
        # Simulate deployment delay
        import asyncio
        await asyncio.sleep(2)
        
        return endpoint
        
    def _generate_widget_code(self, deployment_id: str, api_key: str) -> str:
        """Generate embeddable widget code"""
        widget_html = f"""
<!-- Metra AI Widget -->
<div id="metra-widget-{deployment_id}"></div>
<script>
  (function() {{
    const script = document.createElement('script');
    script.src = 'https://cdn.metra.ai/widget.js';
    script.async = true;
    script.onload = function() {{
      MetraWidget.init({{
        deploymentId: '{deployment_id}',
        apiKey: '{api_key}',
        container: 'metra-widget-{deployment_id}'
      }});
    }};
    document.head.appendChild(script);
  }})();
</script>
"""
        return widget_html
        
    async def _export_model(self, model_id: str, format: str) -> str:
        """Export model in specified format"""
        # In production, this would convert and upload the model
        # For demo, return a mock download URL
        export_url = f"https://storage.metra.ai/exports/{model_id}.{format}"
        
        # Simulate export process
        import asyncio
        await asyncio.sleep(3)
        
        return export_url
        
    def get_deployments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all deployments for a user"""
        user_deployments = []
        for deployment in self.deployments.values():
            if deployment["user_id"] == user_id:
                # Add runtime metrics
                deployment["metrics"]["last_used"] = self._calculate_last_used(deployment)
                deployment["metrics"]["health"] = self._calculate_health(deployment)
                user_deployments.append(deployment)
                
        return sorted(user_deployments, key=lambda x: x["created_at"], reverse=True)
        
    def get_deployment(self, deployment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific deployment"""
        deployment = self.deployments.get(deployment_id)
        if deployment and deployment["user_id"] == user_id:
            deployment["metrics"]["last_used"] = self._calculate_last_used(deployment)
            deployment["metrics"]["health"] = self._calculate_health(deployment)
            return deployment
        return None
        
    def update_deployment(self, deployment_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update deployment configuration"""
        deployment = self.deployments.get(deployment_id)
        if deployment and deployment["user_id"] == user_id:
            deployment.update(updates)
            deployment["updated_at"] = datetime.now().isoformat()
            self._save_deployments()
            return deployment
        return None
        
    def delete_deployment(self, deployment_id: str, user_id: str) -> bool:
        """Delete a deployment"""
        deployment = self.deployments.get(deployment_id)
        if deployment and deployment["user_id"] == user_id:
            del self.deployments[deployment_id]
            self._save_deployments()
            return True
        return False
        
    def update_metrics(self, deployment_id: str, metric_type: str, value: Any):
        """Update deployment metrics"""
        if deployment_id in self.deployments:
            metrics = self.deployments[deployment_id]["metrics"]
            
            if metric_type == "api_call":
                metrics["api_calls"] += 1
                metrics["total_requests"] += 1
            elif metric_type == "error":
                metrics["errors"] += 1
            elif metric_type == "response_time":
                # Calculate rolling average
                current_avg = metrics["avg_response_time"]
                total_calls = metrics["api_calls"]
                new_avg = ((current_avg * (total_calls - 1)) + value) / total_calls
                metrics["avg_response_time"] = round(new_avg, 2)
                
            self._save_deployments()
            
    def _calculate_last_used(self, deployment: Dict[str, Any]) -> str:
        """Calculate when deployment was last used"""
        # In production, this would check actual usage logs
        # For demo, return mock data
        if deployment["metrics"]["api_calls"] > 0:
            hours_ago = min(deployment["metrics"]["api_calls"] % 24, 23)
            if hours_ago == 0:
                return "Just now"
            elif hours_ago == 1:
                return "1 hour ago"
            else:
                return f"{hours_ago} hours ago"
        return "Never"
        
    def _calculate_health(self, deployment: Dict[str, Any]) -> int:
        """Calculate deployment health score"""
        if deployment["status"] != "active":
            return 0
            
        # Simple health calculation based on errors and uptime
        error_rate = deployment["metrics"]["errors"] / max(deployment["metrics"]["total_requests"], 1)
        health = int((1 - error_rate) * deployment["metrics"]["uptime"])
        return max(0, min(100, health))
        
    def start_deployment(self, deployment_id: str, user_id: str) -> bool:
        """Start a stopped deployment"""
        deployment = self.deployments.get(deployment_id)
        if deployment and deployment["user_id"] == user_id:
            deployment["status"] = "active"
            deployment["started_at"] = datetime.now().isoformat()
            self._save_deployments()
            return True
        return False
        
    def stop_deployment(self, deployment_id: str, user_id: str) -> bool:
        """Stop an active deployment"""
        deployment = self.deployments.get(deployment_id)
        if deployment and deployment["user_id"] == user_id:
            deployment["status"] = "stopped"
            deployment["stopped_at"] = datetime.now().isoformat()
            self._save_deployments()
            return True
        return False
        
    def test_deployment(self, deployment_id: str, user_id: str, test_input: Dict[str, Any]) -> Dict[str, Any]:
        """Test a deployment with sample input"""
        deployment = self.deployments.get(deployment_id)
        if not deployment or deployment["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Deployment not found")
            
        if deployment["status"] != "active":
            raise HTTPException(status_code=400, detail="Deployment is not active")
            
        # Simulate model prediction
        # In production, this would call the actual deployed model
        result = {
            "prediction": "negative" if "bad" in str(test_input.get("text", "")).lower() else "positive",
            "confidence": 0.87 + (hash(str(test_input)) % 13) / 100,
            "processing_time": 45 + (hash(str(test_input)) % 50),
            "model_version": "1.0.0"
        }
        
        # Update metrics
        self.update_metrics(deployment_id, "api_call", None)
        self.update_metrics(deployment_id, "response_time", result["processing_time"])
        
        return result 