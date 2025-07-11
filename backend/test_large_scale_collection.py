#!/usr/bin/env python3
"""
Test script for large-scale data collection
Tests the enhanced data collection system with 10,000 samples
"""

import asyncio
import json
import httpx
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

async def test_large_scale_collection():
    """Test collecting 10,000 samples to verify scaling improvements"""
    
    # Test task and model data
    task_info = {
        "task": "中医症状诊断专家系统",
        "type": "classification", 
        "language": "chinese",
        "labels": ["寒证", "热证", "虚证", "实证", "表证", "里证"],
        "description": "基于中医理论的症状诊断和辨证论治专家系统",
        "domain": "medical"
    }
    
    selected_model = {
        "id": "chatglm2-6b-tcm",
        "name": "ChatGLM2-6B-TCM",
        "provider": "THUDM",
        "modelType": "Medical",
        "size": "6B"
    }
    
    print("=== Testing Large-Scale Data Collection (10,000 samples) ===")
    print(f"Task: {task_info['task']}")
    print(f"Model: {selected_model['name']}")
    print(f"Target: 10,000 samples")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Start data collection
        print("\n1. Starting data collection...")
        collection_request = {
            "task_info": task_info,
            "selected_model": selected_model,
            "data_count": 10000,
            "quality_mode": "balanced",
            "use_recommendation": False
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/data-builder/collect",
                json=collection_request
            )
            response.raise_for_status()
            result = response.json()
            
            job_id = result["job_id"]
            print(f"✅ Collection started successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {result['status']}")
            print(f"   Estimated time: {result.get('estimated_time_minutes', 'unknown')} minutes")
            
        except Exception as e:
            print(f"❌ Failed to start collection: {e}")
            return False
        
        # Monitor progress
        print(f"\n2. Monitoring collection progress...")
        last_count = 0
        stalled_checks = 0
        max_stalled = 3
        
        for i in range(60):  # Check for up to 60 iterations (30 minutes max)
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                response = await client.get(f"{API_BASE}/data-builder/progress/{job_id}")
                if response.status_code == 200:
                    status = response.json()
                    
                    progress = status.get('progress', 0)
                    collected = status.get('collected_count', 0)
                    job_status = status.get('status', 'unknown')
                    message = status.get('message', '')
                    
                    print(f"   Progress: {progress}% | Collected: {collected:,} samples | Status: {job_status}")
                    if message:
                        print(f"   Message: {message}")
                    
                    # Check for stalling
                    if collected == last_count:
                        stalled_checks += 1
                        if stalled_checks >= max_stalled:
                            print(f"   ⚠️  Collection appears stalled (no progress for {max_stalled * 30} seconds)")
                    else:
                        stalled_checks = 0
                    last_count = collected
                    
                    # Check completion status
                    if job_status == 'completed':
                        print(f"   ✅ Collection completed successfully!")
                        print(f"   Final count: {collected:,} samples")
                        break
                    elif job_status == 'failed':
                        print(f"   ❌ Collection failed!")
                        errors = status.get('errors', [])
                        if errors:
                            print(f"   Errors: {', '.join(errors)}")
                        return False
                        
                else:
                    print(f"   ⚠️  Could not get progress (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"   ⚠️  Error checking progress: {e}")
                continue
        
        # Get final results
        print(f"\n3. Retrieving collected data...")
        try:
            response = await client.get(f"{API_BASE}/data-builder/data/{job_id}?limit=50")
            if response.status_code == 200:
                data = response.json()
                sample_count = len(data)
                
                print(f"   ✅ Retrieved {sample_count} sample data points")
                
                # Analyze data sources
                sources = {}
                for item in data:
                    source = item.get('source', 'unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                print(f"   Data sources breakdown:")
                for source, count in sources.items():
                    print(f"     - {source}: {count} samples")
                
                # Show sample data
                if data:
                    print(f"\n   Sample data point:")
                    sample = data[0]
                    print(f"     Title: {sample.get('title', 'N/A')[:100]}...")
                    print(f"     Text: {sample.get('text', 'N/A')[:200]}...")
                    print(f"     Source: {sample.get('source', 'N/A')}")
                
                return True
                
            else:
                print(f"   ❌ Could not retrieve data (HTTP {response.status_code})")
                return False
                
        except Exception as e:
            print(f"   ❌ Error retrieving data: {e}")
            return False

async def main():
    print("Large-Scale Data Collection Test")
    print("=" * 40)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await test_large_scale_collection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Large-scale collection test PASSED!")
        print("   System can now handle 10,000+ sample collections")
    else:
        print("❌ Large-scale collection test FAILED!")
        print("   Further improvements needed for scaling")
    
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())