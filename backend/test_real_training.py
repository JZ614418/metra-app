#!/usr/bin/env python3
"""
Test real training functionality
"""

import asyncio
import httpx

async def test_training_start():
    """Test starting a real training job"""
    
    print("🚀 Testing Real Training Functionality")
    print("=" * 50)
    
    # Use a completed data collection job
    payload = {
        "task_name": "中医症状诊断模型训练测试",
        "task_description": "基于收集的中医数据进行模型微调训练",
        "base_model": "meta/llama-2-7b-chat",
        "data_builder_job_id": "collect_1_1752195932.255954",  # Use a completed job
        "training_mode": "light"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print("1. Testing training start endpoint...")
            response = await client.post(
                "http://localhost:8000/api/v1/training/start",
                json=payload
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                training_id = result.get('training_id')
                print(f"✅ Training started successfully!")
                print(f"   Training ID: {training_id}")
                print(f"   Status: {result.get('status')}")
                print(f"   Platform: {result.get('platform', 'N/A')}")
                
                return training_id
                
            elif response.status_code == 404:
                print("⚠️  Data collection job not found")
                print("   Need to complete a data collection first")
                
            elif response.status_code == 400:
                error = response.json()
                print(f"⚠️  Training validation failed: {error.get('detail')}")
                
            else:
                print(f"⚠️  Unexpected response: {response.text}")
                
        except Exception as e:
            print(f"❌ Training test failed: {e}")
            
        # Test training list endpoint
        try:
            print("\n2. Testing training list endpoint...")
            response = await client.get("http://localhost:8000/api/v1/training/jobs")
            
            if response.status_code == 200:
                jobs = response.json()
                print(f"✅ Found {len(jobs)} training jobs")
                
                for job in jobs[:3]:  # Show first 3
                    print(f"   - {job.get('task_name', 'Unknown')}: {job.get('status', 'Unknown')}")
            else:
                print(f"⚠️  Could not get training jobs: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Training list test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_training_start())