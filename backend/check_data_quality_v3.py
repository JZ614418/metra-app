#!/usr/bin/env python3
"""
检查Data Builder V3收集的数据质量
"""

import asyncio
import json
import logging
from app.services.data_builder_v3.pipeline import DataBuilderPipeline
from app.services.fast_data_collector import FastDataCollector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def collect_and_analyze_data():
    """收集并分析数据质量"""
    
    # 1. 使用Data Builder V3收集一些样本
    logger.info("🚀 启动Data Builder V3收集样本...")
    
    pipeline = DataBuilderPipeline()
    
    # 定义一个高质量的任务
    task_definition = {
        "task": "用户评论情感分析",
        "type": "classification",
        "language": "chinese",
        "domain": "电商评论",
        "description": "判断用户对产品的评价是正面还是负面",
        "labels": ["正面评价", "负面评价"],
        "data_volume": 20  # 收集20条样本
    }
    
    # 启动收集
    task_id = await pipeline.start_data_collection(
        task_definition=task_definition,
        target_samples=20
    )
    
    logger.info(f"任务ID: {task_id}")
    
    # 等待收集完成（最多等待2分钟）
    max_wait = 120
    waited = 0
    while waited < max_wait:
        progress = pipeline.active_tasks.get(task_id)
        if progress:
            logger.info(f"进度: {progress.collected_samples}/{progress.target_samples} ({progress.progress:.1f}%)")
            if progress.status in ["completed", "failed"]:
                break
        else:
            # 检查是否在已完成任务中
            completed = False
            for task in pipeline.completed_tasks:
                if task.get("task_id") == task_id:
                    completed = True
                    break
            if completed:
                break
        
        await asyncio.sleep(5)
        waited += 5
    
    # 2. 获取收集的数据
    logger.info("\n📊 分析数据质量...")
    
    # 从storage writer获取数据
    from app.services.data_builder_v3.sqlalchemy_storage_writer import SQLAlchemyStorageWriter
    storage = SQLAlchemyStorageWriter()
    
    # 获取最近的数据样本
    from app.db.session import SessionLocal
    from app.models.data_collection_task import DataCollectionTask
    
    db = SessionLocal()
    try:
        # 查找任务
        task = db.query(DataCollectionTask).filter(
            DataCollectionTask.job_id == task_id
        ).first()
        
        if task and task.collected_data:
            samples = task.collected_data
            
            logger.info(f"\n✅ 成功获取 {len(samples)} 条数据样本")
            
            # 3. 分析数据质量
            logger.info("\n🔍 数据质量分析：")
            
            # 展示前5条样本
            logger.info("\n📝 样本展示（前5条）：")
            for i, sample in enumerate(samples[:5], 1):
                logger.info(f"\n--- 样本 {i} ---")
                logger.info(f"输入: {sample.get('input', '')[:100]}...")
                logger.info(f"输出: {sample.get('output', '')}")
                logger.info(f"标签: {sample.get('label', 'N/A')}")
                
            # 质量统计
            logger.info("\n📈 质量统计：")
            
            # 检查字段完整性
            complete_samples = 0
            for sample in samples:
                if all(key in sample for key in ['input', 'output']):
                    complete_samples += 1
            
            logger.info(f"字段完整率: {complete_samples/len(samples)*100:.1f}%")
            
            # 检查输入长度
            input_lengths = [len(sample.get('input', '')) for sample in samples]
            avg_input_length = sum(input_lengths) / len(input_lengths)
            logger.info(f"平均输入长度: {avg_input_length:.0f} 字符")
            
            # 检查标签分布（如果是分类任务）
            if task_definition['type'] == 'classification':
                label_counts = {}
                for sample in samples:
                    label = sample.get('label', 'unknown')
                    label_counts[label] = label_counts.get(label, 0) + 1
                
                logger.info("\n标签分布:")
                for label, count in label_counts.items():
                    logger.info(f"  {label}: {count} ({count/len(samples)*100:.1f}%)")
            
            # 保存样本到文件
            output_file = f"data_quality_sample_{task_id[:8]}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "task_info": task_definition,
                    "total_samples": len(samples),
                    "sample_data": samples[:10],  # 保存前10条
                    "quality_stats": {
                        "completeness": f"{complete_samples/len(samples)*100:.1f}%",
                        "avg_input_length": avg_input_length,
                        "label_distribution": label_counts if task_definition['type'] == 'classification' else None
                    }
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"\n💾 数据样本已保存到: {output_file}")
            
        else:
            logger.warning("未找到任务数据")
            
    finally:
        db.close()

async def test_fast_collector_quality():
    """测试FastDataCollector的数据质量"""
    logger.info("\n\n🚀 测试FastDataCollector数据质量...")
    
    collector = FastDataCollector()
    
    # 测试任务
    task_info = {
        "task": "产品使用体验评测",
        "type": "qa",
        "description": "收集关于产品使用体验的问答数据",
        "labels": []
    }
    
    # 收集少量数据
    job_id = f"quality_test_{int(asyncio.get_event_loop().time())}"
    
    try:
        result = await collector.collect_data_fast(
            task_info=task_info,
            target_count=5,
            job_id=job_id,
            enhanced_mode=True  # 使用增强模式提高质量
        )
        
        logger.info(f"\n✅ FastCollector收集了 {len(result)} 条数据")
        
        # 展示数据
        logger.info("\n📝 FastCollector样本展示：")
        for i, item in enumerate(result[:3], 1):
            logger.info(f"\n--- 样本 {i} ---")
            logger.info(f"问题: {item.get('input', '')[:100]}...")
            logger.info(f"答案: {item.get('output', '')[:200]}...")
            
    except Exception as e:
        logger.error(f"FastCollector测试失败: {e}")

async def main():
    """主函数"""
    logger.info("🔍 Data Builder V3 数据质量检查")
    logger.info("="*60)
    
    # 测试Data Builder V3
    await collect_and_analyze_data()
    
    # 测试FastDataCollector
    await test_fast_collector_quality()
    
    logger.info("\n✅ 数据质量检查完成！")

if __name__ == "__main__":
    asyncio.run(main()) 