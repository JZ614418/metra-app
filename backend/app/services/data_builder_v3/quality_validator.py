"""
QualityValidator - 多维度质量验证器
基于6个维度对样本进行质量评估，使用sentence-transformers计算语义相似度
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

from app.services.data_builder_v3.config import InternalSpec, config
from app.services.data_builder_v3.sample_extractor import ExtractedSample

logger = logging.getLogger(__name__)

@dataclass
class QualityScore:
    """质量评分结果"""
    overall_score: float
    content_quality: float
    language_quality: float
    label_quality: float
    confidence_score: float
    source_reliability: float
    metadata_completeness: float
    reasons: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "overall_score": self.overall_score,
            "dimensions": {
                "content_quality": self.content_quality,
                "language_quality": self.language_quality,
                "label_quality": self.label_quality,
                "confidence_score": self.confidence_score,
                "source_reliability": self.source_reliability,
                "metadata_completeness": self.metadata_completeness
            },
            "reasons": self.reasons
        }

@dataclass
class ValidatedSample:
    """验证后的样本"""
    sample: ExtractedSample
    quality_score: QualityScore
    is_valid: bool
    validation_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "sample": self.sample.to_dict(),
            "quality_score": self.quality_score.to_dict(),
            "is_valid": self.is_valid,
            "validation_time": self.validation_time
        }

class QualityValidator:
    """多维度质量验证器"""
    
    def __init__(self):
        self.sentence_model = None
        self.model_loading = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 统计信息
        self.validation_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.start_time = time.time()
        
        # 质量阈值
        self.thresholds = config.quality
    
    async def _load_sentence_model(self):
        """异步加载sentence-transformers模型"""
        if self.sentence_model is not None:
            return
        
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not available, skipping model loading")
            return
        
        if self.model_loading:
            # 如果正在加载，等待完成
            while self.model_loading:
                await asyncio.sleep(0.1)
            return
        
        self.model_loading = True
        try:
            logger.info("📥 Loading sentence-transformers model...")
            
            # 在线程池中加载模型以避免阻塞事件循环
            loop = asyncio.get_event_loop()
            self.sentence_model = await loop.run_in_executor(
                self.executor,
                lambda: SentenceTransformer('all-MiniLM-L6-v2')
            )
            
            logger.info("✅ sentence-transformers model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {str(e)}")
            self.sentence_model = None
        finally:
            self.model_loading = False
    
    async def validate_samples(
        self, 
        samples: List[ExtractedSample], 
        spec: InternalSpec
    ) -> List[ValidatedSample]:
        """
        批量验证样本质量
        
        Args:
            samples: 待验证样本列表
            spec: 任务规范
            
        Returns:
            List[ValidatedSample]: 验证后的样本列表
        """
        logger.info(f"🔍 开始质量验证: {len(samples)}个样本")
        
        # 确保模型已加载
        await self._load_sentence_model()
        
        validated_samples = []
        
        # 分批处理以控制内存使用
        batch_size = 100
        for i in range(0, len(samples), batch_size):
            batch_samples = samples[i:i + batch_size]
            
            # 并发验证当前批次
            tasks = [
                self._validate_single_sample(sample, spec)
                for sample in batch_samples
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for result in batch_results:
                if isinstance(result, ValidatedSample):
                    validated_samples.append(result)
                    if result.is_valid:
                        self.passed_count += 1
                    else:
                        self.failed_count += 1
                elif isinstance(result, Exception):
                    logger.error(f"样本验证失败: {str(result)}")
                    self.failed_count += 1
                
                self.validation_count += 1
        
        # 按质量分数排序
        validated_samples.sort(key=lambda x: x.quality_score.overall_score, reverse=True)
        
        pass_rate = self.passed_count / self.validation_count if self.validation_count > 0 else 0
        logger.info(f"✅ 质量验证完成: {len(validated_samples)}个样本, 通过率: {pass_rate:.1%}")
        
        return validated_samples
    
    async def _validate_single_sample(
        self, 
        sample: ExtractedSample, 
        spec: InternalSpec
    ) -> ValidatedSample:
        """验证单个样本"""
        start_time = time.time()
        
        try:
            # 计算各维度质量分数
            quality_score = await self._calculate_quality_score(sample, spec)
            
            # 判断是否通过验证
            is_valid = self._is_sample_valid(quality_score, spec)
            
            validation_time = time.time() - start_time
            
            return ValidatedSample(
                sample=sample,
                quality_score=quality_score,
                is_valid=is_valid,
                validation_time=validation_time
            )
            
        except Exception as e:
            logger.error(f"样本验证失败: {str(e)}")
            # 返回低分数的验证结果
            quality_score = QualityScore(
                overall_score=0.0,
                content_quality=0.0,
                language_quality=0.0,
                label_quality=0.0,
                confidence_score=0.0,
                source_reliability=0.0,
                metadata_completeness=0.0,
                reasons=[f"验证错误: {str(e)}"]
            )
            
            return ValidatedSample(
                sample=sample,
                quality_score=quality_score,
                is_valid=False,
                validation_time=time.time() - start_time
            )
    
    async def _calculate_quality_score(
        self, 
        sample: ExtractedSample, 
        spec: InternalSpec
    ) -> QualityScore:
        """计算质量分数"""
        reasons = []
        
        # 1. 内容质量 (25%)
        content_quality = self._evaluate_content_quality(sample, spec, reasons)
        
        # 2. 语言质量 (20%)
        language_quality = await self._evaluate_language_quality(sample, spec, reasons)
        
        # 3. 标签质量 (20%)
        label_quality = self._evaluate_label_quality(sample, spec, reasons)
        
        # 4. 置信度分数 (15%)
        confidence_score = sample.extraction_confidence
        
        # 5. 来源可靠性 (10%)
        source_reliability = self._evaluate_source_reliability(sample, reasons)
        
        # 6. 元数据完整性 (10%)
        metadata_completeness = self._evaluate_metadata_completeness(sample, reasons)
        
        # 计算总分
        overall_score = (
            content_quality * 0.25 +
            language_quality * 0.20 +
            label_quality * 0.20 +
            confidence_score * 0.15 +
            source_reliability * 0.10 +
            metadata_completeness * 0.10
        )
        
        return QualityScore(
            overall_score=overall_score,
            content_quality=content_quality,
            language_quality=language_quality,
            label_quality=label_quality,
            confidence_score=confidence_score,
            source_reliability=source_reliability,
            metadata_completeness=metadata_completeness,
            reasons=reasons
        )
    
    def _evaluate_content_quality(
        self, 
        sample: ExtractedSample, 
        spec: InternalSpec, 
        reasons: List[str]
    ) -> float:
        """评估内容质量"""
        score = 0.0
        
        # 检查内容长度
        min_length = spec.quality_rules.get('min_content_length', 60)
        if len(sample.input_text) >= min_length:
            score += 0.3
        else:
            reasons.append(f"输入内容过短: {len(sample.input_text)} < {min_length}")
        
        # 检查输出长度
        min_answer_length = spec.quality_rules.get('min_answer_length', 100)
        if len(sample.output_text) >= min_answer_length:
            score += 0.3
        else:
            reasons.append(f"输出内容过短: {len(sample.output_text)} < {min_answer_length}")
        
        # 检查必需关键词
        required_keywords = spec.quality_rules.get('required_keywords', [])
        if required_keywords:
            matched_keywords = sum(
                1 for keyword in required_keywords 
                if keyword in sample.input_text or keyword in sample.output_text
            )
            keyword_score = matched_keywords / len(required_keywords)
            score += keyword_score * 0.2
            
            if keyword_score < 0.5:
                reasons.append(f"关键词匹配不足: {matched_keywords}/{len(required_keywords)}")
        else:
            score += 0.2
        
        # 检查禁止关键词
        forbidden_keywords = spec.quality_rules.get('forbidden_keywords', [])
        forbidden_found = any(
            keyword in sample.input_text or keyword in sample.output_text
            for keyword in forbidden_keywords
        )
        
        if not forbidden_found:
            score += 0.2
        else:
            reasons.append("包含禁止关键词")
        
        return min(score, 1.0)
    
    async def _evaluate_language_quality(
        self, 
        sample: ExtractedSample, 
        spec: InternalSpec, 
        reasons: List[str]
    ) -> float:
        """评估语言质量 - 增强版"""
        score = 0.0
        
        # 1. 语法和流畅性评估 (35%)
        grammar_score = self._check_grammar_quality_enhanced(sample.input_text, sample.output_text, reasons)
        score += grammar_score * 0.35
        
        # 2. 语义相似性检查 (25%)
        if spec.task_type == "question_answering" and self.sentence_model:
            try:
                similarity_score = await self._calculate_semantic_similarity(
                    sample.input_text, sample.output_text
                )
                score += similarity_score * 0.25
            except Exception as e:
                logger.debug(f"语义相似性计算失败: {str(e)}")
                score += 0.2  # 给较低的默认分数
        else:
            score += 0.25
        
        # 3. 内容完整性检查 (25%)
        completeness_score = self._check_content_completeness_enhanced(sample, reasons)
        score += completeness_score * 0.25
        
        # 4. 🔧 新增：任务特定质量检查 (15%)
        task_specific_score = self._check_task_specific_quality(sample, spec, reasons)
        score += task_specific_score * 0.15
        
        if score < self.thresholds.language_quality_threshold:
            reasons.append(f"语言质量不达标: {score:.2f}")
        
        return min(score, 1.0)
    
    def _check_grammar_quality_enhanced(self, input_text: str, output_text: str, reasons: List[str]) -> float:
        """增强的语法质量检查"""
        score = 0.0
        text = input_text + " " + output_text
        
        # 1. 基础结构检查
        if len(text.strip()) > 10:
            score += 0.2
        
        # 2. 句子完整性
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if sentences:
            score += 0.2
            
            # 检查句子长度分布
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 3 <= avg_sentence_length <= 30:  # 合理的句子长度
                score += 0.2
            else:
                reasons.append(f"句子长度异常: 平均{avg_sentence_length:.1f}词")
        
        # 3. 标点符号检查
        punctuation_ratio = sum(1 for char in text if char in '.,!?;:') / max(len(text), 1)
        if 0.02 <= punctuation_ratio <= 0.15:  # 合理的标点符号比例
            score += 0.2
        
        # 4. 🔧 新增：词汇多样性检查
        words = text.lower().split()
        if len(words) > 10:
            unique_words = len(set(words))
            diversity_ratio = unique_words / len(words)
            if diversity_ratio > 0.6:  # 词汇多样性较好
                score += 0.2
            else:
                reasons.append(f"词汇重复度较高: {(1-diversity_ratio)*100:.1f}%")
        
        return min(score, 1.0)
    
    def _check_content_completeness_enhanced(self, sample: ExtractedSample, reasons: List[str]) -> float:
        """增强的内容完整性检查"""
        score = 0.0
        
        # 1. 输入文本质量
        input_text = sample.input_text.strip()
        if len(input_text) >= 20:  # 提高最小长度要求
            score += 0.3
            
            # 检查是否包含有意义的词汇
            words = input_text.split()
            meaningful_words = [w for w in words if len(w) > 2 and w.isalpha()]
            if len(meaningful_words) / max(len(words), 1) > 0.7:
                score += 0.2
        else:
            reasons.append(f"输入文本过短: {len(input_text)}字符")
        
        # 2. 输出文本质量
        output_text = sample.output_text.strip()
        if len(output_text) >= 10:
            score += 0.3
            
            # 检查输入输出的平衡性
            length_ratio = len(output_text) / max(len(input_text), 1)
            if 0.1 <= length_ratio <= 3.0:  # 合理的长度比例
                score += 0.2
            else:
                reasons.append(f"输入输出长度比例异常: {length_ratio:.2f}")
        else:
            reasons.append(f"输出文本过短: {len(output_text)}字符")
        
        return min(score, 1.0)
    
    def _check_task_specific_quality(self, sample: ExtractedSample, spec: InternalSpec, reasons: List[str]) -> float:
        """任务特定的质量检查"""
        score = 0.0
        
        try:
            if spec.task_type == "question_answering":
                # 问答任务质量检查
                input_lower = sample.input_text.lower()
                
                # 检查是否包含问题标志
                question_indicators = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 
                                     '什么', '如何', '为什么', '何时', '哪里', '谁', '哪个']
                has_question_word = any(indicator in input_lower for indicator in question_indicators)
                has_question_mark = input_lower.strip().endswith(('?', '？'))
                
                if has_question_word or has_question_mark:
                    score += 0.5
                else:
                    reasons.append("问答任务但输入不包含问题标志")
                
                # 检查答案的完整性
                if len(sample.output_text.strip()) > 15:
                    score += 0.5
                else:
                    reasons.append("答案过于简短")
                    
            elif spec.task_type == "text_classification":
                # 文本分类任务质量检查
                output_words = sample.output_text.strip().split()
                
                # 分类标签应该相对简短
                if len(output_words) <= 5:
                    score += 0.5
                else:
                    reasons.append("分类标签过长")
                
                # 输入文本应该有足够的内容供分类
                if len(sample.input_text.strip()) > 30:
                    score += 0.5
                else:
                    reasons.append("分类文本内容不足")
                    
            elif spec.task_type == "summarization":
                # 摘要任务质量检查
                input_len = len(sample.input_text.strip())
                output_len = len(sample.output_text.strip())
                
                # 摘要应该比原文短
                if output_len < input_len and output_len > input_len * 0.1:
                    score += 0.5
                else:
                    reasons.append("摘要长度不合理")
                
                # 摘要应该包含关键信息
                if output_len > 20:
                    score += 0.5
                else:
                    reasons.append("摘要过短")
                    
            else:
                # 通用任务质量检查
                if (sample.input_text.strip() and sample.output_text.strip() and 
                    len(sample.input_text.strip()) > 10 and len(sample.output_text.strip()) > 5):
                    score += 1.0
                    
        except Exception as e:
            logger.error(f"任务特定质量检查失败: {e}")
            score = 0.5  # 默认给中等分数
            
        return min(score, 1.0)
    
    def _evaluate_label_quality(
        self, 
        sample: ExtractedSample, 
        spec: InternalSpec, 
        reasons: List[str]
    ) -> float:
        """评估标签质量"""
        score = 0.0
        
        # 根据任务类型检查标签格式
        if spec.task_type == "question_answering":
            # 问题格式检查
            if sample.input_text.strip().endswith(('?', '？')):
                score += 0.5
            else:
                reasons.append("问题格式不正确")
            
            # 答案完整性检查
            if len(sample.output_text.strip()) > 20:
                score += 0.5
            else:
                reasons.append("答案过短")
                
        elif spec.task_type == "text_classification":
            # 分类标签有效性检查
            if sample.output_text.strip() and len(sample.output_text.strip()) < 50:
                score += 0.5
            else:
                reasons.append("分类标签格式不正确")
            
            # 文本内容检查
            if len(sample.input_text.strip()) > 20:
                score += 0.5
            else:
                reasons.append("分类文本过短")
        else:
            # 其他任务类型的通用检查
            if sample.input_text.strip() and sample.output_text.strip():
                score += 1.0
        
        return min(score, 1.0)
    
    def _evaluate_source_reliability(
        self, 
        sample: ExtractedSample, 
        reasons: List[str]
    ) -> float:
        """评估来源可靠性"""
        score = 0.0
        
        # 域名可信度检查
        trusted_domains = ['.gov', '.edu', '.org', 'wikipedia', 'baidu', 'zhihu']
        domain_score = 0.0
        
        for trusted in trusted_domains:
            if trusted in sample.source_domain:
                domain_score = 1.0
                break
        
        if domain_score == 0.0:
            # 检查是否为常见不可信域名
            untrusted_domains = ['ads', 'spam', 'fake']
            for untrusted in untrusted_domains:
                if untrusted in sample.source_domain:
                    domain_score = 0.0
                    reasons.append(f"来源域名不可信: {sample.source_domain}")
                    break
            else:
                domain_score = 0.5  # 中性域名
        
        score += domain_score * 0.6
        
        # URL有效性检查
        if sample.source_url.startswith(('http://', 'https://')):
            score += 0.4
        else:
            reasons.append("URL格式无效")
        
        if score < self.thresholds.source_reliability_threshold:
            reasons.append(f"来源可靠性不足: {score:.2f}")
        
        return min(score, 1.0)
    
    def _evaluate_metadata_completeness(
        self, 
        sample: ExtractedSample, 
        reasons: List[str]
    ) -> float:
        """评估元数据完整性"""
        score = 0.0
        
        # 检查必需的元数据字段
        required_fields = ['page_title', 'extraction_time', 'task_type', 'domain']
        present_fields = sum(1 for field in required_fields if field in sample.metadata)
        
        score += (present_fields / len(required_fields)) * 0.8
        
        # 检查元数据质量
        if sample.metadata.get('page_title') and len(sample.metadata['page_title']) > 5:
            score += 0.2
        else:
            reasons.append("页面标题缺失或过短")
        
        return min(score, 1.0)
    
    def _check_grammar_quality(self, input_text: str, output_text: str) -> float:
        """检查语法质量"""
        score = 0.0
        
        # 简单的语法检查
        texts = [input_text, output_text]
        
        for text in texts:
            # 检查句子完整性
            if re.search(r'[.!?。！？]', text):
                score += 0.2
            
            # 检查标点符号合理性
            if not re.search(r'[.!?。！？]{2,}', text):  # 没有重复标点
                score += 0.2
            
            # 检查是否有基本的词汇结构
            if len(text.split()) >= 3:
                score += 0.1
        
        return min(score, 1.0)
    
    async def _calculate_semantic_similarity(self, input_text: str, output_text: str) -> float:
        """计算语义相似性"""
        if not HAS_SENTENCE_TRANSFORMERS or not self.sentence_model:
            return 0.5  # 模型未加载时给默认分数
        
        try:
            # 在线程池中计算embedding以避免阻塞
            loop = asyncio.get_event_loop()
            
            embeddings = await loop.run_in_executor(
                self.executor,
                lambda: self.sentence_model.encode([input_text, output_text])
            )
            
            # 计算余弦相似度
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # 对于QA任务，相似度应该在合理范围内（不能太高也不能太低）
            if 0.3 <= similarity <= 0.7:
                return 1.0
            elif similarity > 0.7:
                return 0.7  # 太相似可能是重复
            else:
                return similarity * 2  # 提升低相似度的分数
                
        except Exception as e:
            logger.debug(f"相似性计算失败: {str(e)}")
            return 0.5
    
    def _check_content_completeness(self, text: str) -> float:
        """检查内容完整性"""
        score = 0.0
        
        # 检查文本是否被截断
        if not text.endswith(('...', '。。。', '...')):
            score += 0.3
        
        # 检查是否有完整的句子结构
        sentences = re.split(r'[.!?。！？]', text)
        complete_sentences = [s for s in sentences if len(s.strip()) > 10]
        
        if len(complete_sentences) >= 2:
            score += 0.4
        elif len(complete_sentences) == 1:
            score += 0.2
        
        # 检查内容密度
        if len(text) > 100 and len(text.split()) > 15:
            score += 0.3
        
        return min(score, 1.0)
    
    def _is_sample_valid(self, quality_score: QualityScore, spec: InternalSpec) -> bool:
        """判断样本是否有效"""
        # 总分必须达到最低要求
        if quality_score.overall_score < self.thresholds.minimum_pass_rate:
            return False
        
        # 关键维度必须达到要求
        if quality_score.content_quality < 0.4:
            return False
        
        if quality_score.language_quality < self.thresholds.language_quality_threshold:
            return False
        
        if quality_score.source_reliability < self.thresholds.source_reliability_threshold:
            return False
        
        return True
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        elapsed_time = time.time() - self.start_time
        
        return {
            "validation_count": self.validation_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "pass_rate": self.passed_count / self.validation_count if self.validation_count > 0 else 0,
            "elapsed_time": elapsed_time,
            "validations_per_minute": (self.validation_count / elapsed_time * 60) if elapsed_time > 0 else 0,
            "model_loaded": self.sentence_model is not None
        }

# 创建全局实例
quality_validator = QualityValidator()