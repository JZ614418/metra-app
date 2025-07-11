#!/usr/bin/env python3
"""Verify data collection results"""

import requests
import json
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

def check_scraping_job(token, job_id):
    """Check the status of a scraping job"""
    print(f"\nChecking scraping job: {job_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/data-collection/web-scraping/{job_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Job Status: {data['status']}")
        print(f"  Progress: {data['progress']}%")
        print(f"  Total Data Collected: {data['total_data_collected']}")
        
        if data['sites_completed']:
            print("\n  Sites Completed:")
            for site in data['sites_completed']:
                print(f"    - {site['name']}: {site['count']} items (Status: {site['status']})")
        
        if data.get('errors'):
            print("\n  Errors:")
            for error in data['errors']:
                print(f"    - {error}")
        
        return data
    else:
        print(f"✗ Failed to get job status: {response.status_code}")
        return None

def check_generation_job(token, job_id):
    """Check the status of a generation job"""
    print(f"\nChecking generation job: {job_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/data-collection/ai-generate/{job_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Job Status: {data['status']}")
        print(f"  Progress: {data['progress']}%")
        print(f"  Generated Count: {data['generated_count']}")
        
        if data.get('by_label'):
            print("\n  By Label:")
            for label, count in data['by_label'].items():
                print(f"    - {label}: {count}")
        
        return data
    else:
        print(f"✗ Failed to get job status: {response.status_code}")
        return None

def main():
    """Main verification function"""
    print("Data Collection Verification")
    print("=" * 50)
    
    # Login
    token = login()
    
    # Check if there are any job IDs in the command line
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
        
        # Try as scraping job first
        result = check_scraping_job(token, job_id)
        
        # If not found, try as generation job
        if not result:
            result = check_generation_job(token, job_id)
    else:
        print("\nUsage: python verify_data_collection.py <job_id>")
        print("\nExample job IDs from logs:")
        print("  - scrape_99da575a-ce4c-4b46-b8e1-a2dc2c70d1ba_1751533838.140531")
        print("  - scrape_99da575a-ce4c-4b46-b8e1-a2dc2c70d1ba_1751533385.183013")
        print("  - gen_99da575a-ce4c-4b46-b8e1-a2dc2c70d1ba_1751533393.224396")
        
        # Try the most recent job from logs
        print("\nChecking the most recent scraping job...")
        check_scraping_job(token, "scrape_99da575a-ce4c-4b46-b8e1-a2dc2c70d1ba_1751533838.140531")
        
        print("\nChecking a previous completed scraping job...")
        check_scraping_job(token, "scrape_99da575a-ce4c-4b46-b8e1-a2dc2c70d1ba_1751533385.183013")
        
        print("\nChecking a generation job...")
        check_generation_job(token, "gen_99da575a-ce4c-4b46-b8e1-a2dc2c70d1ba_1751533393.224396")

if __name__ == "__main__":
    main() 