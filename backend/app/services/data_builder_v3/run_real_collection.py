#!/usr/bin/env python3
"""
真实数据收集任务
使用TogetherAI收集1000个训练样本
"""

import asyncio
import logging
import os
import sys
import time
import json
from typing import Dict, Any

# 设置路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from app.services.data_builder_v3.pipeline import data_builder_pipeline

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_data_collection():
    """运行真实的数据收集任务"""
    logger.info("🚀 开始使用TogetherAI收集1000个数据样本...")
    
    # 定义数据收集任务
    task_definition = {
        "task": "中医药知识问答数据收集",
        "type": "qa",
        "language": "chinese", 
        "description": "收集中医药相关的高质量问答数据，包括病症诊断、药材功效、方剂配伍等内容",
        "domain": "tcm",
        "labels": ["中医", "中药", "药材", "病症", "方剂", "诊断", "治疗", "养生"],
        "data_volume": 1000
    }
    
    logger.info(f"📋 任务定义:")
    logger.info(f"   任务: {task_definition['task']}")
    logger.info(f"   类型: {task_definition['type']}")
    logger.info(f"   领域: {task_definition['domain']}")
    logger.info(f"   目标数量: {task_definition['data_volume']}")
    logger.info(f"   关键词: {task_definition['labels']}")
    
    try:
        # 启动数据收集任务
        task_id = await data_builder_pipeline.start_data_collection(
            task_definition=task_definition,
            target_samples=1000
        )
        
        logger.info(f"✅ 任务已启动，ID: {task_id}")
        
        # 监控任务进度
        start_time = time.time()
        last_status = None
        
        while True:
            # 获取任务进度
            progress = data_builder_pipeline.get_task_progress(task_id)
            
            if not progress:
                logger.error("❌ 无法获取任务进度")
                break
            
            current_status = progress['status']
            
            # 只在状态变化时输出详细信息
            if current_status != last_status:
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 任务状态: {current_status}")
                logger.info(f"🔄 当前步骤: {progress['current_step']} ({progress['current_step_number']}/{progress['total_steps']})")
                logger.info(f"📈 进度: {progress['progress_percentage']:.1f}%")
                logger.info(f"⏱️  已用时间: {progress['elapsed_time']:.1f}秒")
                if progress['estimated_remaining_time'] > 0:
                    logger.info(f"⏳ 预计剩余: {progress['estimated_remaining_time']:.1f}秒")
                
                # 显示样本统计
                if progress['samples_collected'] > 0:
                    logger.info(f"📝 已收集样本: {progress['samples_collected']}")
                if progress['samples_validated'] > 0:
                    logger.info(f"✅ 已验证样本: {progress['samples_validated']}")
                    logger.info(f"🎯 质量通过率: {progress['quality_pass_rate']:.1%}")
                if progress['samples_stored'] > 0:
                    logger.info(f"💾 已存储样本: {progress['samples_stored']}")
                
                last_status = current_status
            else:
                # 状态未变化时，只显示简单进度
                print(f"\r⏳ {current_status} - {progress['progress_percentage']:.1f}% - 已收集:{progress['samples_collected']} 已验证:{progress['samples_validated']} 已存储:{progress['samples_stored']}", end='', flush=True)
            
            # 检查任务是否完成
            if current_status in ['completed', 'failed']:
                print()  # 换行
                break
            
            # 等待一段时间再检查
            await asyncio.sleep(2)
        
        # 最终结果
        final_progress = data_builder_pipeline.get_task_progress(task_id)
        total_time = time.time() - start_time
        
        logger.info(f"\n{'='*60}")
        logger.info("🏁 任务完成!")
        logger.info(f"📊 最终状态: {final_progress['status']}")
        logger.info(f"⏱️  总耗时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
        
        if final_progress['status'] == 'completed':
            logger.info(f"✅ 成功结果:")
            logger.info(f"   📝 收集样本: {final_progress['samples_collected']}")
            logger.info(f"   ✅ 验证样本: {final_progress['samples_validated']}")
            logger.info(f"   💾 存储样本: {final_progress['samples_stored']}")
            logger.info(f"   🎯 质量通过率: {final_progress['quality_pass_rate']:.1%}")
            logger.info(f"   ⚡ 平均速度: {final_progress['samples_stored']/(total_time/60):.1f} 样本/分钟")
            
            # 计算性能指标
            if final_progress['samples_stored'] >= 800:  # 80%目标完成率
                logger.info("🎉 数据收集任务大成功!")
            elif final_progress['samples_stored'] >= 500:  # 50%目标完成率
                logger.info("✅ 数据收集任务基本成功!")
            else:
                logger.warning("⚠️  数据收集任务部分成功，样本数量较少")
        else:
            logger.error(f"❌ 任务失败: {final_progress.get('error_message', '未知错误')}")
        
        # 显示系统统计
        system_stats = data_builder_pipeline.get_system_stats()
        logger.info(f"\n📈 系统统计:")
        logger.info(f"   活跃任务: {system_stats['pipeline_stats']['active_tasks']}")
        logger.info(f"   完成任务: {system_stats['pipeline_stats']['completed_tasks']}")
        
        return final_progress['status'] == 'completed'
        
    except Exception as e:
        logger.error(f"❌ 数据收集任务异常: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """主函数"""
    logger.info("🌟 DataBuilderv3 + TogetherAI 真实数据收集演示")
    logger.info("=" * 60)
    
    success = await run_data_collection()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎊 数据收集任务圆满完成!")
    else:
        logger.error("💥 数据收集任务失败!")
    
    return success

if __name__ == "__main__":
    # 运行数据收集
    success = asyncio.run(main())
    sys.exit(0 if success else 1)