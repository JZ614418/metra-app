"""
StorageWriter - 批量存储写入器
支持批量upsert、高级去重和数据持久化到Supabase
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict

from supabase import create_client, Client
from app.core.config import settings
from app.services.data_builder_v3.config import config
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

class StorageWriter:
    """批量存储写入器"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        
        # 去重缓存
        self.content_hashes: Set[str] = set()
        self.semantic_hashes: Set[str] = set()
        self.url_hashes: Set[str] = set()
        
        # 统计信息
        self.total_processed = 0
        self.total_inserted = 0
        self.total_updated = 0
        self.total_duplicated = 0
        self.total_failed = 0
        self.start_time = time.time()
        
        # 去重缓存将在首次使用时初始化
        self._dedup_cache_initialized = False
    
    async def _initialize_dedup_cache(self):
        """初始化去重缓存"""
        try:
            logger.info("🔄 初始化去重缓存...")
            
            # 从数据库加载现有数据的hash
            response = self.supabase.table("training_samples").select("content_hash, semantic_hash, source_url").execute()
            
            for item in response.data:
                if item.get('content_hash'):
                    self.content_hashes.add(item['content_hash'])
                if item.get('semantic_hash'):
                    self.semantic_hashes.add(item['semantic_hash'])
                if item.get('source_url'):
                    self.url_hashes.add(self._hash_url(item['source_url']))
            
            logger.info(f"✅ 去重缓存初始化完成: {len(self.content_hashes)}个内容hash")
            
        except Exception as e:
            logger.error(f"❌ 去重缓存初始化失败: {str(e)}")
    
    async def store_validated_samples(
        self, 
        validated_samples: List[ValidatedSample],
        task_id: str,
        batch_size: Optional[int] = None
    ) -> StorageResult:
        """
        批量存储验证后的样本
        
        Args:
            validated_samples: 验证后的样本列表
            task_id: 任务ID
            batch_size: 批处理大小
            
        Returns:
            StorageResult: 存储结果
        """
        logger.info(f"💾 开始存储样本: {len(validated_samples)}个")
        
        start_time = time.time()
        batch_size = batch_size or config.performance.max_storage_batch_size
        
        # 过滤有效样本
        valid_samples = [vs for vs in validated_samples if vs.is_valid]
        logger.info(f"📊 有效样本: {len(valid_samples)}/{len(validated_samples)}")
        
        # 高级去重
        deduplicated_samples = await self._advanced_deduplication(valid_samples)
        logger.info(f"🔄 去重后样本: {len(deduplicated_samples)}")
        
        # 分批存储
        inserted_count = 0
        updated_count = 0
        failed_count = 0
        duplicated_count = len(valid_samples) - len(deduplicated_samples)
        
        for i in range(0, len(deduplicated_samples), batch_size):
            batch_samples = deduplicated_samples[i:i + batch_size]
            
            try:
                batch_result = await self._store_batch(batch_samples, task_id)
                inserted_count += batch_result['inserted']
                updated_count += batch_result['updated']
                failed_count += batch_result['failed']
                
                # 更新统计
                self.total_processed += len(batch_samples)
                self.total_inserted += batch_result['inserted']
                self.total_updated += batch_result['updated']
                self.total_failed += batch_result['failed']
                
            except Exception as e:
                logger.error(f"❌ 批次存储失败: {str(e)}")
                failed_count += len(batch_samples)
                self.total_failed += len(batch_samples)
            
            # 简单的速率控制
            await asyncio.sleep(0.1)
        
        # 更新去重统计
        self.total_duplicated += duplicated_count
        
        storage_time = time.time() - start_time
        
        result = StorageResult(
            total_samples=len(validated_samples),
            inserted_samples=inserted_count,
            updated_samples=updated_count,
            duplicated_samples=duplicated_count,
            failed_samples=failed_count,
            storage_time=storage_time
        )
        
        logger.info(f"✅ 存储完成: {result.to_dict()}")
        return result
    
    async def _advanced_deduplication(
        self, 
        validated_samples: List[ValidatedSample]
    ) -> List[ValidatedSample]:
        """高级去重处理"""
        # 确保去重缓存已初始化
        if not self._dedup_cache_initialized:
            await self._initialize_dedup_cache()
            self._dedup_cache_initialized = True
        
        unique_samples = []
        
        for sample in validated_samples:
            # 计算多种hash
            content_hash = self._hash_content(sample.sample.input_text, sample.sample.output_text)
            semantic_hash = self._hash_semantic(sample.sample.input_text, sample.sample.output_text)
            url_hash = self._hash_url(sample.sample.source_url)
            
            # 多层去重检查
            is_duplicate = False
            
            # 1. 内容完全相同
            if content_hash in self.content_hashes:
                is_duplicate = True
            
            # 2. 语义相似度过高
            elif semantic_hash in self.semantic_hashes:
                is_duplicate = True
            
            # 3. 相同URL的相似内容
            elif url_hash in self.url_hashes:
                # 检查是否为同一URL的相似内容
                if self._is_similar_from_same_url(sample, url_hash):
                    is_duplicate = True
            
            if not is_duplicate:
                unique_samples.append(sample)
                
                # 更新缓存
                self.content_hashes.add(content_hash)
                self.semantic_hashes.add(semantic_hash)
                self.url_hashes.add(url_hash)
        
        return unique_samples
    
    def _hash_content(self, input_text: str, output_text: str) -> str:
        """计算内容hash"""
        combined_text = f"{input_text.strip()}{output_text.strip()}"
        return hashlib.md5(combined_text.encode('utf-8')).hexdigest()
    
    def _hash_semantic(self, input_text: str, output_text: str) -> str:
        """计算语义hash（简化版）"""
        # 提取关键词并排序
        import re
        
        # 移除标点符号和数字
        text = re.sub(r'[^\w\s]', '', f"{input_text} {output_text}")
        words = text.split()
        
        # 提取长度大于2的词
        keywords = [word for word in words if len(word) > 2]
        
        # 排序并取前10个词
        sorted_keywords = sorted(set(keywords))[:10]
        
        keyword_string = ''.join(sorted_keywords)
        return hashlib.md5(keyword_string.encode('utf-8')).hexdigest()
    
    def _hash_url(self, url: str) -> str:
        """计算URL hash"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _is_similar_from_same_url(self, sample: ValidatedSample, url_hash: str) -> bool:
        """检查是否为同一URL的相似内容"""
        # 这里可以实现更复杂的相似度检查
        # 目前简化处理，返回False表示不重复
        return False
    
    async def _store_batch(
        self, 
        samples: List[ValidatedSample], 
        task_id: str
    ) -> Dict[str, int]:
        """存储单个批次"""
        inserted = 0
        updated = 0
        failed = 0
        
        try:
            # 准备批量数据
            batch_data = []
            
            for sample in samples:
                data_row = {
                    'task_id': task_id,
                    'input_text': sample.sample.input_text,
                    'output_text': sample.sample.output_text,
                    'source_url': sample.sample.source_url,
                    'source_domain': sample.sample.source_domain,
                    'content_hash': self._hash_content(sample.sample.input_text, sample.sample.output_text),
                    'semantic_hash': self._hash_semantic(sample.sample.input_text, sample.sample.output_text),
                    'quality_score': sample.quality_score.overall_score,
                    'quality_details': sample.quality_score.to_dict(),
                    'extraction_confidence': sample.sample.extraction_confidence,
                    'validation_time': sample.validation_time,
                    'metadata': {
                        **sample.sample.metadata,
                        'storage_time': time.time()
                    }
                }
                batch_data.append(data_row)
            
            # 执行批量upsert
            response = self.supabase.table("training_samples").upsert(
                batch_data,
                on_conflict="content_hash"
            ).execute()
            
            if response.data:
                inserted = len(response.data)
                logger.debug(f"✅ 批次存储成功: {inserted}条记录")
            
        except Exception as e:
            logger.error(f"❌ 批次存储失败: {str(e)}")
            failed = len(samples)
        
        return {
            'inserted': inserted,
            'updated': updated,
            'failed': failed
        }
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        elapsed_time = time.time() - self.start_time
        
        # 获取数据库统计
        try:
            total_count_response = self.supabase.table("training_samples").select("*", count="exact").execute()
            total_in_db = total_count_response.count
        except Exception as e:
            logger.error(f"获取数据库统计失败: {str(e)}")
            total_in_db = 0
        
        return {
            "total_processed": self.total_processed,
            "total_inserted": self.total_inserted,
            "total_updated": self.total_updated,
            "total_duplicated": self.total_duplicated,
            "total_failed": self.total_failed,
            "total_in_database": total_in_db,
            "dedup_cache_size": len(self.content_hashes),
            "elapsed_time": elapsed_time,
            "samples_per_minute": (self.total_processed / elapsed_time * 60) if elapsed_time > 0 else 0
        }
    
    async def cleanup_old_samples(self, days_old: int = 30) -> int:
        """清理旧样本"""
        try:
            # 计算截止时间
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            cutoff_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cutoff_time))
            
            # 删除旧记录
            response = self.supabase.table("training_samples").delete().lt('created_at', cutoff_timestamp).execute()
            
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"🗑️ 清理旧样本: {deleted_count}条记录")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ 清理旧样本失败: {str(e)}")
            return 0
    
    async def get_sample_quality_distribution(self) -> Dict[str, Any]:
        """获取样本质量分布"""
        try:
            # 获取质量分数分布
            response = self.supabase.table("training_samples").select("quality_score").execute()
            
            if not response.data:
                return {}
            
            scores = [item['quality_score'] for item in response.data if item.get('quality_score')]
            
            if not scores:
                return {}
            
            # 计算分布统计
            distribution = {
                "total_samples": len(scores),
                "average_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
                "score_ranges": {
                    "excellent (0.8-1.0)": len([s for s in scores if s >= 0.8]),
                    "good (0.6-0.8)": len([s for s in scores if 0.6 <= s < 0.8]),
                    "fair (0.4-0.6)": len([s for s in scores if 0.4 <= s < 0.6]),
                    "poor (0.0-0.4)": len([s for s in scores if s < 0.4])
                }
            }
            
            return distribution
            
        except Exception as e:
            logger.error(f"❌ 获取质量分布失败: {str(e)}")
            return {}

# 创建全局实例
storage_writer = StorageWriter()