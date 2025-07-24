"""
DataBuilderPipeline - 主编排器
协调所有模块，实现完整的7步质量驱动数据收集流程
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.services.data_builder_v3.config import InternalSpec, config
from app.services.data_builder_v3.spec_mapper import spec_mapper
from app.services.data_builder_v3.query_generator import query_generator
from app.services.data_builder_v3.page_scraper import PageScraper
from app.services.data_builder_v3.sample_extractor import sample_extractor
from app.services.data_builder_v3.quality_validator import quality_validator
from app.services.data_builder_v3.sqlalchemy_storage_writer import sqlalchemy_storage_writer as storage_writer
from app.services.data_builder_v3.monitoring import monitoring

logger = logging.getLogger(__name__)

class PipelineStatus(Enum):
    """流水线状态"""
    INITIALIZING = "initializing"
    MAPPING_SPEC = "mapping_spec"
    GENERATING_QUERIES = "generating_queries"
    SCRAPING_PAGES = "scraping_pages"
    EXTRACTING_SAMPLES = "extracting_samples"
    VALIDATING_QUALITY = "validating_quality"
    STORING_DATA = "storing_data"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PipelineProgress:
    """流水线进度"""
    task_id: str
    status: PipelineStatus
    progress_percentage: float
    current_step: str
    total_steps: int
    current_step_number: int
    samples_collected: int
    samples_validated: int
    samples_stored: int
    quality_pass_rate: float
    elapsed_time: float
    estimated_remaining_time: float
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_number": self.current_step_number,
            "samples_collected": self.samples_collected,
            "samples_validated": self.samples_validated,
            "samples_stored": self.samples_stored,
            "quality_pass_rate": self.quality_pass_rate,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining_time": self.estimated_remaining_time,
            "error_message": self.error_message
        }

class DataBuilderPipeline:
    """数据构建流水线"""
    
    def __init__(self):
        self.active_tasks: Dict[str, PipelineProgress] = {}
        self.completed_tasks: List[Dict[str, Any]] = []
        
        # 流水线步骤定义
        self.pipeline_steps = [
            ("Task Specification Mapping", self._step_map_specification),
            ("Generate Search Queries", self._step_generate_queries),
            ("Scrape Web Content", self._step_scrape_pages),
            ("Extract Training Samples", self._step_extract_samples),
            ("Quality Validation", self._step_validate_quality),
            ("Data Storage", self._step_store_data),
            ("Finalize", self._step_finalize)
        ]
    
    async def start_data_collection(
        self, 
        task_definition: Dict[str, Any],
        target_samples: int = 1000,
        api_task_id: str = None
    ) -> str:
        """
        启动数据收集任务
        
        Args:
            task_definition: 任务定义
            target_samples: 目标样本数量
            api_task_id: API层传递的任务ID
            
        Returns:
            str: 任务ID
        """
        # 使用API传递的task_id，如果没有则生成新的
        task_id = api_task_id if api_task_id else str(uuid.uuid4())
        
        # 初始化进度跟踪
        progress = PipelineProgress(
            task_id=task_id,
            status=PipelineStatus.INITIALIZING,
            progress_percentage=0.0,
            current_step="初始化",
            total_steps=len(self.pipeline_steps),
            current_step_number=0,
            samples_collected=0,
            samples_validated=0,
            samples_stored=0,
            quality_pass_rate=0.0,
            elapsed_time=0.0,
            estimated_remaining_time=0.0
        )
        
        self.active_tasks[task_id] = progress
        
        # 启动异步任务
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._execute_pipeline(task_id, task_definition, target_samples))
        except RuntimeError:
            # 如果没有运行的事件循环，在后台启动
            asyncio.ensure_future(self._execute_pipeline(task_id, task_definition, target_samples))
        
        logger.info(f"🚀 启动数据收集任务: {task_id}")
        return task_id
    
    async def _execute_pipeline(
        self, 
        task_id: str, 
        task_definition: Dict[str, Any], 
        target_samples: int
    ):
        """执行完整的数据收集流水线"""
        progress = self.active_tasks[task_id]
        start_time = time.time()
        
        try:
            # 尝试恢复之前的进度
            context = await self._restore_pipeline_context(task_id)
            if context is None:
                context = {
                    "task_definition": task_definition,
                    "target_samples": target_samples,
                    "spec": None,
                    "queries": None,
                    "pages": None,
                    "samples": None,
                    "validated_samples": None,
                    "storage_result": None,
                    "last_completed_step": 0
                }
            
            # 从上次完成的步骤继续
            start_from_step = context.get("last_completed_step", 0) + 1
            
            # 执行流水线步骤
            for step_number, (step_name, step_func) in enumerate(self.pipeline_steps[start_from_step-1:], start_from_step):
                progress.current_step = step_name
                progress.current_step_number = step_number
                progress.progress_percentage = (step_number - 1) / len(self.pipeline_steps) * 100
                progress.elapsed_time = time.time() - start_time
                
                # 估算剩余时间
                if step_number > 1:
                    avg_time_per_step = progress.elapsed_time / (step_number - start_from_step + 1)
                    remaining_steps = len(self.pipeline_steps) - step_number + 1
                    progress.estimated_remaining_time = avg_time_per_step * remaining_steps
                
                logger.info(f"📋 执行步骤 {step_number}/{len(self.pipeline_steps)}: {step_name}")
                
                # 执行步骤
                await step_func(context, progress)
                
                # 保存进度到数据库
                context["last_completed_step"] = step_number
                await self._save_pipeline_context(task_id, context, progress)
                
                # 更新进度
                progress.progress_percentage = step_number / len(self.pipeline_steps) * 100
            
            # 完成任务
            progress.status = PipelineStatus.COMPLETED
            progress.elapsed_time = time.time() - start_time
            progress.estimated_remaining_time = 0.0
            
            # 移动到完成列表
            self.completed_tasks.append({
                **progress.to_dict(),
                "completion_time": time.time(),
                "final_stats": context.get("storage_result", {})
            })
            
            logger.info(f"✅ 任务完成: {task_id} ({progress.elapsed_time:.1f}秒)")
            
        except Exception as e:
            progress.status = PipelineStatus.FAILED
            progress.error_message = str(e)
            progress.elapsed_time = time.time() - start_time
            
            # 保存失败状态，以便后续恢复
            await self._save_pipeline_context(task_id, context, progress)
            
            logger.error(f"❌ 任务失败: {task_id} - {str(e)}")
        
        finally:
            # 清理活动任务
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def _save_pipeline_context(self, task_id: str, context: Dict[str, Any], progress: PipelineProgress):
        """保存流水线上下文到数据库"""
        try:
            # 准备要保存的数据
            checkpoint_data = {
                "task_id": task_id,
                "context": {
                    "task_definition": context.get("task_definition"),
                    "target_samples": context.get("target_samples"),
                    "last_completed_step": context.get("last_completed_step", 0),
                    "spec": context.get("spec"),
                    "queries": context.get("queries"),
                    # 只保存关键信息，避免数据过大
                    "pages_count": len(context.get("pages", [])) if context.get("pages") else 0,
                    "samples_count": len(context.get("samples", [])) if context.get("samples") else 0,
                    "validated_samples_count": len(context.get("validated_samples", [])) if context.get("validated_samples") else 0,
                },
                "progress": progress.to_dict(),
                "saved_at": time.time()
            }
            
            # 保存到storage_writer（利用现有的存储机制）
            await storage_writer.save_task_checkpoint(task_id, checkpoint_data)
            logger.info(f"💾 已保存任务进度: {task_id} (步骤 {context.get('last_completed_step', 0)})")
            
        except Exception as e:
            logger.warning(f"保存进度失败，但继续执行: {str(e)}")
    
    async def _restore_pipeline_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """从数据库恢复流水线上下文"""
        try:
            # 尝试从storage_writer恢复
            checkpoint_data = await storage_writer.load_task_checkpoint(task_id)
            
            if checkpoint_data and "context" in checkpoint_data:
                logger.info(f"🔄 恢复任务进度: {task_id} (从步骤 {checkpoint_data['context'].get('last_completed_step', 0)} 继续)")
                return checkpoint_data["context"]
            
            return None
            
        except Exception as e:
            logger.warning(f"恢复进度失败，将从头开始: {str(e)}")
            return None
    
    async def resume_task(self, task_id: str) -> bool:
        """恢复一个失败或中断的任务"""
        try:
            # 检查是否有保存的上下文
            context = await self._restore_pipeline_context(task_id)
            if not context:
                logger.error(f"找不到任务 {task_id} 的保存进度")
                return False
            
            # 重新启动任务
            await self.start_data_collection(
                task_definition=context.get("task_definition"),
                target_samples=context.get("target_samples"),
                api_task_id=task_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"恢复任务失败: {str(e)}")
            return False
    
    async def _step_map_specification(self, context: Dict[str, Any], progress: PipelineProgress):
        """步骤1: 任务规范映射"""
        progress.status = PipelineStatus.MAPPING_SPEC
        
        spec = await spec_mapper.map_task_to_spec(context["task_definition"])
        context["spec"] = spec
        
        logger.info(f"✅ 规范映射完成: {spec.domain}/{spec.task_type}")
    
    async def _step_generate_queries(self, context: Dict[str, Any], progress: PipelineProgress):
        """步骤2: 生成搜索查询"""
        progress.status = PipelineStatus.GENERATING_QUERIES
        
        queries = await query_generator.generate_search_queries(
            context["spec"], 
            target_count=50
        )
        context["queries"] = queries
        
        logger.info(f"✅ 查询生成完成: {len(queries)}个查询")
    
    async def _step_scrape_pages(self, context: Dict[str, Any], progress: PipelineProgress):
        """步骤3: 抓取网页内容"""
        progress.status = PipelineStatus.SCRAPING_PAGES
        
        async with PageScraper() as scraper:
            pages = await scraper.scrape_search_results(context["queries"])
        
        context["pages"] = pages
        
        logger.info(f"✅ 页面抓取完成: {len(pages)}个页面")
    
    async def _step_extract_samples(self, context: Dict[str, Any], progress: PipelineProgress):
        """步骤4: 提取训练样本"""
        progress.status = PipelineStatus.EXTRACTING_SAMPLES
        
        samples = await sample_extractor.extract_samples_from_pages(
            context["pages"],
            context["spec"],
            context["target_samples"]
        )
        
        context["samples"] = samples
        progress.samples_collected = len(samples)
        
        logger.info(f"✅ 样本提取完成: {len(samples)}个样本")
    
    async def _step_validate_quality(self, context: Dict[str, Any], progress: PipelineProgress):
        """步骤5: 质量验证评估"""
        progress.status = PipelineStatus.VALIDATING_QUALITY
        
        validated_samples = await quality_validator.validate_samples(
            context["samples"],
            context["spec"]
        )
        
        context["validated_samples"] = validated_samples
        
        # 计算质量通过率
        valid_count = sum(1 for vs in validated_samples if vs.is_valid)
        progress.samples_validated = len(validated_samples)
        progress.quality_pass_rate = valid_count / len(validated_samples) if validated_samples else 0
        
        logger.info(f"✅ 质量验证完成: {valid_count}/{len(validated_samples)} 通过")
    
    async def _step_store_data(self, context: Dict[str, Any], progress: PipelineProgress):
        """步骤6: 数据存储写入"""
        progress.status = PipelineStatus.STORING_DATA
        
        storage_result = await storage_writer.store_validated_samples(
            context["validated_samples"],
            progress.task_id
        )
        
        context["storage_result"] = storage_result
        progress.samples_stored = storage_result.inserted_samples
        
        logger.info(f"✅ 数据存储完成: {storage_result.inserted_samples}个样本")
    
    async def _step_finalize(self, context: Dict[str, Any], progress: PipelineProgress):
        """步骤7: 完成处理"""
        # 发送完成通知
        await self._send_completion_notification(context, progress)
        
        # 更新监控指标
        await self._update_monitoring_metrics(context, progress)
        
        logger.info("✅ 流水线执行完成")
    
    async def _send_completion_notification(self, context: Dict[str, Any], progress: PipelineProgress):
        """发送完成通知"""
        try:
            # 构建完成报告
            storage_result = context.get("storage_result")
            if storage_result:
                message = f"""🎉 数据收集任务完成！

