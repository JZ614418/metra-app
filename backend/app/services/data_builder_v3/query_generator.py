"""
QueryGenerator - 智能搜索词生成器
基于任务规范生成精准搜索词，包含OpenAI速率限制
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque

import tenacity
from openai import AsyncOpenAI, RateLimitError
from app.core.config import settings
from app.services.data_builder_v3.config import InternalSpec, config
from app.services.data_builder_v3.together_client import TogetherClient

logger = logging.getLogger(__name__)

@dataclass
class SearchQuery:
    """搜索查询对象"""
    query: str
    priority: int = 1  # 1=高优先级, 2=中优先级, 3=低优先级
    site_filter: Optional[str] = None
    negative_keywords: List[str] = None
    estimated_results: int = 100
    
    def __post_init__(self):
        if self.negative_keywords is None:
            self.negative_keywords = []
    
    def to_search_string(self) -> str:
        """转换为搜索引擎查询字符串"""
        query_parts = [self.query]
        
        # 添加站点过滤
        if self.site_filter:
            query_parts.append(f"site:{self.site_filter}")
        
        # 添加负面关键词
        for neg_keyword in self.negative_keywords:
            if not neg_keyword.startswith('-'):
                neg_keyword = f"-{neg_keyword}"
            query_parts.append(neg_keyword)
        
        return " ".join(query_parts)

class OpenAIRateLimiter:
    """OpenAI速率限制器"""
    
    def __init__(self, rpm_limit: int = 3000, tpm_limit: int = 40000):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        
        # 请求历史 (时间戳, token数)
        self.request_history = deque()
        self.token_history = deque()
        
        # 当前窗口统计
        self.current_rpm = 0
        self.current_tpm = 0
        
        # 锁
        self.lock = asyncio.Lock()
    
    async def acquire(self, estimated_tokens: int = 1000):
        """获取API调用权限"""
        async with self.lock:
            now = time.time()
            
            # 清理过期记录
            self._cleanup_history(now)
            
            # 检查是否超过限制
            if self.current_rpm >= self.rpm_limit:
                wait_time = 60 - (now - self.request_history[0])
                logger.warning(f"RPM限制，等待{wait_time:.1f}秒")
                await asyncio.sleep(wait_time)
                return await self.acquire(estimated_tokens)
            
            if self.current_tpm + estimated_tokens > self.tpm_limit:
                wait_time = 60 - (now - self.token_history[0][0])
                logger.warning(f"TPM限制，等待{wait_time:.1f}秒")
                await asyncio.sleep(wait_time)
                return await self.acquire(estimated_tokens)
            
            # 记录请求
            self.request_history.append(now)
            self.token_history.append((now, estimated_tokens))
            self.current_rpm += 1
            self.current_tpm += estimated_tokens
    
    def _cleanup_history(self, now: float):
        """清理过期的历史记录"""
        # 清理RPM历史
        while self.request_history and now - self.request_history[0] > 60:
            self.request_history.popleft()
        self.current_rpm = len(self.request_history)
        
        # 清理TPM历史
        while self.token_history and now - self.token_history[0][0] > 60:
            _, tokens = self.token_history.popleft()
            self.current_tpm -= tokens
    
    def get_current_usage(self) -> Dict[str, Any]:
        """获取当前使用情况"""
        return {
            "rpm": self.current_rpm,
            "rpm_limit": self.rpm_limit,
            "tpm": self.current_tpm,
            "tpm_limit": self.tpm_limit,
            "rpm_usage": self.current_rpm / self.rpm_limit,
            "tpm_usage": self.current_tpm / self.tpm_limit
        }

class QueryGenerator:
    """智能搜索词生成器"""
    
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
    
    async def generate_search_queries(self, spec: InternalSpec, target_count: int = 50) -> List[SearchQuery]:
        """
        生成搜索查询列表
        
        Args:
            spec: 内部任务规范
            target_count: 目标查询数量
            
        Returns:
            List[SearchQuery]: 搜索查询列表
        """
        try:
            logger.info(f"🔍 开始生成搜索词: {spec.domain}/{spec.task_type}")
            
            # 生成基础查询
            base_queries = await self._generate_base_queries(spec, target_count)
            
            # 生成变体查询
            variant_queries = await self._generate_variant_queries(spec, base_queries)
            
            # 生成站点特定查询
            site_queries = self._generate_site_specific_queries(spec, base_queries)
            
            # 合并和去重
            all_queries = base_queries + variant_queries + site_queries
            unique_queries = self._deduplicate_queries(all_queries)
            
            # 按优先级排序
            sorted_queries = sorted(unique_queries, key=lambda q: q.priority)
            
            logger.info(f"✅ 生成搜索词完成: {len(sorted_queries)}条查询")
            return sorted_queries[:target_count]
            
        except Exception as e:
            logger.error(f"❌ 搜索词生成失败: {str(e)}")
            # 返回备用查询
            return self._generate_fallback_queries(spec)
    
    async def _generate_base_queries(self, spec: InternalSpec, count: int) -> List[SearchQuery]:
        """生成基础查询"""
        
        # 等待速率限制
        await self.rate_limiter.acquire(estimated_tokens=1500)
        
        prompt = f"""
