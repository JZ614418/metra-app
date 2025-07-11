#!/usr/bin/env python3
"""
Start 50K collection directly via API
"""

import asyncio
import httpx
import json
from datetime import datetime

async def start_50k_collection():
    """Start the 50K collection and get job ID"""
    
    payload = {
        "task_info": {
            "task": "中医临床诊疗知识库",
            "type": "text-generation",
            "language": "chinese",
            "labels": ["中医诊断", "中医治疗", "中医方剂", "中医养生", "中医理论"],
            "description": "构建全面的中医临床诊疗知识库，包含症状诊断、治疗方案、方剂配伍、养生保健等全方位中医知识",
            "domain": "medical"
        },
        "selected_model": {
            "id": "chatglm2-6b-medical",
            "name": "ChatGLM2-6B-Medical",
            "provider": "THUDM",
            "modelType": "Medical"
        },
        "data_count": 50000,
        "quality_mode": "balanced",
        "use_recommendation": False
    }
    
    print("🚀 Starting 50,000 sample collection...")
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/data-builder/collect",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            job_id = result["job_id"]
            print(f"✅ Collection started successfully!")
            print(f"Job ID: {job_id}")
            print(f"Estimated time: {result.get('estimated_time_minutes', 'unknown')} minutes")
            
            # Save job ID for monitoring
            with open('current_50k_job.txt', 'w') as f:
                f.write(job_id)
            
            return job_id
            
        except Exception as e:
            print(f"❌ Failed to start collection: {e}")
            return None

if __name__ == "__main__":
    asyncio.run(start_50k_collection())