任务ID: {progress.task_id}
处理时间: {progress.elapsed_time:.1f}秒
样本收集: {progress.samples_collected}
质量通过率: {progress.quality_pass_rate:.1%}
成功存储: {storage_result.inserted_samples}
去重过滤: {storage_result.duplicated_samples}"""
                
                # 这里可以发送到Slack或其他通知系统
                logger.info(message)
                
        except Exception as e:
            logger.error(f"发送完成通知失败: {str(e)}")
    
    async def _update_monitoring_metrics(self, context: Dict[str, Any], progress: PipelineProgress):
        """更新监控指标"""
        try:
            # 这里可以更新监控系统的指标
            # 例如：总样本数、质量分数、处理时间等
            pass
        except Exception as e:
            logger.error(f"更新监控指标失败: {str(e)}")
    
    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].to_dict()
        
        # 检查已完成任务
        for completed_task in self.completed_tasks:
            if completed_task["task_id"] == task_id:
                return completed_task
        
        return None
    
    def get_all_tasks(self) -> Dict[str, Any]:
        """获取所有任务状态"""
        active_tasks = {
            task_id: progress.to_dict() 
            for task_id, progress in self.active_tasks.items()
        }
        
        return {
            "active_tasks": active_tasks,
            "completed_tasks": self.completed_tasks[-10:],  # 最近10个完成任务
            "total_active": len(self.active_tasks),
            "total_completed": len(self.completed_tasks)
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            "pipeline_stats": {
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "total_steps": len(self.pipeline_steps)
            },
            "component_stats": {
                "query_generator": query_generator.get_rate_limit_status(),
                "sample_extractor": sample_extractor.get_extraction_stats(),
                "quality_validator": quality_validator.get_validation_stats(),
                "storage_writer": "stats_available_via_async_call"
            },
            "monitoring_status": monitoring.get_current_status()
        }
    
    async def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        if task_id in self.active_tasks:
            progress = self.active_tasks[task_id]
            progress.status = PipelineStatus.FAILED
            progress.error_message = "任务被用户停止"
            
            # 移动到完成列表
            self.completed_tasks.append({
                **progress.to_dict(),
                "completion_time": time.time(),
                "stopped_by_user": True
            })
            
            del self.active_tasks[task_id]
            
            logger.info(f"⏹️ 任务已停止: {task_id}")
            return True
        
        return False
    
    async def cleanup_old_tasks(self, max_completed_tasks: int = 100):
        """清理旧任务"""
        if len(self.completed_tasks) > max_completed_tasks:
            self.completed_tasks = self.completed_tasks[-max_completed_tasks:]
            logger.info(f"🧹 清理旧任务，保留最新 {max_completed_tasks} 个")

# 创建全局实例
data_builder_pipeline = DataBuilderPipeline()