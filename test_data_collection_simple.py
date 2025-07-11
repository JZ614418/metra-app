#!/usr/bin/env python3
"""Simple test script to check if data collection endpoints exist"""

import requests
import json

# API configuration
API_BASE_URL = "http://localhost:8000"

def test_api_docs():
    """Test if API docs are accessible"""
    print("Testing API documentation...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ API documentation is accessible")
            return True
        else:
            print(f"✗ API docs returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to API: {e}")
        return False

def test_endpoints():
    """Test if endpoints exist (will get 401 without auth, but that's OK)"""
    print("\nTesting endpoints existence...")
    
    endpoints = [
        ("POST", "/api/v1/data-collection/web-scraping", "Web Scraping"),
        ("POST", "/api/v1/data-collection/ai-generate", "AI Generation"),
        ("POST", "/api/v1/data-collection/file-upload", "File Upload"),
    ]
    
    for method, endpoint, name in endpoints:
        try:
            if method == "POST":
                response = requests.post(f"{API_BASE_URL}{endpoint}", json={}, timeout=5)
            else:
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            
            # 401 means endpoint exists but needs auth
            # 422 means endpoint exists but validation failed
            if response.status_code in [401, 422]:
                print(f"✓ {name} endpoint exists (requires auth)")
            elif response.status_code == 404:
                print(f"✗ {name} endpoint not found")
            else:
                print(f"? {name} endpoint returned: {response.status_code}")
        except Exception as e:
            print(f"✗ {name} endpoint error: {e}")

def main():
    """Main test function"""
    print("Testing Data Collection API Endpoints")
    print("=" * 50)
    
    # Test if API is running
    if not test_api_docs():
        print("\n❌ Backend server is not running!")
        print("Please start the backend with: ./start-backend.sh")
        return
    
    # Test endpoints
    test_endpoints()
    
    print("\n✅ Basic connectivity test completed!")
    print("\nTo test with authentication, use test_data_collection.py")

if __name__ == "__main__":
    main() 