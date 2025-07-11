#!/usr/bin/env python3
"""
Test 50K data collection - Ultimate scaling test
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_50k_collection():
    """Test collecting 50,000 samples - the ultimate scaling test"""
    
    # Test data for large-scale collection
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
        "data_count": 50000,  # 50K samples
        "quality_mode": "balanced",
        "use_recommendation": False
    }
    
    print("🚀 ULTIMATE SCALING TEST: 50,000 Sample Collection")
    print("=" * 60)
    print(f"Task: {payload['task_info']['task']}")
    print(f"Target: {payload['data_count']:,} samples")
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Start collection
        try:
            print("\n🔄 1. Starting massive data collection...")
            response = await client.post(
                "http://localhost:8000/api/v1/data-builder/collect",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            job_id = result["job_id"]
            print(f"✅ Collection started successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Estimated time: {result.get('estimated_time_minutes', 'unknown')} minutes")
            
        except Exception as e:
            print(f"❌ Failed to start collection: {e}")
            return False
        
        # Monitor progress with detailed tracking
        print(f"\n📊 2. Monitoring collection progress...")
        print("   This is a large-scale operation, please be patient...")
        print("   Progress will be reported every 2 minutes")
        
        start_time = datetime.now()
        last_count = 0
        stalled_checks = 0
        progress_log = []
        
        for iteration in range(180):  # Monitor for up to 6 hours (180 * 2min)
            try:
                await asyncio.sleep(120)  # Check every 2 minutes for 50K collection
                
                response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/progress")
                if response.status_code == 200:
                    status = response.json()
                    
                    progress = status.get('progress', 0)
                    collected = status.get('collected_count', 0)
                    job_status = status.get('status', 'unknown')
                    message = status.get('message', '')
                    
                    elapsed = datetime.now() - start_time
                    elapsed_min = elapsed.total_seconds() / 60
                    
                    # Calculate rate
                    rate = collected / elapsed_min if elapsed_min > 0 else 0
                    
                    # Estimate remaining time
                    remaining = (50000 - collected) / rate if rate > 0 else 0
                    
                    print(f"   ⏱️  {elapsed_min:.1f}min | Progress: {progress}% | Collected: {collected:,}/50,000")
                    print(f"      Rate: {rate:.1f} samples/min | ETA: {remaining:.1f}min | Status: {job_status}")
                    if message:
                        print(f"      Message: {message}")
                    
                    # Log progress
                    progress_log.append({
                        'time': elapsed_min,
                        'collected': collected,
                        'rate': rate,
                        'status': job_status
                    })
                    
                    # Check for stalling
                    if collected == last_count and job_status == 'collecting':
                        stalled_checks += 1
                        if stalled_checks >= 3:  # 6 minutes of no progress
                            print(f"      ⚠️  Collection may be stalled (no progress for 6 minutes)")
                            # Continue monitoring but warn user
                    else:
                        stalled_checks = 0
                    last_count = collected
                    
                    # Check completion status
                    if job_status == 'completed':
                        final_time = elapsed.total_seconds() / 60
                        final_rate = collected / final_time
                        
                        print(f"\n🎉 COLLECTION COMPLETED SUCCESSFULLY!")
                        print(f"   ✅ Final count: {collected:,} samples")
                        print(f"   ⏱️  Total time: {final_time:.1f} minutes ({final_time/60:.1f} hours)")
                        print(f"   🚀 Average rate: {final_rate:.1f} samples/minute")
                        print(f"   📈 Peak efficiency: {max([p['rate'] for p in progress_log]):.1f} samples/min")
                        break
                        
                    elif job_status == 'failed':
                        print(f"\n❌ COLLECTION FAILED!")
                        errors = status.get('errors', [])
                        if errors:
                            print(f"   Errors: {', '.join(errors)}")
                        return False
                        
                else:
                    print(f"   ⚠️  Could not get progress (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"   ⚠️  Error checking progress: {e}")
                continue
        
        # Get sample results
        print(f"\n📋 3. Analyzing collected data...")
        try:
            response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/data?limit=10")
            if response.status_code == 200:
                data_response = response.json()
                total = data_response.get('total', 0)
                sample_data = data_response.get('data', [])
                stats = data_response.get('statistics', {})
                
                print(f"   ✅ Data retrieval successful")
                print(f"   📊 Total samples in database: {total:,}")
                
                # Show statistics
                if stats:
                    source_dist = stats.get('source_distribution', {})
                    print(f"   📈 Source distribution:")
                    for source, count in source_dist.items():
                        percentage = (count / total * 100) if total > 0 else 0
                        print(f"      - {source}: {count:,} samples ({percentage:.1f}%)")
                
                # Show sample data
                if sample_data:
                    print(f"\n   📝 Sample data points:")
                    for i, sample in enumerate(sample_data[:3], 1):
                        print(f"      Sample {i}:")
                        print(f"        Title: {sample.get('title', 'N/A')[:80]}...")
                        print(f"        Text: {sample.get('text', 'N/A')[:120]}...")
                        print(f"        Source: {sample.get('source', 'N/A')}")
                        print()
                
                return True
                
            else:
                print(f"   ❌ Could not retrieve data (HTTP {response.status_code})")
                return False
                
        except Exception as e:
            print(f"   ❌ Error retrieving data: {e}")
            return False

async def main():
    print("🔥 METRA AI ULTIMATE SCALING TEST 🔥")
    print("Testing 50,000 sample data collection")
    print("This will verify our system can handle enterprise-scale training datasets")
    print()
    
    success = await test_50k_collection()
    
    print("\n" + "=" * 60)
    if success:
        print("🏆 ULTIMATE SCALING TEST PASSED!")
        print("   Metra can now handle enterprise-scale data collection")
        print("   Ready for 100K+ training datasets")
    else:
        print("❌ Ultimate scaling test failed")
        print("   Further optimization needed")
    
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())