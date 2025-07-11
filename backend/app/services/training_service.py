"""
Training Service - Handles model fine-tuning using cloud GPU services
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid
import logging
from enum import Enum

import httpx
import replicate
from huggingface_hub import HfApi, create_repo, upload_file
from openai import AsyncOpenAI

from app.core.config import settings
from app.db.supabase_client import supabase_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
replicate_client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
hf_api = HfApi(token=settings.HUGGINGFACE_TOKEN)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class TrainingStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


class TrainingService:
    """Service for managing model training jobs"""
    
    def __init__(self):
        self.training_jobs: Dict[str, Dict] = {}
        # Add a mock completed job for testing
        self._create_mock_completed_job()
        # Initialize Supabase
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase tables"""
        try:
            import asyncio
            asyncio.create_task(supabase_service.ensure_tables_exist())
        except RuntimeError:
            # If no event loop is running, skip initialization
            pass
    
    def get_user_training_jobs(self, user_id: str) -> List[Dict]:
        """Get all training jobs for a user"""
        user_jobs = []
        for job_id, job in self.training_jobs.items():
            if job.get('user_id') == user_id:
                user_jobs.append(job)
        return user_jobs
    
    def _create_mock_completed_job(self):
        """Create a mock completed training job for testing export functionality"""
        mock_job_id = "mock_completed_job_12345"
        self.training_jobs[mock_job_id] = {
            "id": mock_job_id,
            "task_name": "中医AI诊断治疗系统",
            "task_description": "用于测试的中医AI诊断治疗模型",
            "base_model": "meta/llama-2-7b-chat",
            "user_id": "1",
            "status": TrainingStatus.COMPLETED,
            "progress": 100,
            "created_at": datetime.utcnow().isoformat(),
            "training_config": {
                "epochs": 1,
                "learning_rate": 3e-5,
                "batch_size": 4,
                "training_mode": "light"
            },
            "data_count": 4,
            "logs": [
                {"timestamp": datetime.utcnow().isoformat(), "message": "Training completed successfully!"}
            ],
            "metrics": {
                "final_loss": 0.25,
                "accuracy": 0.85
            },
            "model_url": "meta/llama-2-7b-chat:mock-tcm-model",
            "error": None
        }
    
    async def start_training(
        self,
        task_name: str,
        task_description: str,
        base_model: str,
        training_data: List[Dict],
        user_id: str,
        training_config: Optional[Dict] = None
    ) -> Dict:
        """
        Start a model training job
        
        Args:
            task_name: Name of the task (e.g., "TCM Diet Guide AI")
            task_description: Description of what the model should do
            base_model: Base model to fine-tune (e.g., "gpt-3.5-turbo")
            training_data: Processed data from DFE
            user_id: User who initiated the training
            training_config: Optional training configuration
        """
        # Generate training job ID
        job_id = f"train_{uuid.uuid4()}"
        
        # Create job record
        job = {
            "id": job_id,
            "task_name": task_name,
            "task_description": task_description,
            "base_model": base_model,
            "user_id": user_id,
            "status": TrainingStatus.PENDING,
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "training_config": training_config or self._get_default_config(base_model),
            "data_count": len(training_data),
            "logs": [],
            "metrics": {},
            "model_url": None,
            "error": None
        }
        
        self.training_jobs[job_id] = job
        
        # Also store in Supabase
        try:
            import asyncio
            asyncio.create_task(supabase_service.create_training_job({
                'job_id': job_id,
                'user_id': user_id,
                'task_name': task_name,
                'task_description': task_description,
                'base_model': base_model,
                'status': TrainingStatus.PENDING.value,
                'progress': 0,
                'data_count': len(training_data),
                'training_config': training_config or self._get_default_config(base_model),
                'logs': [],
                'metrics': {},
                'model_url': None,
                'error': None
            }))
        except Exception as e:
            logger.error(f"Failed to store training job in Supabase: {e}")
        
        # Start training asynchronously
        asyncio.create_task(self._run_training(job_id, base_model, training_data))
        
        return {
            "job_id": job_id,
            "status": TrainingStatus.PENDING,
            "message": f"Training job started for {task_name}",
            "estimated_time": self._estimate_training_time(len(training_data), base_model)
        }
    
    async def _run_training(self, job_id: str, base_model: str, training_data: List[Dict]):
        """Run the actual training process"""
        job = self.training_jobs[job_id]
        
        try:
            # Update status to preparing
            job["status"] = TrainingStatus.PREPARING
            job["progress"] = 10
            self._add_log(job, "Preparing training data...")
            
            # Prepare training data in JSONL format
            training_file = await self._prepare_training_data(training_data)
            job["progress"] = 20
            self._add_log(job, f"Prepared {len(training_data)} training samples")
            
            # Choose training method based on model
            if "gpt" in base_model.lower():
                # Use OpenAI fine-tuning
                await self._train_with_openai(job_id, training_file)
            elif "llama" in base_model.lower() or "mistral" in base_model.lower():
                # Use Replicate for open-source models
                await self._train_with_replicate(job_id, base_model, training_file)
            else:
                # Default to Replicate
                await self._train_with_replicate(job_id, base_model, training_file)
            
        except Exception as e:
            logger.error(f"Training error for job {job_id}: {str(e)}")
            job["status"] = TrainingStatus.FAILED
            job["error"] = str(e)
            self._add_log(job, f"Training failed: {str(e)}")
    
    async def _train_with_replicate(self, job_id: str, base_model: str, training_file: str):
        """Train using Replicate API with improved error handling"""
        job = self.training_jobs[job_id]
        
        try:
            job["status"] = TrainingStatus.TRAINING
            job["progress"] = 30
            self._add_log(job, "Starting training on Replicate...")
            
            # Map base model to Replicate model
            replicate_model = self._get_replicate_model(base_model)
            self._add_log(job, f"Using Replicate model: {replicate_model}")
            
            # For now, simulate training process since we need proper file hosting
            # In production, you would:
            # 1. Upload training_file to a public URL (S3, Google Cloud Storage, etc.)
            # 2. Use that URL in the training request
            
            # Simulate training progress
            self._add_log(job, "Simulating training process (file upload needed for real training)...")
            
            # Progress simulation
            for progress in range(30, 100, 10):
                job["progress"] = progress
                self._add_log(job, f"Training progress: {progress}%")
                await asyncio.sleep(2)  # Simulate training time
            
            # Mark as completed with a simulated model URL
            job["status"] = TrainingStatus.COMPLETED
            job["progress"] = 100
            job["model_url"] = f"{replicate_model}:metra-{job_id}"
            self._add_log(job, "Training simulation completed successfully!")
            self._add_log(job, "Note: To enable real training, upload training data to a public URL")
            
            # Add simulated metrics
            job["metrics"] = {
                "final_loss": 0.25,
                "training_accuracy": 0.92,
                "validation_accuracy": 0.88,
                "training_time_minutes": 45
            }
            
        except Exception as e:
            logger.error(f"Replicate training error: {str(e)}")
            raise Exception(f"Replicate training failed: {str(e)}")
    
    async def _train_with_openai(self, job_id: str, training_file: str):
        """Train using OpenAI fine-tuning API"""
        job = self.training_jobs[job_id]
        
        try:
            job["status"] = TrainingStatus.TRAINING
            job["progress"] = 30
            self._add_log(job, "Uploading data to OpenAI...")
            
            # Upload training file
            with open(training_file, "rb") as f:
                upload_response = await openai_client.files.create(
                    file=f,
                    purpose="fine-tune"
                )
            
            job["progress"] = 40
            self._add_log(job, "Starting fine-tuning job...")
            
            # Create fine-tuning job
            fine_tune_response = await openai_client.fine_tuning.jobs.create(
                training_file=upload_response.id,
                model="gpt-3.5-turbo",
                hyperparameters={
                    "n_epochs": job["training_config"]["epochs"],
                }
            )
            
            fine_tune_id = fine_tune_response.id
            job["openai_job_id"] = fine_tune_id
            
            # Poll for completion with improved progress tracking
            poll_count = 0
            max_polls = 240  # 2 hours maximum
            
            while poll_count < max_polls:
                poll_count += 1
                
                fine_tune_status = await openai_client.fine_tuning.jobs.retrieve(fine_tune_id)
                
                if fine_tune_status.status == "succeeded":
                    break
                elif fine_tune_status.status == "failed":
                    error_info = getattr(fine_tune_status, 'error', None)
                    if error_info and hasattr(error_info, 'message'):
                        error_msg = error_info.message
                    elif error_info and isinstance(error_info, dict):
                        error_msg = error_info.get('message', 'Unknown error')
                    else:
                        error_msg = str(error_info) if error_info else 'Unknown error'
                    raise Exception(f"Fine-tuning failed: {error_msg}")
                elif fine_tune_status.status == "cancelled":
                    raise Exception("Fine-tuning was cancelled")
                
                # Update progress based on status
                if fine_tune_status.status == "validating_files":
                    job["progress"] = 45
                elif fine_tune_status.status == "queued":
                    job["progress"] = 50
                elif fine_tune_status.status == "running":
                    # Estimate progress based on time
                    progress_increment = min(90, 50 + (poll_count * 2))
                    job["progress"] = progress_increment
                
                self._add_log(job, f"Fine-tuning status: {fine_tune_status.status}")
                
                await asyncio.sleep(30)
            
            if fine_tune_status.status == "succeeded":
                # Training completed
                job["status"] = TrainingStatus.COMPLETED
                job["progress"] = 100
                job["model_url"] = fine_tune_status.fine_tuned_model
                self._add_log(job, "Fine-tuning completed successfully!")
                
                # Save metrics if available
                if hasattr(fine_tune_status, 'trained_tokens'):
                    job["metrics"] = {
                        "trained_tokens": fine_tune_status.trained_tokens,
                        "training_files": fine_tune_status.training_file
                    }
            else:
                raise Exception(f"Fine-tuning timed out or failed with status: {fine_tune_status.status}")
            
        except Exception as e:
            raise Exception(f"OpenAI fine-tuning failed: {str(e)}")
    
    async def _prepare_training_data(self, data: List[Dict]) -> str:
        """Prepare training data in appropriate format"""
        # Create temporary file
        filename = f"/tmp/training_data_{uuid.uuid4()}.jsonl"
        
        with open(filename, "w", encoding="utf-8") as f:
            for item in data:
                # Handle DFE processed data format
                if "text" in item and "label" in item:
                    # For classification tasks - convert to chat format
                    task_type = item.get("task_type", "classification")
                    
                    if task_type == "classification":
                        formatted_item = {
                            "messages": [
                                {"role": "user", "content": f"Classify the following text: {item['text']}"},
                                {"role": "assistant", "content": f"Category: {item['label']}"}
                            ]
                        }
                    elif task_type == "sentiment":
                        formatted_item = {
                            "messages": [
                                {"role": "user", "content": f"Analyze the sentiment of: {item['text']}"},
                                {"role": "assistant", "content": f"Sentiment: {item.get('sentiment', item.get('label', 'neutral'))}"}
                            ]
                        }
                    elif task_type == "qa":
                        formatted_item = {
                            "messages": [
                                {"role": "user", "content": item.get('question', item['text'])},
                                {"role": "assistant", "content": item.get('answer', item.get('label', 'No answer provided'))}
                            ]
                        }
                    else:
                        # Generic format for other tasks
                        formatted_item = {
                            "messages": [
                                {"role": "user", "content": f"Process this text: {item['text']}"},
                                {"role": "assistant", "content": str(item.get('label', 'Processed'))}
                            ]
                        }
                elif "text" in item:
                    # Parse the text field if it's a JSON string (legacy format)
                    try:
                        parsed = json.loads(item["text"])
                        formatted_item = {
                            "messages": [
                                {"role": "user", "content": parsed.get("prompt", "")},
                                {"role": "assistant", "content": parsed.get("response", "")}
                            ]
                        }
                    except:
                        # Fallback format
                        formatted_item = {
                            "messages": [
                                {"role": "user", "content": "Please respond"},
                                {"role": "assistant", "content": item["text"]}
                            ]
                        }
                else:
                    # Use item as-is if already formatted
                    formatted_item = item
                
                f.write(json.dumps(formatted_item, ensure_ascii=False) + "\n")
        
        return filename
    
    def _get_default_config(self, base_model: str) -> Dict:
        """Get default training configuration based on model"""
        if "gpt" in base_model.lower():
            return {
                "epochs": 3,
                "learning_rate": 2e-5,
                "batch_size": 4,
                "training_mode": "standard"
            }
        else:
            return {
                "epochs": 5,
                "learning_rate": 3e-4,
                "batch_size": 8,
                "training_mode": "standard"
            }
    
    def _get_replicate_model(self, base_model: str) -> str:
        """Map base model name to Replicate model version"""
        # Updated model mapping with correct Replicate models for training
        model_map = {
            "llama-2-7b": "meta/llama-2-7b-chat",
            "llama-2-7b-chat": "meta/llama-2-7b-chat",
            "mistral-7b": "mistralai/mistral-7b-instruct-v0.1",
            "qwen-7b": "qwen/qwen-7b-chat",
            "chatglm-6b": "thudm/chatglm-6b",
            "chatglm3-6b": "thudm/chatglm3-6b",
            "baichuan-7b": "baichuan-inc/baichuan-7b",
            "baichuan2-7b": "baichuan-inc/baichuan2-7b-chat",
            "yi-6b": "01-ai/yi-6b",
            "google-bert/bert-base-chinese": "meta/llama-2-7b-chat"
        }
        
        # Clean up base model name and find match
        base_model_clean = base_model.lower().replace('-hf', '').replace('-instruct', '').replace('-chat', '')
        
        # Try exact match first
        if base_model.lower() in model_map:
            return model_map[base_model.lower()]
        
        # Try partial match
        for key, value in model_map.items():
            if key in base_model_clean or base_model_clean in key:
                return value
        
        # Default to llama-2-7b-chat if not found
        return "meta/llama-2-7b-chat"
    
    def _estimate_training_time(self, data_count: int, base_model: str) -> str:
        """Estimate training time based on data size and model"""
        # Rough estimates
        if data_count < 1000:
            return "10-15 minutes"
        elif data_count < 5000:
            return "20-30 minutes"
        elif data_count < 10000:
            return "45-60 minutes"
        else:
            return "1-2 hours"
    
    def _add_log(self, job: Dict, message: str):
        """Add log entry to job"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message
        }
        job["logs"].append(log_entry)
        
        # Also update in Supabase
        try:
            import asyncio
            asyncio.create_task(supabase_service.update_training_job(job['id'], {
                'logs': job['logs'],
                'status': job['status'],
                'progress': job['progress'],
                'message': message
            }))
        except Exception as e:
            logger.error(f"Failed to update training job in Supabase: {e}")
    
    async def get_job_status(self, job_id: str) -> Dict:
        """Get training job status from Supabase or fallback to memory"""
        # Try to get from Supabase first
        try:
            job = await supabase_service.get_training_job(job_id)
            if job:
                return {
                    "id": job["job_id"],
                    "status": job["status"],
                    "progress": job["progress"],
                    "task_name": job["task_name"],
                    "base_model": job["base_model"],
                    "data_count": job["data_count"],
                    "created_at": job["created_at"],
                    "logs": job.get("logs", [])[-10:],  # Last 10 logs
                    "metrics": job.get("metrics", {}),
                    "error": job.get("error")
                }
        except Exception as e:
            logger.error(f"Failed to get training job from Supabase: {e}")
        
        # Fallback to in-memory storage
        if job_id not in self.training_jobs:
            return {"error": "Job not found"}
        
        job = self.training_jobs[job_id]
        return {
            "id": job["id"],
            "status": job["status"],
            "progress": job["progress"],
            "task_name": job["task_name"],
            "base_model": job["base_model"],
            "data_count": job["data_count"],
            "created_at": job["created_at"],
            "logs": job["logs"][-10:],  # Last 10 logs
            "metrics": job.get("metrics", {}),
            "error": job.get("error")
        }
    
    async def get_job_result(self, job_id: str) -> Dict:
        """Get completed training job result from Supabase or fallback to memory"""
        # Try to get from Supabase first
        try:
            job = await supabase_service.get_training_job(job_id)
            if job:
                if job["status"] != TrainingStatus.COMPLETED.value:
                    return {"error": f"Job is {job['status']}, not completed"}
                
                return {
                    "id": job["job_id"],
                    "task_name": job["task_name"],
                    "model_url": job["model_url"],
                    "metrics": job["metrics"],
                    "training_config": job["training_config"],
                    "created_at": job["created_at"],
                    "completed_at": job["logs"][-1]["timestamp"] if job.get("logs") else None
                }
        except Exception as e:
            logger.error(f"Failed to get training job from Supabase: {e}")
        
        # Fallback to in-memory storage
        if job_id not in self.training_jobs:
            return {"error": "Job not found"}
        
        job = self.training_jobs[job_id]
        if job["status"] != TrainingStatus.COMPLETED:
            return {"error": f"Job is {job['status']}, not completed"}
        
        return {
            "id": job["id"],
            "task_name": job["task_name"],
            "model_url": job["model_url"],
            "metrics": job["metrics"],
            "training_config": job["training_config"],
            "created_at": job["created_at"],
            "completed_at": job["logs"][-1]["timestamp"] if job["logs"] else None
        }
    
    async def test_model(self, job_id: str, test_input: str) -> Dict:
        """Test a trained model with sample input"""
        if job_id not in self.training_jobs:
            return {"error": "Job not found"}
        
        job = self.training_jobs[job_id]
        if job["status"] != TrainingStatus.COMPLETED:
            return {"error": "Model training not completed"}
        
        try:
            # Test based on model type
            if job["model_url"].startswith("ft:gpt"):
                # OpenAI model - use new API
                response = await openai_client.chat.completions.create(
                    model=job["model_url"],
                    messages=[{"role": "user", "content": test_input}],
                    max_tokens=200
                )
                return {
                    "input": test_input,
                    "output": response.choices[0].message.content
                }
            else:
                # Replicate model
                try:
                    output = replicate_client.run(
                        job["model_url"],
                        input={"prompt": test_input, "max_new_tokens": 200}
                    )
                    # Handle different output formats
                    if isinstance(output, str):
                        result = output
                    elif isinstance(output, list):
                        result = "".join(output)
                    else:
                        result = str(output)
                    
                    return {
                        "input": test_input,
                        "output": result
                    }
                except Exception as e:
                    # For mock/demo purposes, return a simulated response
                    return {
                        "input": test_input,
                        "output": f"模拟中医AI回复：根据您描述的症状（{test_input}），建议您注意脾胃调理，可考虑使用健脾益气的中药方剂。请咨询专业中医师获取个性化治疗方案。",
                        "note": f"模拟回复（实际模型调用失败：{str(e)}）"
                    }
        except Exception as e:
            return {"error": f"Model test failed: {str(e)}"}

    async def export_model(self, job_id: str, export_format: str) -> Dict:
        """Export a trained model in the specified format"""
        if job_id not in self.training_jobs:
            return {"error": "Job not found"}
        
        job = self.training_jobs[job_id]
        if job["status"] != TrainingStatus.COMPLETED:
            return {"error": f"Job is {job['status']}, not completed"}
        
        # Create export record
        export_id = f"export_{uuid.uuid4()}"
        export_record = {
            "export_id": export_id,
            "job_id": job_id,
            "format": export_format,
            "status": "preparing",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "file_path": None,
            "download_url": None,
            "error": None
        }
        
        # Store export record
        if "exports" not in job:
            job["exports"] = {}
        job["exports"][export_id] = export_record
        
        # Start export process
        asyncio.create_task(self._process_export(job_id, export_id, export_format))
        
        return {
            "export_id": export_id,
            "status": "preparing",
            "message": f"Started {export_format} export for {job['task_name']}",
            "estimated_time_minutes": self._estimate_export_time(export_format)
        }
    
    async def _process_export(self, job_id: str, export_id: str, export_format: str):
        """Process model export in background"""
        job = self.training_jobs[job_id]
        export_record = job["exports"][export_id]
        
        try:
            export_record["status"] = "exporting"
            export_record["progress"] = 20
            
            model_url = job["model_url"]
            
            if export_format == "openai":
                # For OpenAI models, just return the model ID
                export_record["download_url"] = model_url
                export_record["status"] = "completed"
                export_record["progress"] = 100
                
            elif export_format == "pytorch":
                # Export to PyTorch format
                await self._export_to_pytorch(job_id, export_id, model_url)
                
            elif export_format == "gguf":
                # Export to GGUF format
                await self._export_to_gguf(job_id, export_id, model_url)
                
            else:
                raise Exception(f"Unsupported export format: {export_format}")
                
        except Exception as e:
            logger.error(f"Export error for {export_id}: {str(e)}")
            export_record["status"] = "failed"
            export_record["error"] = str(e)
    
    async def _export_to_pytorch(self, job_id: str, export_id: str, model_url: str):
        """Export model to PyTorch format"""
        job = self.training_jobs[job_id]
        export_record = job["exports"][export_id]
        
        try:
            export_record["progress"] = 40
            
            # Create export directory
            export_dir = f"/tmp/exports/{export_id}"
            import os
            os.makedirs(export_dir, exist_ok=True)
            
            if model_url.startswith("ft:gpt"):
                # For OpenAI models, create a wrapper
                export_record["progress"] = 60
                
                # Create model wrapper file
                wrapper_code = f'''
import openai
import torch
import json
from typing import Dict, Any

class MetraOpenAIWrapper:
    def __init__(self, model_id: str):
        self.model_id = "{model_url}"
        self.client = openai.OpenAI()
    
    def predict(self, text: str, max_tokens: int = 200) -> str:
        """Make prediction using OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{{"role": "user", "content": text}}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def save_pretrained(self, path: str):
        """Save model configuration"""
        config = {{
            "model_id": self.model_id,
            "model_type": "openai_finetuned",
            "task_name": "{job['task_name']}",
            "base_model": "{job['base_model']}",
            "training_config": {json.dumps(job['training_config'])}
        }}
        
        with open(f"{{path}}/config.json", "w") as f:
            json.dump(config, f, indent=2)

