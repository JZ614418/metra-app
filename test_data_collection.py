#!/usr/bin/env python3
"""Test script for data collection API endpoints"""

import requests
import json
import time
import sys

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def login():
    """Login and get access token"""
    print("Logging in...")
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        headers={"Content-Type": "application/json"},
        json={
            "email": "jzhe614@gmail.com",
            "password": "Jz061407"
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.json())
        sys.exit(1)

def test_web_scraping(token):
    """Test web scraping endpoint"""
    print("\n=== Testing Web Scraping ===")
    
    # Start web scraping job
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "task_type": "Customer Complaint Classifier",
        "task_description": "Classify customer feedback as complaint or not complaint",
        "data_type": "text",
        "labels": ["Complaint", "Not Complaint"]
    }
    
    print("Starting web scraping job...")
    response = requests.post(
        f"{API_BASE_URL}/data-collection/web-scraping",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        job_id = result["job_id"]
        print(f"✓ Job started: {job_id}")
        
        # Poll for progress
        print("Polling for progress...")
        for i in range(30):  # Poll for up to 60 seconds
            time.sleep(2)
            
            progress_response = requests.get(
                f"{API_BASE_URL}/data-collection/web-scraping/{job_id}",
                headers=headers
            )
            
            if progress_response.status_code == 200:
                progress = progress_response.json()
                print(f"Progress: {progress['progress']}% - Total data: {progress['total_data_collected']}")
                
                if progress['status'] == 'completed':
                    print("✓ Web scraping completed!")
                    print(f"Total data collected: {progress['total_data_collected']}")
                    print("Sites completed:")
                    for site in progress['sites_completed']:
                        print(f"  - {site['name']}: {site['count']} items")
                    break
            else:
                print(f"✗ Failed to get progress: {progress_response.status_code}")
                break
    else:
        print(f"✗ Failed to start web scraping: {response.status_code}")
        print(response.json())

def test_ai_generation(token):
    """Test AI generation endpoint"""
    print("\n=== Testing AI Generation ===")
    
    # Start AI generation job
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "task_type": "Customer Complaint Classifier",
        "task_description": "Classify customer feedback as complaint or not complaint",
        "data_type": "text",
        "labels": ["Complaint", "Not Complaint"],
        "count": 50
    }
    
    print("Starting AI generation job...")
    response = requests.post(
        f"{API_BASE_URL}/data-collection/ai-generate",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        job_id = result["job_id"]
        print(f"✓ Job started: {job_id}")
        
        # Poll for progress
        print("Polling for progress...")
        for i in range(30):  # Poll for up to 30 seconds
            time.sleep(1)
            
            progress_response = requests.get(
                f"{API_BASE_URL}/data-collection/ai-generate/{job_id}",
                headers=headers
            )
            
            if progress_response.status_code == 200:
                progress = progress_response.json()
                print(f"Progress: {progress['progress']}% - Generated: {progress['generated_count']}")
                
                if progress['status'] == 'completed':
                    print("✓ AI generation completed!")
                    print(f"Total generated: {progress['generated_count']}")
                    if progress.get('by_label'):
                        print("By label:")
                        for label, count in progress['by_label'].items():
                            print(f"  - {label}: {count}")
                    break
            else:
                print(f"✗ Failed to get progress: {progress_response.status_code}")
                break
    else:
        print(f"✗ Failed to start AI generation: {response.status_code}")
        print(response.json())

def main():
    """Main test function"""
    print("Testing Data Collection APIs")
    print("=" * 50)
    
    # Login
    token = login()
    
    # Test web scraping
    test_web_scraping(token)
    
    # Test AI generation
    test_ai_generation(token)
    
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    main() 