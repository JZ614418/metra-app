"""
Test script for Data Builder module
Tests web scraping, AI generation, and file upload endpoints
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# API configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test user credentials
TEST_EMAIL = "jzhe614@gmail.com"
TEST_PASSWORD = "Jz061407"

# Global token
TOKEN = None

async def login():
    """Login and get access token"""
    global TOKEN
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            TOKEN = data["access_token"]
            print(f"✅ Login successful! Token: {TOKEN[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False

async def test_web_scraping():
    """Test web scraping endpoint"""
    print("\n🔍 Testing Web Scraping...")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Test 1: Search for TCM data
    request_data = {
        "query": "traditional chinese medicine acupuncture treatment",
        "max_results": 20,
        "include_full_content": False,
        "sources": ["google", "wikipedia"]
    }
    
    async with httpx.AsyncClient() as client:
        # Start scraping job
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/data-collection/web-scraping",
            headers=headers,
            json=request_data
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✅ Scraping job started: {job_id}")
            
            # Poll for progress
            for i in range(30):  # Max 30 seconds
                await asyncio.sleep(1)
                
                progress_response = await client.get(
                    f"{BASE_URL}{API_PREFIX}/data-collection/job/{job_id}",
                    headers=headers
                )
                
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    print(f"  Progress: {progress_data['progress']}% - Status: {progress_data['status']}")
                    
                    if progress_data['status'] == 'completed':
                        print(f"✅ Scraping completed! Total data points: {progress_data['total_count']}")
                        
                        # Get the data
                        data_response = await client.get(
                            f"{BASE_URL}{API_PREFIX}/data-collection/job/{job_id}/data",
                            headers=headers
                        )
                        
                        if data_response.status_code == 200:
                            data = data_response.json()
                            print(f"  Sample data (first 3):")
                            for item in data['data'][:3]:
                                print(f"    - {item.get('title', 'No title')}: {item['content'][:100]}...")
                        
                        break
                    elif progress_data['status'] == 'failed':
                        print(f"❌ Job failed: {progress_data.get('message', 'Unknown error')}")
                        break
                else:
                    print(f"❌ Failed to get progress: {progress_response.text}")
        else:
            print(f"❌ Failed to start scraping: {response.text}")

async def test_ai_generation():
    """Test AI data generation endpoint"""
    print("\n🤖 Testing AI Generation...")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Test sentiment analysis data generation
    request_data = {
        "task_type": "sentiment_analysis",
        "task_description": "Generate customer reviews for e-commerce products with sentiment labels",
        "count": 30,
        "labels": ["positive", "negative", "neutral"],
        "style": "balanced"
    }
    
    async with httpx.AsyncClient() as client:
        # Start generation job
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/data-collection/ai-generate",
            headers=headers,
            json=request_data
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✅ Generation job started: {job_id}")
            
            # Poll for progress
            for i in range(20):  # Max 20 seconds
                await asyncio.sleep(1)
                
                progress_response = await client.get(
                    f"{BASE_URL}{API_PREFIX}/data-collection/job/{job_id}",
                    headers=headers
                )
                
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    print(f"  Progress: {progress_data['progress']}% - Status: {progress_data['status']}")
                    
                    if progress_data['status'] == 'completed':
                        print(f"✅ Generation completed! Total samples: {progress_data['total_count']}")
                        
                        # Show sample data
                        if progress_data.get('data'):
                            print(f"  Sample generated data:")
                            for label in ["positive", "negative", "neutral"]:
                                samples = [d for d in progress_data['data'] if d.get('label') == label]
                                if samples:
                                    print(f"    {label.upper()} ({len(samples)} samples):")
                                    for sample in samples[:2]:
                                        print(f"      - {sample['content']}")
                        
                        break
                    elif progress_data['status'] == 'failed':
                        print(f"❌ Job failed: {progress_data.get('message', 'Unknown error')}")
                        break
                else:
                    print(f"❌ Failed to get progress: {progress_response.text}")
        else:
            print(f"❌ Failed to start generation: {response.text}")

async def test_file_upload():
    """Test file upload endpoint"""
    print("\n📁 Testing File Upload...")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Create a sample CSV file
    csv_content = """content,label
"This product is amazing! Best purchase ever.",positive
"Terrible quality, complete waste of money.",negative
"It's okay, nothing special but does the job.",neutral
"Excellent customer service and fast shipping!",positive
"Product broke after one day of use.",negative
"""
    
    async with httpx.AsyncClient() as client:
        # Upload file
        files = {
            'file': ('sample_data.csv', csv_content, 'text/csv')
        }
        data = {
            'task_type': 'sentiment_analysis',
            'has_labels': 'true',
            'label_column': 'label',
            'content_column': 'content'
        }
        
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/data-collection/file-upload",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ File uploaded successfully!")
            print(f"  Job ID: {result['job_id']}")
            print(f"  Total data points: {result['total_count']}")
            print(f"  Preview:")
            for item in result.get('preview', []):
                print(f"    - {item['content']} -> {item.get('label', 'no label')}")
        else:
            print(f"❌ Failed to upload file: {response.text}")

async def test_sources():
    """Test available sources endpoint"""
    print("\n📚 Testing Available Sources...")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/data-collection/sources",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Available data sources:")
            for source in data['sources']:
                print(f"  - {source['name']} ({source['id']})")
                print(f"    Description: {source['description']}")
                print(f"    Free quota: {source['free_quota']}")
                print(f"    Requires API key: {source['requires_key']}")
                print()
        else:
            print(f"❌ Failed to get sources: {response.text}")

async def main():
    """Run all tests"""
    print("🚀 Starting Data Builder Tests...")
    print(f"   API URL: {BASE_URL}{API_PREFIX}")
    print(f"   Test User: {TEST_EMAIL}")
    print("-" * 50)
    
    # Login first
    if not await login():
        print("❌ Cannot proceed without login")
        return
    
    # Run tests
    await test_sources()
    await test_web_scraping()
    await test_ai_generation()
    await test_file_upload()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 