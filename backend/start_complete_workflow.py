#!/usr/bin/env python3
"""
Complete Metra Workflow Test: Data Collection → Training
"""

import asyncio
import httpx
import json
from datetime import datetime

async def complete_workflow_test():
    """Test the complete workflow from data collection to training"""
    
    print("🚀 开始完整的Metra AI训练流程测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Step 1: 数据收集
        print("\n📊 步骤1: 启动数据收集")
        print("-" * 40)
        
        collection_payload = {
            "task_info": {
                "task": "中医智能诊疗助手",
                "type": "text-generation",
                "language": "chinese",
                "labels": ["中医诊断", "症状分析", "治疗方案", "方剂推荐"],
                "description": "基于中医理论的智能诊疗助手，能够分析症状并提供治疗建议",
                "domain": "medical"
            },
            "selected_model": {
                "id": "chatglm2-6b-medical",
                "name": "ChatGLM2-6B-Medical",
                "provider": "THUDM",
                "modelType": "Medical"
            },
            "data_count": 1000,  # 1K samples for testing
            "quality_mode": "balanced",
            "use_recommendation": False
        }
        
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/data-builder/collect",
                json=collection_payload
            )
            response.raise_for_status()
            result = response.json()
            
            job_id = result["job_id"]
            print(f"✅ 数据收集已启动")
            print(f"   任务ID: {job_id}")
            print(f"   目标样本数: 1,000")
            print(f"   预计时间: {result.get('estimated_time_minutes', 'unknown')} 分钟")
            
        except Exception as e:
            print(f"❌ 数据收集启动失败: {e}")
            return False
        
        # Step 2: 监控数据收集进度
        print(f"\n⏳ 步骤2: 监控数据收集进度")
        print("-" * 40)
        
        for attempt in range(30):  # 最多等待15分钟
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/progress")
                if response.status_code == 200:
                    status = response.json()
                    
                    progress = status.get('progress', 0)
                    collected = status.get('collected_count', 0)
                    job_status = status.get('status', 'unknown')
                    message = status.get('message', '')
                    
                    print(f"   进度: {progress}% | 已收集: {collected:,} 样本 | 状态: {job_status}")
                    if message:
                        print(f"   消息: {message}")
                    
                    if job_status == 'completed':
                        print(f"✅ 数据收集完成！共收集 {collected:,} 个样本")
                        break
                    elif job_status == 'failed':
                        print(f"❌ 数据收集失败!")
                        return False
                        
                else:
                    print(f"   ⚠️  无法获取进度 (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"   ⚠️  检查进度时出错: {e}")
                continue
        
        # Step 3: 验证数据质量
        print(f"\n🔍 步骤3: 验证数据质量")
        print("-" * 40)
        
        try:
            response = await client.get(f"http://localhost:8000/api/v1/data-builder/job/{job_id}/data?limit=5")
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                samples = data.get('data', [])
                stats = data.get('statistics', {})
                
                print(f"✅ 数据验证成功")
                print(f"   总样本数: {total:,}")
                print(f"   数据质量: {stats.get('average_confidence', 0):.1%}")
                
                # 显示数据来源分布
                source_dist = stats.get('source_distribution', {})
                print(f"   数据来源:")
                for source, count in source_dist.items():
                    percentage = (count / total * 100) if total > 0 else 0
                    print(f"     - {source}: {count:,} ({percentage:.1f}%)")
                
                # 显示样本预览
                if samples:
                    print(f"   样本预览:")
                    sample = samples[0]
                    print(f"     文本长度: {len(sample.get('text', ''))} 字符")
                    print(f"     质量评分: {sample.get('confidence', 0):.1%}")
                    print(f"     内容预览: {sample.get('text', '')[:100]}...")
                
            else:
                print(f"❌ 数据验证失败 (HTTP {response.status_code})")
                return False
                
        except Exception as e:
            print(f"❌ 数据验证出错: {e}")
            return False
        
        # Step 4: 启动模型训练
        print(f"\n🤖 步骤4: 启动模型训练")
        print("-" * 40)
        
        training_payload = {
            "task_name": "中医智能诊疗助手v1.0",
            "task_description": "基于收集的中医数据训练的智能诊疗助手模型",
            "base_model": "meta/llama-2-7b-chat",
            "data_builder_job_id": job_id,
            "training_mode": "light"  # 使用轻量级训练进行测试
        }
        
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/training/start",
                json=training_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                training_id = result.get('training_id')
                
                print(f"✅ 模型训练已启动")
                print(f"   训练ID: {training_id}")
                print(f"   基础模型: {training_payload['base_model']}")
                print(f"   训练模式: {training_payload['training_mode']}")
                print(f"   数据来源: {job_id}")
                
                return True
                
            else:
                error = response.json()
                print(f"❌ 训练启动失败: {error.get('detail', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ 训练启动出错: {e}")
            return False

async def main():
    print("🏁 Metra AI 完整工作流测试")
    print("测试从数据收集到模型训练的完整流程")
    print()
    
    success = await complete_workflow_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 完整工作流测试成功!")
        print("✅ 数据收集 → ✅ 数据验证 → ✅ 模型训练")
        print()
        print("💡 下一步可以:")
        print("   1. 在前端查看Training模块的真实训练进度")
        print("   2. 监控训练指标和GPU使用情况")
        print("   3. 等待训练完成并测试模型")
    else:
        print("❌ 工作流测试失败")
        print("需要检查具体的错误并修复")
    
    print(f"结束时间: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())