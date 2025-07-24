"""
Mock Data Collector - 用于测试的模拟数据收集器
不依赖外部API，生成模拟数据用于测试
"""
import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MockDataCollector:
    """模拟数据收集器 - 用于测试"""
    
    def __init__(self):
        self.jobs = {}
        
    async def collect_data_fast(self, 
                               task_info: Dict[str, Any], 
                               target_count: int,
                               job_id: str,
                               progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        模拟高速数据收集 - 测试版本
        """
        
        logger.info(f"🧪 启动模拟数据收集 job {job_id}")
        logger.info(f"目标: {target_count} 条数据")
        
        start_time = time.time()
        all_collected_data = []
        
        try:
            # 更新任务状态
            self.jobs[job_id] = {
                "status": "running",
                "progress": 0,
                "total": target_count,
                "collected": 0,
                "start_time": start_time
            }
            
            # 模拟数据收集过程
            task_type = task_info.get('type', 'classification')
            labels = task_info.get('labels', ['正面', '负面'])
            
            # 生成模拟数据
            for i in range(target_count):
                # 模拟处理时间（每个样本0.1-0.5秒）
                await asyncio.sleep(0.1 + (i % 5) * 0.1)
                
                if task_type == 'classification':
                    sample = {
                        "text": f"这是第{i+1}条测试文本数据，用于验证DataBuilder V2的功能。内容包括情感表达和分类测试。",
                        "label": labels[i % len(labels)],
                        "confidence": 0.8 + (i % 3) * 0.05,  # 0.8-0.9之间
                        "source": f"https://test-source-{i+1}.example.com",
                        "source_type": "mock",
                        "meta_data": {
                            "sample_id": i+1,
                            "generated_at": datetime.now().isoformat(),
                            "test_mode": True
                        }
                    }
                else:
                    sample = {
                        "input": f"测试输入{i+1}：请分析这段文本的主要内容",
                        "output": f"测试输出{i+1}：这段文本主要讨论了测试数据的生成和验证过程。",
                        "confidence": 0.85 + (i % 2) * 0.05,
                        "source": f"https://test-source-{i+1}.example.com",
                        "source_type": "mock",
                        "meta_data": {
                            "sample_id": i+1,
                            "generated_at": datetime.now().isoformat(),
                            "test_mode": True
                        }
                    }
                
                all_collected_data.append(sample)
                
                # 更新进度
                progress = int((i + 1) / target_count * 100)
                self.jobs[job_id]["collected"] = len(all_collected_data)
                self.jobs[job_id]["progress"] = progress
                
                if progress_callback:
                    await progress_callback({
                        "status": "collecting",
                        "message": f"模拟收集中... 已完成 {i+1}/{target_count}",
                        "collected": len(all_collected_data),
                        "total": target_count,
                        "progress": progress
                    })
                
                logger.info(f"🧪 生成样本 {i+1}/{target_count}")
            
            # 完成
            end_time = time.time()
            duration = end_time - start_time
            
            self.jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "collected": len(all_collected_data),
                "end_time": end_time,
                "duration": duration
            })
            
            logger.info(f"🎉 模拟收集完成!")
            logger.info(f"   样本数: {len(all_collected_data)}")
            logger.info(f"   耗时: {duration:.1f}秒")
            logger.info(f"   速度: {len(all_collected_data)/duration:.1f} 样本/秒")
            
            if progress_callback:
                await progress_callback({
                    "status": "completed",
                    "message": f"模拟收集完成! {len(all_collected_data)} 条数据，耗时 {duration:.1f}秒",
                    "collected": len(all_collected_data),
                    "total": target_count,
                    "progress": 100
                })
            
            return all_collected_data
            
        except Exception as e:
            logger.error(f"模拟收集失败: {e}")
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)
            
            if progress_callback:
                await progress_callback({
                    "status": "failed",
                    "message": f"模拟收集失败: {str(e)}",
                    "collected": len(all_collected_data),
                    "total": target_count
                })
            
            raise
    
    def get_job_status(self, job_id: str) -> Dict:
        """获取任务状态"""
        return self.jobs.get(job_id, {"status": "not_found"})

# 创建全局实例
mock_collector = MockDataCollector()