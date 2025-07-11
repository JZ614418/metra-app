#!/usr/bin/env python3
"""
Test DFE (Data Fusion Engine) functionality
"""

import asyncio
import httpx
import json

async def test_dfe_functionality():
    """Test DFE endpoints and processing"""
    
    print("🔧 Testing DFE (Data Fusion Engine) Module")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Test 1: DFE extraction endpoint
        print("1. Testing DFE extraction endpoint...")
        try:
            test_urls = [
                "https://www.who.int/zh/news-room/fact-sheets/detail/traditional-complementary-and-integrative-medicine",
                "https://en.wikipedia.org/wiki/Traditional_Chinese_medicine"
            ]
            
            dfe_payload = {
                "urls": test_urls,
                "options": {
                    "enable_v2_features": True,
                    "field_alignment": {
                        "title": ["标题", "title", "name"],
                        "content": ["内容", "content", "text"],
                        "author": ["作者", "author", "writer"]
                    },
                    "fill_missing_values": True,
                    "output_format": "json"
                }
            }
            
            response = await client.post(
                "http://localhost:8000/api/v1/dfe/start",
                json=dfe_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ DFE extraction endpoint working")
                print(f"   Task ID: {result.get('task_id', 'N/A')}")
                print(f"   Status: {result.get('status', 'N/A')}")
            else:
                print(f"⚠️  DFE endpoint returned {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ DFE extraction test failed: {e}")
        
        # Test 2: Check if DFE is working in data collection pipeline
        print("\n2. Testing DFE integration in data collection...")
        try:
            # Check our completed 1K job to see if DFE processing worked
            job_id = "collect_1_1752193012.022967"
            
            response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/data?limit=1")
            
            if response.status_code == 200:
                data = response.json()
                samples = data.get('data', [])
                
                if samples:
                    sample = samples[0]
                    
                    # Check if DFE processing markers are present
                    dfe_markers = [
                        'processed_by',
                        'processed_at',
                        'task_type',
                        '_original'
                    ]
                    
                    found_markers = [marker for marker in dfe_markers if marker in sample]
                    
                    print("✅ DFE integration check completed")
                    print(f"   DFE markers found: {found_markers}")
                    print(f"   Processed by: {sample.get('processed_by', 'N/A')}")
                    print(f"   Task type: {sample.get('task_type', 'N/A')}")
                    print(f"   Processed at: {sample.get('processed_at', 'N/A')}")
                    
                    if 'processed_by' in sample and sample['processed_by'] == 'dfe':
                        print("✅ DFE is actively processing data in the pipeline!")
                    else:
                        print("⚠️  DFE processing markers not found - may need attention")
                else:
                    print("⚠️  No sample data found for DFE check")
            else:
                print(f"⚠️  Could not retrieve data for DFE check: {response.status_code}")
                
        except Exception as e:
            print(f"❌ DFE integration test failed: {e}")
        
        # Test 3: Check DFE data processing quality
        print("\n3. Testing DFE data processing quality...")
        try:
            response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/data?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                samples = data.get('data', [])
                
                if samples:
                    processed_count = 0
                    field_alignment_count = 0
                    
                    for sample in samples:
                        # Check if processed by DFE
                        if sample.get('processed_by') == 'dfe':
                            processed_count += 1
                        
                        # Check field alignment (text field should exist)
                        if 'text' in sample and sample['text']:
                            field_alignment_count += 1
                    
                    print(f"✅ DFE quality check completed")
                    print(f"   Samples processed by DFE: {processed_count}/{len(samples)}")
                    print(f"   Samples with aligned fields: {field_alignment_count}/{len(samples)}")
                    
                    if processed_count == len(samples):
                        print("✅ All samples properly processed by DFE!")
                    else:
                        print("⚠️  Some samples not processed by DFE")
                        
                else:
                    print("⚠️  No samples found for quality check")
            else:
                print(f"⚠️  Could not retrieve data for quality check: {response.status_code}")
                
        except Exception as e:
            print(f"❌ DFE quality test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_dfe_functionality())