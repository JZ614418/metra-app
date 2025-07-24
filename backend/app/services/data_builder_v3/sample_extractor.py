"""
SampleExtractor - 样本提取器
使用GPT从页面内容中提取高质量训练样本，支持速率限制和批处理
"""

import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import tenacity
from openai import AsyncOpenAI, RateLimitError
from app.core.config import settings
from app.services.data_builder_v3.config import InternalSpec, config
from app.services.data_builder_v3.page_scraper import ScrapedPage
from app.services.data_builder_v3.query_generator import OpenAIRateLimiter
from app.services.data_builder_v3.together_client import TogetherClient

logger = logging.getLogger(__name__)

@dataclass
class ExtractedSample:
    """提取的训练样本"""
    input_text: str
    output_text: str
    source_url: str
    source_domain: str
    extraction_confidence: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "input": self.input_text,
            "output": self.output_text,
            "source_url": self.source_url,
            "source_domain": self.source_domain,
            "extraction_confidence": self.extraction_confidence,
            "metadata": self.metadata
        }

class SampleExtractor:
    """样本提取器"""
    
    def __init__(self):
        # 根据配置选择AI客户端
        if config.ai_provider == "together":
            self.ai_client = TogetherClient(
                api_key=config.together.api_key,
                base_url=config.together.base_url
            )
            self.rate_limiter = OpenAIRateLimiter(
                rpm_limit=config.performance.max_together_rpm,
                tpm_limit=config.performance.max_together_tpm
            )
            self.use_together = True
        else:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.rate_limiter = OpenAIRateLimiter(
                rpm_limit=config.performance.max_openai_rpm,
                tpm_limit=config.performance.max_openai_tpm
            )
            self.use_together = False
        
        # 统计信息
        self.extraction_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.start_time = time.time()
    
    async def extract_samples_from_pages(
        self, 
        pages: List[ScrapedPage], 
        spec: InternalSpec,
        target_samples: int = 1000
    ) -> List[ExtractedSample]:
        """
        从页面列表中提取训练样本
        
        Args:
            pages: 抓取的页面列表
            spec: 内部任务规范
            target_samples: 目标样本数量
            
        Returns:
            List[ExtractedSample]: 提取的样本列表
        """
        logger.info(f"🔍 开始样本提取: {len(pages)}个页面 -> 目标{target_samples}个样本")
        
        all_samples = []
        # 根据AI提供商调整并发数
        concurrent_limit = 100 if self.use_together else 20
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        # 按页面质量分数排序
        sorted_pages = sorted(pages, key=lambda x: x.quality_score, reverse=True)
        
        # 分批处理页面
        for i in range(0, len(sorted_pages), config.performance.batch_size):
            batch_pages = sorted_pages[i:i + config.performance.batch_size]
            
            # 并发提取当前批次
            tasks = [
                self._extract_samples_from_page(page, spec, semaphore)
                for page in batch_pages
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for result in batch_results:
                if isinstance(result, list):
                    all_samples.extend(result)
                    self.success_count += 1
                elif isinstance(result, Exception):
                    self.failure_count += 1
                    logger.debug(f"样本提取失败: {str(result)}")
            
            # 检查是否达到目标
            if len(all_samples) >= target_samples:
                break
                
            # 简单的速率控制
            await asyncio.sleep(0.2)
        
        # 按置信度排序并截取目标数量
        all_samples.sort(key=lambda x: x.extraction_confidence, reverse=True)
        final_samples = all_samples[:target_samples]
        
        logger.info(f"✅ 样本提取完成: {len(final_samples)}个样本, 成功率: {self._get_success_rate():.1%}")
        return final_samples
    
    async def _extract_samples_from_page(
        self, 
        page: ScrapedPage, 
        spec: InternalSpec, 
        semaphore: asyncio.Semaphore
    ) -> List[ExtractedSample]:
        """从单个页面提取样本"""
        async with semaphore:
            try:
                # 等待速率限制
                await self.rate_limiter.acquire(estimated_tokens=2000)
                
                # 准备提取prompt
                prompt = self._prepare_extraction_prompt(page, spec)
                
                # 调用AI提取
                response = await self._call_ai_with_retry(prompt, max_tokens=2000)
                
                # 解析响应
                samples = self._parse_extraction_response(response, page, spec)
                
                self.extraction_count += 1
                return samples
                
            except Exception as e:
                logger.error(f"页面样本提取失败 {page.url}: {str(e)}")
                return []
    
    def _prepare_extraction_prompt(self, page: ScrapedPage, spec: InternalSpec) -> str:
        """准备提取prompt"""
        # 截取页面内容以避免token限制
        max_content_length = 3000
        content = page.content[:max_content_length]
        if len(page.content) > max_content_length:
            content += "\n...(内容已截断)"
        
        # 对TogetherAI使用更严格的JSON格式要求
        if self.use_together:
            # 为开源模型添加更明确的JSON示例
            json_example = {
                "question_answering": '[{"input": "这是问题？", "output": "这是详细的答案..."}]',
                "text_classification": '[{"text": "这是文本内容...", "label": "类别"}]', 
                "text_generation": '[{"input": "输入文本", "output": "生成的输出"}]'
            }.get(spec.task_type, '[{"input": "问题", "output": "答案"}]')
            
            # 修改模板，添加更强的JSON格式指示
            template = spec.extraction_template.replace(
                "返回JSON数组格式：", 
                f"必须返回标准JSON数组，不要添加任何其他文字。示例格式：\n{json_example}\n\n实际返回："
            )
            
            # 使用修改后的模板
            prompt = template.format(
                page_text=content,
                domain=spec.domain,
                task_type=spec.task_type,
                language=spec.language
            )
        else:
            # OpenAI使用原有模板
            prompt = spec.extraction_template.format(
                page_text=content,
                domain=spec.domain,
                task_type=spec.task_type,
                language=spec.language
            )
        
        return prompt
    
    def _parse_extraction_response(
        self, 
        response: str, 
        page: ScrapedPage, 
        spec: InternalSpec
    ) -> List[ExtractedSample]:
        """解析GPT响应"""
        samples = []
        
        try:
            # 提取JSON内容
            json_content = self._extract_json_from_response(response)
            
            if not json_content:
                logger.debug(f"无法从响应中提取JSON: {page.url}")
                return []
            
            # 解析JSON
            parsed_data = json.loads(json_content)
            
            # 处理不同的数据格式
            if isinstance(parsed_data, list):
                sample_list = parsed_data
            elif isinstance(parsed_data, dict) and 'samples' in parsed_data:
                sample_list = parsed_data['samples']
            elif isinstance(parsed_data, dict) and 'data' in parsed_data:
                sample_list = parsed_data['data']
            elif isinstance(parsed_data, dict):
                # 如果是单个字典且包含必要字段，作为单个样本
                if any(key in parsed_data for key in ['input', 'text', 'question']):
                    sample_list = [parsed_data]
                else:
                    logger.debug(f"字典格式不正确，缺少必要字段: {page.url}")
                    return []
            else:
                # 如果不是列表或字典，记录错误
                logger.debug(f"解析结果类型错误，期望列表或字典，实际: {type(parsed_data).__name__} - {page.url}")
                return []
            
            # 创建样本对象
            for sample_data in sample_list:
                if isinstance(sample_data, dict):
                    sample = self._create_sample_from_dict(sample_data, page, spec)
                    if sample:
                        samples.append(sample)
                else:
                    logger.debug(f"跳过非字典类型的样本: {type(sample_data).__name__}")
            
            logger.debug(f"成功提取 {len(samples)} 个样本: {page.url}")
            
        except json.JSONDecodeError as e:
            logger.debug(f"JSON解析失败 {page.url}: {str(e)}")
        except Exception as e:
            logger.error(f"响应解析失败 {page.url}: {str(e)}")
        
        return samples
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """从响应中提取JSON内容"""
        if not response:
            return None
        
        # 方法1: 寻找```json代码块
        if '```json' in response:
            start = response.find('```json') + 7
            end = response.find('```', start)
            if end > start:
                return response[start:end].strip()
        
        # 方法2: 寻找JSON对象
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(response):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    return response[start_idx:i+1]
        
        # 方法3: 寻找JSON数组
        bracket_count = 0
        start_idx = -1
        
        for i, char in enumerate(response):
            if char == '[':
                if bracket_count == 0:
                    start_idx = i
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0 and start_idx != -1:
                    return response[start_idx:i+1]
        
        return None
    
    def _create_sample_from_dict(
        self, 
        sample_data: Dict[str, Any], 
        page: ScrapedPage, 
        spec: InternalSpec
    ) -> Optional[ExtractedSample]:
        """从字典创建样本对象"""
        try:
            # 根据任务类型提取不同字段
            if spec.task_type == "question_answering":
                input_text = sample_data.get('input', sample_data.get('question', ''))
                output_text = sample_data.get('output', sample_data.get('answer', ''))
            elif spec.task_type == "text_classification":
                input_text = sample_data.get('text', sample_data.get('input', ''))
                output_text = sample_data.get('label', sample_data.get('output', ''))
            else:
                input_text = sample_data.get('input', '')
                output_text = sample_data.get('output', '')
            
            # 验证样本质量
            if not input_text or not output_text:
                return None
            
            # 移除长度限制 - 允许各种长度的样本以适应不同模型训练需求
            
            # 计算置信度
            confidence = self._calculate_extraction_confidence(
                input_text, output_text, page, spec
            )
            
            return ExtractedSample(
                input_text=input_text.strip(),
                output_text=output_text.strip(),
                source_url=page.url,
                source_domain=page.source_domain,
                extraction_confidence=confidence,
                metadata={
                    'page_title': page.title,
                    'page_quality': page.quality_score,
                    'extraction_time': time.time(),
                    'task_type': spec.task_type,
                    'domain': spec.domain
                }
            )
            
        except Exception as e:
            logger.debug(f"样本创建失败: {str(e)}")
            return None
    
    def _calculate_extraction_confidence(
        self, 
        input_text: str, 
        output_text: str, 
        page: ScrapedPage, 
        spec: InternalSpec
    ) -> float:
        """计算提取置信度"""
        confidence = 0.0
        
        # 页面质量贡献 (30%)
        confidence += page.quality_score * 0.3
        
        # 内容长度贡献 (20%)
        if len(output_text) > 200:
            confidence += 0.2
        elif len(output_text) > 100:
            confidence += 0.15
        elif len(output_text) > 50:
            confidence += 0.1
        
        # 关键词匹配贡献 (25%)
        required_keywords = spec.quality_rules.get('required_keywords', [])
        if required_keywords:
            matched_keywords = 0
            for keyword in required_keywords:
                if keyword in input_text or keyword in output_text:
                    matched_keywords += 1
            confidence += (matched_keywords / len(required_keywords)) * 0.25
        else:
            confidence += 0.25  # 如果没有关键词要求，给满分
        
        # 格式正确性贡献 (25%)
        if spec.task_type == "question_answering":
            if input_text.endswith('？') or input_text.endswith('?'):
                confidence += 0.15
            if len(output_text.split()) > 10:  # 答案有一定长度
                confidence += 0.1
        else:
            confidence += 0.25  # 其他任务类型给满分
        
        return min(confidence, 1.0)
    
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type((RateLimitError, Exception))
    )
    async def _call_ai_with_retry(self, prompt: str, max_tokens: int = 1500) -> str:
        """带重试的AI调用"""
        try:
            if self.use_together:
                # 使用TogetherAI (平衡模型，用于大批量样本提取)
                model = config.get_model_for_task("balanced")
                return await self.ai_client.generate_chat(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.3
                )
            else:
                # 使用OpenAI
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            
        except RateLimitError as e:
            logger.warning(f"AI速率限制: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"AI调用失败: {str(e)}")
            raise
    
    def _get_success_rate(self) -> float:
        """获取成功率"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """获取提取统计信息"""
        elapsed_time = time.time() - self.start_time
        
        return {
            "extraction_count": self.extraction_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self._get_success_rate(),
            "elapsed_time": elapsed_time,
            "extractions_per_minute": (self.extraction_count / elapsed_time * 60) if elapsed_time > 0 else 0,
            "rate_limit_status": self.rate_limiter.get_current_usage()
        }

# 创建全局实例
sample_extractor = SampleExtractor()