你是一个搜索专家，需要为{spec.domain}领域的{spec.task_type}任务生成{count}条精准搜索词。

任务信息：
- 领域: {spec.domain}
- 任务类型: {spec.task_type}
- 语言: {spec.language}
- 基础关键词: {spec.search_strategy.get('base_keywords', [])}
- 质量要求: {spec.quality_rules}

请生成多样化的搜索词，包括：
1. 直接相关词汇
2. 同义词变体
3. 专业术语
4. 常见问题模式
5. 相关子主题

要求：
- 搜索词要准确且多样化
- 适合在百度、Google等搜索引擎使用
- 避免过于宽泛的词汇
- 优先考虑能找到高质量内容的词汇

返回JSON格式，包含查询列表：
{{
  "queries": [
    {{
      "query": "具体搜索词",
      "priority": 1,
      "estimated_results": 100,
      "reasoning": "选择理由"
    }}
  ]
}}

只返回JSON，无需其他说明。
"""
        
        try:
            response = await self._call_ai_with_retry(prompt, max_tokens=1500)
            
            # 解析响应
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.rfind('```')
                response = response[json_start:json_end]
            elif '{' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                response = response[json_start:json_end]
            
            result = json.loads(response)
            queries = []
            
            for query_data in result.get('queries', []):
                query = SearchQuery(
                    query=query_data['query'],
                    priority=query_data.get('priority', 1),
                    estimated_results=query_data.get('estimated_results', 100),
                    negative_keywords=spec.search_strategy.get('negative_keywords', [])
                )
                queries.append(query)
            
            logger.info(f"✅ 生成基础查询: {len(queries)}条")
            return queries
            
        except Exception as e:
            logger.error(f"❌ 基础查询生成失败: {str(e)}")
            return self._generate_fallback_queries(spec)
    
    async def _generate_variant_queries(self, spec: InternalSpec, base_queries: List[SearchQuery]) -> List[SearchQuery]:
        """生成变体查询"""
        
        if not base_queries:
            return []
        
        # 选择前5个高优先级查询生成变体
        top_queries = [q for q in base_queries if q.priority == 1][:5]
        
        variant_queries = []
        
        for base_query in top_queries:
            try:
                await self.rate_limiter.acquire(estimated_tokens=800)
                
                prompt = f"""
基于搜索词"{base_query.query}"，为{spec.domain}领域生成5个变体搜索词。

变体类型：
1. 同义词替换
2. 添加限定词
3. 不同表达方式
4. 相关子主题
5. 问句形式

要求：
- 保持原意但表达不同
- 适合{spec.language}语言
- 避免过于相似

