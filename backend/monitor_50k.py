#!/usr/bin/env python3
"""
Monitor 50K collection progress
"""

import asyncio
import httpx
import json
from datetime import datetime

async def monitor_progress():
    """Monitor the 50K collection progress"""
    
    # Get job ID
    try:
        with open('current_50k_job.txt', 'r') as f:
            job_id = f.read().strip()
    except:
        job_id = "collect_1_1752193739.69842"  # Fallback to known job ID
    
    print(f"📊 Monitoring 50K collection progress")
    print(f"Job ID: {job_id}")
    print(f"Check time: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/progress")
            response.raise_for_status()
            status = response.json()
            
            progress = status.get('progress', 0)
            collected = status.get('collected_count', 0)
            job_status = status.get('status', 'unknown')
            message = status.get('message', '')
            
            print(f"📈 Progress: {progress}%")
            print(f"📊 Collected: {collected:,} / 50,000 samples")
            print(f"🔄 Status: {job_status}")
            print(f"💬 Message: {message}")
            
            # Calculate performance metrics
            if collected > 0:
                completion_rate = (collected / 50000) * 100
                print(f"🎯 Completion: {completion_rate:.1f}%")
                
                if progress > 0:
                    estimated_total_time = (100 / progress) * 200  # Based on 200min estimate
                    remaining_time = estimated_total_time * (1 - progress/100)
                    print(f"⏱️  Estimated remaining: {remaining_time:.0f} minutes")
            
            print("=" * 50)
            
            if job_status == 'completed':
                print("🎉 COLLECTION COMPLETED!")
                return True
            elif job_status == 'failed':
                print("❌ COLLECTION FAILED!")
                errors = status.get('errors', [])
                if errors:
                    print(f"Errors: {', '.join(errors)}")
                return False
            else:
                print("✅ Collection in progress...")
                return None
                
        except Exception as e:
            print(f"❌ Error checking progress: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(monitor_progress())