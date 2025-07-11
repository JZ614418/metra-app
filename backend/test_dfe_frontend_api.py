#!/usr/bin/env python3
"""
Test DFE frontend API endpoints
"""

import asyncio
import httpx

async def test_dfe_frontend_apis():
    """Test DFE APIs that frontend expects"""
    
    print("🔧 Testing DFE Frontend API Endpoints")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Available tasks endpoint
        print("1. Testing available tasks endpoint...")
        try:
            response = await client.get("http://localhost:8000/api/v1/dfe/available-tasks")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                tasks = response.json()
                print(f"   ✅ Found {len(tasks)} available tasks")
                if tasks:
                    print(f"   Sample task: {tasks[0].get('task_name', 'N/A')}")
            elif response.status_code == 404:
                print("   ⚠️  Endpoint not found - may need implementation")
            else:
                print(f"   ⚠️  Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Process task endpoint  
        print("\n2. Testing process task endpoint...")
        try:
            # Use our completed job ID
            job_id = "collect_1_1752193012.022967"
            
            response = await client.post(f"http://localhost:8000/api/v1/dfe/process-task/{job_id}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Processing started")
                print(f"   Task ID: {result.get('task_id', 'N/A')}")
            elif response.status_code == 404:
                print("   ⚠️  Endpoint not found - may need implementation")
            else:
                print(f"   ⚠️  Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Status endpoint
        print("\n3. Testing status endpoint...")
        try:
            # Use a test task ID
            task_id = "test-task-123"
            
            response = await client.get(f"http://localhost:8000/api/v1/dfe/status/{task_id}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                status = response.json()
                print(f"   ✅ Status retrieved")
                print(f"   Task status: {status.get('status', 'N/A')}")
            elif response.status_code == 404:
                print("   ⚠️  Task not found or endpoint not implemented")
            else:
                print(f"   ⚠️  Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Results endpoint
        print("\n4. Testing results endpoint...")
        try:
            task_id = "test-task-123"
            
            response = await client.get(f"http://localhost:8000/api/v1/dfe/results/{task_id}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json()
                print(f"   ✅ Results retrieved")
                print(f"   Results type: {type(results)}")
            elif response.status_code == 404:
                print("   ⚠️  Results not found or endpoint not implemented")
            else:
                print(f"   ⚠️  Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_dfe_frontend_apis())