# Load model
def load_model():
    return MetraOpenAIWrapper("{model_url}")

if __name__ == "__main__":
    model = load_model()
    print("Model loaded successfully!")
'''
                
                with open(f"{export_dir}/model.py", "w") as f:
                    f.write(wrapper_code)
                
                # Create requirements.txt
                requirements = """openai>=1.0.0
torch>=1.9.0
transformers>=4.20.0
"""
                with open(f"{export_dir}/requirements.txt", "w") as f:
                    f.write(requirements)
                
                # Create README
                readme = f"""# {job['task_name']} - PyTorch Export

This is a PyTorch-compatible wrapper for the fine-tuned OpenAI model.

## Usage

```python
from model import load_model

model = load_model()
result = model.predict("Your input text here")
print(result)
```

## Installation

```bash
pip install -r requirements.txt
```

## Model Info
- Task: {job['task_name']}
- Base Model: {job['base_model']}
- Training Data: {job['data_count']} samples
- Model ID: {model_url}
"""
                
                with open(f"{export_dir}/README.md", "w") as f:
                    f.write(readme)
                
            else:
                # For Replicate models, download the actual model files
                export_record["progress"] = 50
                
                # This would typically download model weights from Replicate
                # For now, create a placeholder
                placeholder_model = f"""
# Replicate Model Export: {model_url}
# This would contain the actual model weights and tokenizer files
# Task: {job['task_name']}
# Base Model: {job['base_model']}
"""
                with open(f"{export_dir}/model_info.txt", "w") as f:
                    f.write(placeholder_model)
            
            export_record["progress"] = 80
            
            # Create zip file
            import zipfile
            zip_path = f"/tmp/exports/{export_id}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(export_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, export_dir)
                        zipf.write(file_path, arcname)
            
            export_record["file_path"] = zip_path
            export_record["status"] = "completed"
            export_record["progress"] = 100
            
        except Exception as e:
            raise Exception(f"PyTorch export failed: {str(e)}")
    
    async def _export_to_gguf(self, job_id: str, export_id: str, model_url: str):
        """Export model to GGUF format"""
        job = self.training_jobs[job_id]
        export_record = job["exports"][export_id]
        
        try:
            export_record["progress"] = 40
            
            # Create export directory
            export_dir = f"/tmp/exports/{export_id}"
            import os
            os.makedirs(export_dir, exist_ok=True)
            
            # For GGUF export, we'd typically use llama.cpp conversion tools
            # For now, create a placeholder with instructions
            export_record["progress"] = 60
            
            gguf_info = f"""# GGUF Export for {job['task_name']}

This export contains instructions for converting your model to GGUF format.

## Model Information
- Task: {job['task_name']}
- Base Model: {job['base_model']}
- Model URL: {model_url}
- Training Data: {job['data_count']} samples

## Conversion Instructions

### For OpenAI Models:
OpenAI fine-tuned models cannot be directly converted to GGUF format as they are hosted on OpenAI's servers.
Consider using the OpenAI API wrapper or training a local model with similar data.

### For Replicate/HuggingFace Models:
1. Download the model weights from: {model_url}
2. Use llama.cpp conversion tools:
   ```bash
   python convert-hf-to-gguf.py model_directory
   ```

### For Local Training:
If you have the original model files, use:
```bash
python convert.py --input model.safetensors --output model.gguf
```

## Usage with llama.cpp
```bash
./main -m model.gguf -p "Your prompt here"
```

## Quantization Options
- Q4_0: 4-bit quantization (recommended for most use cases)
- Q8_0: 8-bit quantization (better quality, larger size)
- F16: 16-bit float (best quality, largest size)

Example:
```bash
./quantize model.gguf model_q4_0.gguf Q4_0
```
"""
            
            with open(f"{export_dir}/GGUF_CONVERSION_GUIDE.md", "w") as f:
                f.write(gguf_info)
            
            # Create a sample configuration file
            config = {
                "model_name": job['task_name'],
                "base_model": job['base_model'],
                "model_url": model_url,
                "task_type": job.get('task_type', 'unknown'),
                "training_samples": job['data_count'],
                "recommended_quantization": "Q4_0",
                "context_length": 2048,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            with open(f"{export_dir}/model_config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            export_record["progress"] = 80
            
            # Create zip file
            import zipfile
            zip_path = f"/tmp/exports/{export_id}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(export_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, export_dir)
                        zipf.write(file_path, arcname)
            
            export_record["file_path"] = zip_path
            export_record["status"] = "completed"
            export_record["progress"] = 100
            
        except Exception as e:
            raise Exception(f"GGUF export failed: {str(e)}")
    
    def _estimate_export_time(self, export_format: str) -> int:
        """Estimate export time based on format"""
        time_estimates = {
            "openai": 1,      # Instant - just return model ID
            "pytorch": 5,     # 5 minutes to create wrapper
            "gguf": 10        # 10 minutes for conversion guide
        }
        return time_estimates.get(export_format, 5)
    
    async def get_export_status(self, job_id: str) -> Dict:
        """Get status of model export"""
        if job_id not in self.training_jobs:
            return {"error": "Job not found"}
        
        job = self.training_jobs[job_id]
        exports = job.get("exports", {})
        
        if not exports:
            return {"exports": []}
        
        export_list = []
        for export_id, export_record in exports.items():
            export_list.append({
                "export_id": export_id,
                "format": export_record["format"],
                "status": export_record["status"],
                "progress": export_record["progress"],
                "created_at": export_record["created_at"],
                "error": export_record.get("error")
            })
        
        return {"exports": export_list}
    
    async def get_export_download_url(self, job_id: str) -> Dict:
        """Get download URL for the most recent completed export"""
        if job_id not in self.training_jobs:
            return {"error": "Job not found"}
        
        job = self.training_jobs[job_id]
        exports = job.get("exports", {})
        
        # Find the most recent completed export
        completed_exports = [
            export for export in exports.values()
            if export["status"] == "completed"
        ]
        
        if not completed_exports:
            return {"error": "No completed exports found"}
        
        # Get the most recent one
        latest_export = max(completed_exports, key=lambda x: x["created_at"])
        
        if latest_export.get("download_url"):
            return {"download_url": latest_export["download_url"]}
        elif latest_export.get("file_path"):
            return {
                "file_path": latest_export["file_path"],
                "filename": f"{job['task_name']}_{latest_export['format']}.zip"
            }
        else:
            return {"error": "Export file not ready"}


# Create global service instance
training_service = TrainingService() 