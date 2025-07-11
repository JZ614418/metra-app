#!/usr/bin/env python3
"""
DFE V1 + V2 功能本地直接调用测试
"""
import asyncio
import json
import sys
import os

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 将项目根目录添加到Python路径，以正确解析app模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 直接从服务导入
from app.services.dfe_service import DFEService

async def test_dfe_v1_local():
    """测试DFE V1基础功能（本地调用）"""
    print("=" * 50)
    print("测试 DFE V1 - 基础网页抓取 (本地)")
    print("=" * 50)
    
    dfe_service = DFEService()
    # 使用有效的URL进行测试
    urls = [
        "https://www.medicalnewstoday.com/articles/265990", # Ginger
        "https://www.healthline.com/nutrition/ginkgo-biloba-benefits" # Ginkgo
    ]
    task_id = "local_v1_task"
    
    # 直接调用服务方法
    await dfe_service.start_extraction(task_id, urls)
    
    # 轮询状态
    while True:
        status = await dfe_service.get_task_status(task_id)
        print(f"   状态: {status['status']} - 进度: {status['progress']}%")
        if status['status'] == 'completed':
            break
        elif status['status'] == 'failed':
            print(f"❌ 任务失败: {status.get('error', '未知错误')}")
            return False
        await asyncio.sleep(1)
        
    # 获取结果
    results = await dfe_service.get_task_results(task_id)
    print(f"\n✅ V1 结果获取成功:")
    print(f"   - 总数: {results['total']}")
    
    if results['results']:
        first_result = results['results'][0]
        print(f"\n   第一个结果示例:")
        print(f"   - URL: {first_result.get('url', 'N/A')}")
        print(f"   - 标题: {first_result.get('title', 'N/A')[:50]}...")
        print(f"   - 内容长度: {len(first_result.get('main_content', ''))} 字符")
        print(f"   - 成功: {first_result.get('success', False)}")
    
    return True

async def test_dfe_v2_local():
    """测试DFE V2高级功能（本地调用）"""
    print("\n" + "=" * 50)
    print("测试 DFE V2 - 高级数据处理 (本地)")
    print("=" * 50)
    
    dfe_service = DFEService()
    urls = [
        "https://www.medicalnewstoday.com/articles/306981", # Turmeric
        "https://www.healthline.com/nutrition/ginkgo-biloba-benefits" # Ginkgo
    ]
    
    v2_options = {
        "enable_v2_features": True,
        "field_alignment": {
            "herb_name": ["title", "name", "herb", "药材名称"],
            "description": ["description", "content", "text", "描述"],
            "benefits": ["benefits", "effects", "功效", "作用"],
            "usage": ["usage", "application", "用法", "使用方法"]
        },
        "fill_missing_values": True,
        "data_augmentation": True,
        "output_format": "jsonl"
    }
    task_id = "local_v2_task"
    
    await dfe_service.start_extraction(task_id, urls, v2_options)
    
    print("\n处理中...")
    while True:
        status = await dfe_service.get_task_status(task_id)
        print(f"   状态: {status['status']} - 进度: {status['progress']}%")
        if status['status'] == 'completed':
            break
        elif status['status'] == 'failed':
            print(f"❌ 任务失败: {status.get('error', '未知错误')}")
            return False
        await asyncio.sleep(1)
        
    results = await dfe_service.get_task_results(task_id)
    print(f"\n✅ V2 结果获取成功:")
    print(f"   - 总数: {results['total']} (包含增强数据)")
    print(f"   - 输出格式: {results['options'].get('output_format', 'json')}")
    
    if results['results']:
        original_count = len([r for r in results['results'] if not json.loads(r['text']).get('is_augmented')])
        augmented_count = len([r for r in results['results'] if json.loads(r['text']).get('is_augmented')])
        
        print(f"\n   数据统计:")
        print(f"   - 原始数据: {original_count}")
        print(f"   - 增强数据: {augmented_count}")
        
        first_result = results['results'][0]
        if 'text' in first_result:
            print(f"\n   JSONL格式示例:")
            parsed = json.loads(first_result['text'])
            for key in ['herb_name', 'description', 'benefits', 'usage']:
                if key in parsed:
                    value = parsed[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"   - {key}: {value}")
    
    return True

async def main():
    """运行所有本地测试"""
    print("开始本地测试 DFE V1 + V2 功能...")

    # 测试V1
    v1_success = await test_dfe_v1_local()
    
    # 测试V2
    v2_success = await test_dfe_v2_local()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"V1 基础功能 (本地): {'✅ 通过' if v1_success else '❌ 失败'}")
    print(f"V2 高级功能 (本地): {'✅ 通过' if v2_success else '❌ 失败'}")
    print("=" * 50)
    
    if all([v1_success, v2_success]):
        print("\n🎉 所有本地测试通过! DFE 服务层功能正常工作")
        return 0
    else:
        print("\n⚠️  部分本地测试失败，请检查日志")
        return 1

if __name__ == "__main__":
    # Run the async main function
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    sys.exit(asyncio.run(main())) 