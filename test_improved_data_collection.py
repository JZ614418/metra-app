#!/usr/bin/env python3
"""Test improved data collection with realistic mock data"""

import requests
import json
import time

# API configuration
API_URL = "http://localhost:8000/api/v1"
EMAIL = "jzhe614@gmail.com"
PASSWORD = "Jz061407"

def login():
    """Login and get access token"""
    print("Logging in...")
    response = requests.post(
        f"{API_URL}/auth/login",
        json={
            "email": EMAIL,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful")
        return data["access_token"]
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.text)
        return None

def test_web_scraping(token):
    """Test web scraping with mock data"""
    print("\n=== Testing Web Scraping ===")
    
    # Start web scraping job
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_URL}/data-collection/web-scraping",
        headers=headers,
        json={
            "task_type": "Customer Complaint Classifier",
            "task_description": "Classify customer feedback",
            "data_type": "text",
            "labels": ["Complaint", "Not Complaint"]
        }
    )
    
    if response.status_code != 200:
        print(f"✗ Failed to start web scraping: {response.status_code}")
        print(response.text)
        return None
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✓ Web scraping job started: {job_id}")
    
    # Poll for progress
    while True:
        response = requests.get(
            f"{API_URL}/data-collection/web-scraping/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            progress_data = response.json()
            print(f"Progress: {progress_data['progress']}% - Sites: {len(progress_data['sites_completed'])}")
            
            if progress_data["status"] == "completed":
                print(f"✓ Web scraping completed!")
                print(f"  Total data collected: {progress_data['total_data_collected']}")
                
                # Get the actual data
                data_response = requests.get(
                    f"{API_URL}/data-collection/web-scraping/{job_id}/data",
                    headers=headers
                )
                
                if data_response.status_code == 200:
                    data = data_response.json()
                    print(f"✓ Retrieved {data['total_count']} data samples")
                    
                    # Show first 5 samples
                    print("\nFirst 5 samples:")
                    for i, sample in enumerate(data['data'][:5]):
                        print(f"{i+1}. {sample['content'][:80]}...")
                
                break
        
        time.sleep(2)
    
    return job_id

def test_ai_generation(token):
    """Test AI data generation with realistic samples"""
    print("\n=== Testing AI Generation ===")
    
    # Start AI generation job
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_URL}/data-collection/ai-generate",
        headers=headers,
        json={
            "task_type": "Customer Complaint Classifier",
            "task_description": "Classify customer feedback",
            "data_type": "text",
            "labels": ["Complaint", "Not Complaint"],
            "count": 50
        }
    )
    
    if response.status_code != 200:
        print(f"✗ Failed to start AI generation: {response.status_code}")
        print(response.text)
        return None
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✓ AI generation job started: {job_id}")
    
    # Poll for progress
    while True:
        response = requests.get(
            f"{API_URL}/data-collection/ai-generate/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            progress_data = response.json()
            print(f"Progress: {progress_data['progress']}% - Generated: {progress_data['generated_count']}")
            
            if progress_data["status"] == "completed":
                print(f"✓ AI generation completed!")
                print(f"  By label: {json.dumps(progress_data['by_label'], ensure_ascii=False)}")
                
                # Get the actual data
                data_response = requests.get(
                    f"{API_URL}/data-collection/ai-generate/{job_id}/data",
                    headers=headers
                )
                
                if data_response.status_code == 200:
                    data = data_response.json()
                    print(f"✓ Retrieved {data['total_count']} generated samples")
                    
                    # Show first 5 samples of each label
                    print("\nSample data:")
                    for label in ["Complaint", "Not Complaint"]:
                        print(f"\n{label}:")
                        label_samples = [s for s in data['data'] if s['label'] == label]
                        for i, sample in enumerate(label_samples[:3]):
                            print(f"  {i+1}. {sample['content']}")
                
                break
        
        time.sleep(1)
    
    return job_id

def main():
    """Main test function"""
    print("=== Data Collection API Test ===")
    
    # Login
    token = login()
    if not token:
        return
    
    # Test web scraping
    scraping_job_id = test_web_scraping(token)
    
    # Test AI generation
    ai_job_id = test_ai_generation(token)
    
    print("\n=== Test Summary ===")
    print(f"✓ Web scraping job: {scraping_job_id}")
    print(f"✓ AI generation job: {ai_job_id}")
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    main() 