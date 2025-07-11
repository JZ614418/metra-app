#!/usr/bin/env python3
"""
Test data quality calculation
"""

import asyncio
import httpx

async def test_data_quality():
    """Test the new data quality calculation"""
    
    print("🔍 Testing Data Quality Calculation")
    print("=" * 50)
    
    # Start a small collection to test quality scoring
    payload = {
        "task_info": {
            "task": "中医症状诊断测试",
            "type": "classification",
            "language": "chinese",
            "labels": ["寒证", "热证", "虚证", "实证"],
            "description": "测试数据质量评分系统"
        },
        "selected_model": {
            "id": "test-model",
            "name": "Test Model",
            "provider": "Test",
            "modelType": "Test"
        },
        "data_count": 100,  # Small test collection
        "quality_mode": "balanced",
        "use_recommendation": False
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print("1. Starting test data collection...")
            response = await client.post(
                "http://localhost:8000/api/v1/data-builder/collect",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            job_id = result["job_id"]
            print(f"✅ Test collection started: {job_id}")
            
            # Wait a bit for collection to complete
            print("2. Waiting for collection to complete...")
            await asyncio.sleep(30)
            
            # Check final results
            response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/progress")
            if response.status_code == 200:
                status = response.json()
                if status.get('status') == 'completed':
                    print(f"✅ Collection completed with {status.get('collected_count', 0)} samples")
                    
                    # Get data with quality scores
                    response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/data?limit=5")
                    if response.status_code == 200:
                        data = response.json()
                        
                        print(f"\n3. Data quality analysis:")
                        print(f"   Total samples: {data.get('total', 0)}")
                        
                        stats = data.get('statistics', {})
                        avg_confidence = stats.get('average_confidence', 0)
                        print(f"   Average quality score: {avg_confidence:.1%}")
                        
                        # Show sample quality scores
                        samples = data.get('data', [])
                        if samples:
                            print(f"\n   Sample quality scores:")
                            for i, sample in enumerate(samples[:3], 1):
                                confidence = sample.get('confidence', 0)
                                text_len = len(sample.get('text', ''))
                                print(f"     Sample {i}: {confidence:.1%} quality (text: {text_len} chars)")
                                print(f"       Text preview: {sample.get('text', '')[:100]}...")
                        
                        if avg_confidence > 0:
                            print(f"\n✅ Data quality calculation working! Average: {avg_confidence:.1%}")
                        else:
                            print(f"\n❌ Data quality still 0.0% - needs more investigation")
                    else:
                        print(f"❌ Could not get data: {response.status_code}")
                else:
                    print(f"⚠️  Collection status: {status.get('status')}")
            else:
                print(f"❌ Could not get status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_data_quality())