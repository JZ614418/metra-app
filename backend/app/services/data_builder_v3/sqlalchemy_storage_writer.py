"""
SQLAlchemy Storage Writer - 替代Supabase的数据库存储器
使用项目的SQLAlchemy数据库来存储DataBuilder V3的收集数据
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import SessionLocal
from app.models.data_collection_task import DataCollectionTask, CollectedDataSample
from app.services.data_builder_v3.quality_validator import ValidatedSample

logger = logging.getLogger(__name__)

@dataclass
class StorageResult:
    """存储结果"""
    total_samples: int
    inserted_samples: int
    updated_samples: int
    duplicated_samples: int
    failed_samples: int
    storage_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

class SQLAlchemyStorageWriter:
    """SQLAlchemy批量存储写入器"""
    
    def __init__(self):
        # 去重缓存
        self.content_hashes: Set[str] = set()
        self.semantic_hashes: Set[str] = set()
        self.url_hashes: Set[str] = set()
        
        # 统计信息
        self.total_processed = 0
        self.total_inserted = 0
        self.total_duplicated = 0
        self.total_failed = 0
        
    def _generate_content_hash(self, text: str) -> str:
        """生成内容哈希"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _generate_semantic_hash(self, text: str) -> str:
        """生成语义哈希（简化版）"""
        # 简化版：移除标点符号和空格后生成哈希
        clean_text = ''.join(char.lower() for char in text if char.isalnum())
        return hashlib.md5(clean_text.encode('utf-8')).hexdigest()
    
    async def store_validated_samples(
        self,
        samples: List[ValidatedSample],
        task_id: str,
        batch_size: int = 100
    ) -> StorageResult:
        """
        批量存储验证过的样本到数据库
        
        Args:
            samples: 验证过的样本列表
            task_id: 任务ID 
            batch_size: 批量处理大小
            
        Returns:
            StorageResult: 存储结果统计
        """
        start_time = time.time()
        
        db = SessionLocal()
        try:
            # 获取任务记录
            db_task = db.query(DataCollectionTask).filter(
                DataCollectionTask.job_id == task_id
            ).first()
            
            if not db_task:
                logger.error(f"Task not found: {task_id}")
                return StorageResult(
                    total_samples=len(samples),
                    inserted_samples=0,
                    updated_samples=0,
                    duplicated_samples=0,
                    failed_samples=len(samples),
                    storage_time=time.time() - start_time
                )
            
            inserted_count = 0
            duplicated_count = 0
            failed_count = 0
            
            # 批量处理样本
            for i in range(0, len(samples), batch_size):
                batch = samples[i:i + batch_size]
                
                for validated_sample in batch:
                    try:
                        # ValidatedSample包含ExtractedSample
                        sample = validated_sample.sample
                        
                        # 生成内容哈希进行去重
                        content_hash = self._generate_content_hash(sample.text)
                        
                        # 检查是否已存在
                        existing = db.query(CollectedDataSample).filter(
                            CollectedDataSample.task_id == db_task.id,
                            CollectedDataSample.text == sample.text
                        ).first()
                        
                        if existing:
                            duplicated_count += 1
                            continue
                        
                        # 创建新样本记录
                        db_sample = CollectedDataSample(
                            task_id=db_task.id,
                            text=sample.text,
                            label=getattr(sample, 'label', None),
                            input_text=getattr(sample, 'input_text', None),
                            output_text=getattr(sample, 'output_text', None),
                            confidence=getattr(sample, 'confidence', 0.0),
                            source=getattr(sample, 'source', ''),
                            source_type='web_scraping',
                            meta_data=json.dumps({
                                'quality_score': validated_sample.quality_score.overall_score,
                                'quality_dimensions': validated_sample.quality_score.to_dict(),
                                'processing_time': validated_sample.validation_time,
                                'content_hash': content_hash
                            })
                        )
                        
                        db.add(db_sample)
                        inserted_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to store sample: {e}")
                        failed_count += 1
                
                # 批量提交
                try:
                    db.commit()
                    logger.info(f"Stored batch of {len(batch)} samples")
                except Exception as e:
                    logger.error(f"Failed to commit batch: {e}")
                    db.rollback()
                    failed_count += len(batch)
            
            # 更新统计信息
            self.total_processed += len(samples)
            self.total_inserted += inserted_count
            self.total_duplicated += duplicated_count
            self.total_failed += failed_count
            
            # 更新任务的收集计数
            db_task.collected_count = inserted_count
            db.commit()
            
            storage_time = time.time() - start_time
            
            logger.info(f"Storage completed: {inserted_count} inserted, {duplicated_count} duplicated, {failed_count} failed in {storage_time:.2f}s")
            
            return StorageResult(
                total_samples=len(samples),
                inserted_samples=inserted_count,
                updated_samples=0,
                duplicated_samples=duplicated_count,
                failed_samples=failed_count,
                storage_time=storage_time
            )
            
        finally:
            db.close()
        
        logger.info(f"✅ 存储完成，统计信息: {result}")
        return result
    
    async def save_task_checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]) -> bool:
        """保存任务检查点"""
        try:
            # 使用现有的数据库连接
            db = SessionLocal()
            
            # 查找任务
            from app.models.data_collection_task import DataCollectionTask
            task = db.query(DataCollectionTask).filter(
                DataCollectionTask.job_id == task_id
            ).first()
            
            if task:
                # 保存检查点数据到task_info字段
                if not task.task_info:
                    task.task_info = {}
                
                task.task_info["checkpoint"] = checkpoint_data
                task.updated_at = datetime.utcnow()
                
                db.commit()
                return True
            else:
                logger.warning(f"找不到任务 {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"保存检查点失败: {str(e)}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    async def load_task_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载任务检查点"""
        try:
            db = SessionLocal()
            
            # 查找任务
            from app.models.data_collection_task import DataCollectionTask
            task = db.query(DataCollectionTask).filter(
                DataCollectionTask.job_id == task_id
            ).first()
            
            if task and task.task_info and "checkpoint" in task.task_info:
                return task.task_info["checkpoint"]
            
            return None
            
        except Exception as e:
            logger.error(f"加载检查点失败: {str(e)}")
            return None
        finally:
            if db:
                db.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_processed": self.total_processed,
            "total_inserted": self.total_inserted,
            "total_duplicated": self.total_duplicated,
            "total_failed": self.total_failed,
            "cache_sizes": {
                "content_hashes": len(self.content_hashes),
                "semantic_hashes": len(self.semantic_hashes),
                "url_hashes": len(self.url_hashes)
            }
        }
    
    def clear_caches(self):
        """清理缓存"""
        self.content_hashes.clear()
        self.semantic_hashes.clear()
        self.url_hashes.clear()
        logger.info("Storage caches cleared")

# 创建全局实例
sqlalchemy_storage_writer = SQLAlchemyStorageWriter()