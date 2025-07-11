#!/usr/bin/env python3
"""
Test data viewer functionality
"""

import asyncio
import httpx

async def test_data_viewer():
    """Test that we can view collected data properly"""
    
    # Use completed 1K job
    job_id = "collect_1_1752193012.022967"
    
    print(f"Testing data viewer for job: {job_id}")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test data retrieval
            response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/data?limit=3")
            response.raise_for_status()
            data = response.json()
            
            print("✅ Data retrieval successful!")
            print(f"📊 Total samples: {data.get('total', 0)}")
            print(f"📄 Returned samples: {len(data.get('data', []))}")
            
            # Show sample format
            samples = data.get('data', [])
            if samples:
                print("\n📝 Sample data format:")
                sample = samples[0]
                print(f"   Text: {sample.get('text', 'N/A')[:100]}...")
                print(f"   Title: {sample.get('title', 'N/A')[:60]}...")
                print(f"   URL: {sample.get('url', 'N/A')[:60]}...")
                print(f"   Source: {sample.get('source', 'N/A')}")
                print(f"   Label: {sample.get('label', 'N/A')}")
                
                # Check if fields match frontend expectations
                required_fields = ['text', 'title', 'url', 'source', 'label']
                missing_fields = [f for f in required_fields if f not in sample]
                if missing_fields:
                    print(f"   ⚠️  Missing fields: {missing_fields}")
                else:
                    print("   ✅ All required fields present")
            
            # Show statistics
            stats = data.get('statistics', {})
            if stats:
                print("\n📈 Statistics:")
                source_dist = stats.get('source_distribution', {})
                for source, count in source_dist.items():
                    print(f"   - {source}: {count} samples")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_data_viewer())