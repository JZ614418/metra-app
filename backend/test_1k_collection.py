#!/usr/bin/env python3
"""
Test 1K data collection to verify the enhanced system
"""

import asyncio
import httpx
import json

async def test_1k_collection():
    """Test collecting 1,000 samples"""
    
    # Test data
    payload = {
        "task_info": {
            "task": "中医症状诊断",
            "type": "classification",
            "language": "chinese",
            "labels": ["寒证", "热证", "虚证", "实证"],
            "description": "中医症状诊断和辨证论治"
        },
        "selected_model": {
            "id": "chatglm2-6b",
            "name": "ChatGLM2-6B",
            "provider": "THUDM",
            "modelType": "General"
        },
        "data_count": 1000,
        "quality_mode": "balanced",
        "use_recommendation": False
    }
    
    print("Testing 1,000 sample collection...")
    print("=" * 40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Start collection
        try:
            print("1. Starting collection...")
            response = await client.post(
                "http://localhost:8000/api/v1/data-builder/collect",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            job_id = result["job_id"]
            print(f"✅ Started! Job ID: {job_id}")
            
        except Exception as e:
            print(f"❌ Failed to start: {e}")
            return
        
        # Quick progress check
        print("2. Checking initial progress...")
        await asyncio.sleep(5)
        
        try:
            response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/progress")
            if response.status_code == 200:
                status = response.json()
                print(f"   Progress: {status.get('progress', 0)}%")
                print(f"   Collected: {status.get('collected_count', 0)} samples")
                print(f"   Status: {status.get('status', 'unknown')}")
                print(f"   Message: {status.get('message', 'N/A')}")
            else:
                print(f"   ⚠️  HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_1k_collection())