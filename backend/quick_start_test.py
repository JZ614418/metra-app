#!/usr/bin/env python3
"""
Quick start data collection
"""

import asyncio
import httpx

async def quick_start():
    """Quick start data collection"""
    
    print("🚀 启动中医AI训练数据收集")
    print("=" * 50)
    
    payload = {
        "task_info": {
            "task": "中医智能诊疗助手",
            "type": "text-generation", 
            "language": "chinese",
            "labels": ["中医诊断", "症状分析", "治疗方案"],
            "description": "中医智能诊疗助手训练数据"
        },
        "selected_model": {
            "id": "chatglm2-6b",
            "name": "ChatGLM2-6B", 
            "provider": "THUDM",
            "modelType": "Medical"
        },
        "data_count": 1000,
        "quality_mode": "balanced",
        "use_recommendation": False
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/data-builder/collect",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            job_id = result["job_id"]
            print(f"✅ 数据收集已启动!")
            print(f"任务ID: {job_id}")
            print(f"目标: 1,000 样本")
            
            # Save job ID
            with open('current_job.txt', 'w') as f:
                f.write(job_id)
            
            print(f"\n📊 监控网址: http://localhost:8080/data-viewer/{job_id}")
            print(f"💻 使用 'python monitor_progress.py' 监控进度")
            
        except Exception as e:
            print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    asyncio.run(quick_start())