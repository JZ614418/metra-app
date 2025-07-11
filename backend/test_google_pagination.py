#!/usr/bin/env python3
"""
Test Google API pagination and quota
"""

import asyncio
from app.services.data_collection import DataCollectionService

async def test_google_pagination():
    """Test the enhanced Google search with pagination"""
    
    service = DataCollectionService()
    
    print("Testing Google Search API with pagination...")
    print("=" * 50)
    
    # Test different result counts
    test_queries = [
        ("中医诊断", 10),
        ("中医治疗", 50), 
        ("中医症状", 100)
    ]
    
    for query, count in test_queries:
        print(f"\nTesting: '{query}' requesting {count} results")
        print("-" * 40)
        
        try:
            results = await service.search_google(query, count)
            actual_count = len(results)
            
            print(f"✅ Successfully retrieved {actual_count} results")
            
            if actual_count > 0:
                # Show sample result
                sample = results[0]
                print(f"   Sample title: {sample.get('title', 'N/A')[:80]}...")
                print(f"   Sample snippet: {sample.get('snippet', 'N/A')[:120]}...")
                
                # Count unique URLs
                unique_urls = set(r.get('url', '') for r in results)
                print(f"   Unique URLs: {len(unique_urls)}")
                
                # Check for duplicates
                if len(unique_urls) < actual_count:
                    print(f"   ⚠️  Found {actual_count - len(unique_urls)} duplicate URLs")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    print("\n" + "=" * 50)
    print("Google pagination test completed!")

if __name__ == "__main__":
    asyncio.run(test_google_pagination())