返回JSON格式：
{{
  "variants": ["变体1", "变体2", "变体3", "变体4", "变体5"]
}}
"""
                
                response = await self._call_ai_with_retry(prompt, max_tokens=800)
                
                # 解析变体
                if '```json' in response:
                    json_start = response.find('```json') + 7
                    json_end = response.rfind('```')
                    response = response[json_start:json_end]
                elif '{' in response:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    response = response[json_start:json_end]
                
                result = json.loads(response)
                
                for variant in result.get('variants', []):
                    variant_query = SearchQuery(
                        query=variant,
                        priority=2,  # 变体优先级为2
                        estimated_results=50,
                        negative_keywords=spec.search_strategy.get('negative_keywords', [])
                    )
                    variant_queries.append(variant_query)
                    
            except Exception as e:
                logger.warning(f"变体生成失败: {str(e)}")
                continue
        
        logger.info(f"✅ 生成变体查询: {len(variant_queries)}条")
        return variant_queries
    
    def _generate_site_specific_queries(self, spec: InternalSpec, base_queries: List[SearchQuery]) -> List[SearchQuery]:
        """生成站点特定查询"""
        
        # 获取可信站点列表
        trusted_sites = spec.search_strategy.get('site_whitelist', [])
        
        # 选择适合的站点
        suitable_sites = []
        for site in trusted_sites:
            if any(domain in site for domain in ['baidu.com', 'zhihu.com', 'wikipedia.org']):
                suitable_sites.append(site)
        
        site_queries = []
        
        # 为每个高优先级查询生成站点特定版本
        for base_query in base_queries[:10]:  # 限制基础查询数量
            if base_query.priority == 1:
                for site in suitable_sites[:3]:  # 限制站点数量
                    site_query = SearchQuery(
                        query=base_query.query,
                        priority=2,
                        site_filter=site,
                        negative_keywords=base_query.negative_keywords,
                        estimated_results=30
                    )
                    site_queries.append(site_query)
        
        logger.info(f"✅ 生成站点查询: {len(site_queries)}条")
        return site_queries
    
    def _deduplicate_queries(self, queries: List[SearchQuery]) -> List[SearchQuery]:
        """去重查询"""
        seen = set()
        unique_queries = []
        
        for query in queries:
            # 创建唯一标识
            unique_key = (query.query.lower(), query.site_filter)
            
            if unique_key not in seen:
                seen.add(unique_key)
                unique_queries.append(query)
        
        logger.info(f"✅ 去重完成: {len(queries)} -> {len(unique_queries)}")
        return unique_queries
    
    def _generate_fallback_queries(self, spec: InternalSpec) -> List[SearchQuery]:
        """生成备用查询"""
        logger.warning("使用备用查询生成策略")
        
        base_keywords = spec.search_strategy.get('base_keywords', [])
        negative_keywords = spec.search_strategy.get('negative_keywords', [])
        
        fallback_queries = []
        
        # 基于基础关键词生成
        for keyword in base_keywords[:10]:
            query = SearchQuery(
                query=keyword,
                priority=1,
                negative_keywords=negative_keywords,
                estimated_results=50
            )
            fallback_queries.append(query)
        
        # 添加一些通用查询
        domain_queries = {
            'tcm': ['中医药', '中药方剂', '中医诊疗'],
            'finance': ['金融投资', '财务管理', '投资理财'],
            'legal': ['法律法规', '法律咨询', '司法实务'],
            'education': ['教育培训', '学习方法', '教学资源']
        }
        
        domain_specific = domain_queries.get(spec.domain, [])
        for query_str in domain_specific:
            query = SearchQuery(
                query=query_str,
                priority=2,
                negative_keywords=negative_keywords,
                estimated_results=30
            )
            fallback_queries.append(query)
        
        return fallback_queries
    
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type((RateLimitError, Exception))
    )
    async def _call_ai_with_retry(self, prompt: str, max_tokens: int = 1000) -> str:
        """带重试的AI调用"""
        try:
            if self.use_together:
                # 使用TogetherAI (平衡模型，用于搜索词生成)
                model = config.get_model_for_task("balanced")
                return await self.ai_client.generate_chat(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
            else:
                # 使用OpenAI
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            
        except RateLimitError as e:
            logger.warning(f"AI速率限制: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"AI调用失败: {str(e)}")
            raise
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """获取速率限制状态"""
        return self.rate_limiter.get_current_usage()

# 创建全局实例
query_generator = QueryGenerator()