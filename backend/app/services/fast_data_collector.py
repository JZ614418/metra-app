"""
Fast Data Collector - 高速并发数据收集器
解决DataBuilder太慢的问题

核心优化：
1. 并发处理 - 同时处理多篇文章
2. 智能超时 - 减少AI处理时间
3. 缓存机制 - 避免重复请求
4. 快速失败 - 跳过问题URL
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
import json

from app.core.config import settings
from app.services.data_collection import DataCollectionService
from app.services.data_generation import DataGenerationService
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class FastDataCollector:
    """高速并发数据收集器 - 解决速度问题"""
    
    def __init__(self):
        self.web_service = DataCollectionService()
        self.ai_service = DataGenerationService()
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.jobs = {}  # 存储任务状态
        
        # 性能配置 - 大幅提升并发能力
        self.MAX_CONCURRENT_ARTICLES = 20  # 从5提升到20
        self.AI_TIMEOUT = 45  # AI处理单篇文章最多45秒（给AI更多时间提取更多样本）
        self.MAX_RETRIES = 2  # 最多重试2次（从3次降到2次）
        self.BATCH_SIZE = 10  # 批处理大小
        
        # 创建工作池
        self.article_processing_pool = asyncio.Queue(maxsize=100)
        self.result_collection_pool = asyncio.Queue(maxsize=1000)
        
    async def collect_data_fast(self, 
                               task_info: Dict[str, Any], 
                               target_count: int,
                               job_id: str,
                               progress_callback: Optional[Callable] = None,
                               enhanced_mode: bool = False) -> List[Dict]:
        """
        高速数据收集 - 核心优化方法
        
        性能目标：
        - 100条数据：< 5分钟（vs 当前的30+分钟）
        - 500条数据：< 15分钟（vs 当前的150+分钟）
        """
        
        logger.info(f"🚀 Starting FAST collection for job {job_id}")
        logger.info(f"Target: {target_count} samples - Performance Mode ON")
        
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
            
            # Step 1: 快速搜索 - 并发执行
            logger.info("📡 Step 1: Fast concurrent search...")
            search_queries = await self._generate_search_queries_fast(task_info, target_count)
            
            # 并发搜索所有查询
            search_tasks = [
                self._search_single_query(query, target_count)
                for query in search_queries
            ]
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 合并所有URL
            all_urls = []
            for result in search_results:
                if isinstance(result, list):
                    all_urls.extend(result)
            
            # 去重并根据目标数量动态设置URL数量
            unique_urls = list(set(all_urls))
            # 根据实际经验调整：每个URL平均约6-8个样本
            # 为了确保达到目标，需要处理更多URL
            max_urls = max(target_count // 6, 300)  # 至少300个URL，按每URL 6个样本计算
            if len(unique_urls) > max_urls:
                unique_urls = unique_urls[:max_urls]
            logger.info(f"📝 Found {len(unique_urls)} unique URLs for processing")
            
            if progress_callback:
                await progress_callback({
                    "status": "processing",
                    "message": f"Found {len(unique_urls)} articles, starting AI processing...",
                    "collected": 0,
                    "total": target_count
                })
            
            # Step 2: 高速并发AI处理 - 核心优化！
            logger.info("🤖 Step 2: Fast concurrent AI processing...")
            
            # 启动并发处理器
            processing_tasks = []
            
            # 创建所有处理任务
            for idx, url in enumerate(unique_urls):
                task = self._process_single_article_fast(
                    url, task_info, idx + 1, target_count, enhanced_mode
                )
                processing_tasks.append(task)
            
            # 使用信号量控制并发数
            semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_ARTICLES)
            
            async def process_with_semaphore(task):
                async with semaphore:
                    return await task
            
            # 包装所有任务
            controlled_tasks = [process_with_semaphore(task) for task in processing_tasks]
            
            # 等待所有处理完成，但使用as_completed来实时收集结果
            all_collected_data = []
            processed_count = 0
            
            for future in asyncio.as_completed(controlled_tasks):
                try:
                    result = await future
                    if result:
                        all_collected_data.extend(result)
                        processed_count += 1
                        
                        # 实时更新进度
                        self.jobs[job_id]["collected_count"] = len(all_collected_data)
                        self.jobs[job_id]["progress"] = int((processed_count / len(controlled_tasks)) * 100)
                        
                        if progress_callback:
                            await progress_callback({
                                "status": "processing",
                                "message": f"Processed {processed_count}/{len(controlled_tasks)} articles, collected {len(all_collected_data)} samples",
                                "collected": len(all_collected_data),
                                "total": target_count
                            })
                        
                        # 如果已经收集够了，可以提前停止
                        if len(all_collected_data) >= target_count * 1.2:
                            logger.info(f"🎯 Target exceeded! Got {len(all_collected_data)} samples")
                            break
                            
                except Exception as e:
                    logger.error(f"Article processing error: {e}")
                    continue
            
            # Step 3: 如果还不够，继续搜索更多URL或AI生成补足
            current_collected = len(all_collected_data)
            
            # 如果收集不够，继续搜索更多
            while current_collected < target_count:
                logger.info(f"📊 Current: {current_collected}/{target_count}, need more data...")
                
                # 生成额外的搜索查询
                additional_queries = await self._generate_search_queries_fast(task_info, target_count)
                additional_urls = []
                
                for query in additional_queries:
                    urls = await self._search_single_query(query, 50)
                    additional_urls.extend(urls)
                
                # 去重
                additional_urls = list(set(additional_urls) - set(unique_urls))
                logger.info(f"Found {len(additional_urls)} additional URLs")
                
                if len(additional_urls) == 0:
                    # 没有更多URL了，使用AI生成
                    break
                
                # 处理额外的URL
                for i in range(0, len(additional_urls), self.BATCH_SIZE):
                    batch_urls = additional_urls[i:i + self.BATCH_SIZE]
                    batch_tasks = [
                        self._process_single_article_fast(url, task_info, len(unique_urls) + i + j + 1, target_count, enhanced_mode)
                        for j, url in enumerate(batch_urls)
                    ]
                    
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, list) and result:
                            all_collected_data.extend(result)
                    
                    current_collected = len(all_collected_data)
                    
                    if progress_callback:
                        await progress_callback({
                            "status": "collecting",
                            "message": f"Collecting more data... Got {current_collected} samples",
                            "collected": current_collected,
                            "total": target_count
                        })
                    
                    if current_collected >= target_count:
                        break
                
                unique_urls.extend(additional_urls)
                
                # 防止无限循环
                if len(unique_urls) > 1000:
                    logger.info("Reached URL limit, stopping search")
                    break
            
            # Step 4: 如果还不够，AI生成补足
            remaining_needed = target_count - len(all_collected_data)
            if remaining_needed > 0:
                logger.info(f"🤖 Step 4: Fast AI generation for {remaining_needed} samples")
                
                try:
                    ai_generated = await asyncio.wait_for(
                        self.ai_service.generate_training_data(
                            task_description=task_info.get('description', ''),
                            task_type=task_info.get('type', 'classification'),
                            count=remaining_needed,
                            labels=task_info.get('labels', [])
                        ),
                        timeout=60  # AI生成最多60秒
                    )
                    
                    if ai_generated and 'data' in ai_generated:
                        generated_samples = ai_generated['data']
                        all_collected_data.extend(generated_samples)
                        logger.info(f"✨ Fast AI generated {len(generated_samples)} samples")
                        
                except asyncio.TimeoutError:
                    logger.warning("AI generation timed out, using collected data only")
                except Exception as e:
                    logger.error(f"AI generation failed: {e}")
            
            # 完成
            final_count = len(all_collected_data)
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"🎉 FAST collection completed!")
            logger.info(f"   Samples: {final_count}")
            logger.info(f"   Time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            logger.info(f"   Speed: {final_count/duration:.1f} samples/second")
            
            # 更新最终状态
            self.jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "collected": final_count,
                "end_time": end_time,
                "duration": duration
            })
            
            if progress_callback:
                await progress_callback({
                    "status": "completed",
                    "message": f"Fast collection completed! {final_count} samples in {duration/60:.1f} minutes",
                    "collected": final_count,
                    "total": target_count
                })
            
            return all_collected_data[:target_count]
            
        except Exception as e:
            logger.error(f"Fast collection failed: {e}")
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)
            
            if progress_callback:
                await progress_callback({
                    "status": "failed",
                    "message": f"Collection failed: {str(e)}",
                    "collected": len(all_collected_data),
                    "total": target_count
                })
            
            raise
    
    async def _generate_search_queries_fast(self, task_info: Dict, target_count: int) -> List[str]:
        """快速生成搜索查询"""
        
        # 基于目标数量动态生成查询数量 - 大幅增加以获得更多URL
        if target_count <= 100:
            num_queries = 8
        elif target_count <= 500:
            num_queries = 15
        elif target_count <= 1000:
            num_queries = 20
        elif target_count <= 2000:
            num_queries = 25
        elif target_count <= 5000:
            num_queries = 30
        else:
            num_queries = 40  # 大目标需要更多查询
        
        try:
            # 快速AI生成查询 - 减少超时时间
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",  # 使用更快的模型
                    messages=[
                        {
                            "role": "system",
                            "content": "你是搜索查询生成专家。根据任务生成多样化的中文搜索关键词。"
                        },
                        {
                            "role": "user",
                            "content": f"""
任务：{task_info.get('description', '')}
类型：{task_info.get('type', '')}
生成{num_queries}个不同的搜索关键词，用于收集相关数据。

要求：
1. 关键词要多样化，覆盖不同角度
2. 适合在搜索引擎中使用
3. 每行一个关键词
4. 只输出关键词，不要其他内容
"""
                        }
                    ],
                    temperature=0.7,
                    max_tokens=200
                ),
                timeout=15  # 15秒超时
            )
            
            queries = response.choices[0].message.content.strip().split('\n')
            queries = [q.strip() for q in queries if q.strip()]
            
            # 如果AI生成失败，使用默认查询
            if not queries:
                domain = task_info.get('domain', '通用')
                queries = [
                    f"{domain}相关内容",
                    f"{task_info.get('description', '')}",
                    f"{domain}案例"
                ]
            
            logger.info(f"Generated {len(queries)} search queries: {queries}")
            return queries[:num_queries]
            
        except Exception as e:
            logger.warning(f"Query generation failed, using defaults: {e}")
            # 备用查询
            return [
                task_info.get('description', '相关内容'),
                f"{task_info.get('domain', '通用')}案例",
                "相关信息"
            ]
    
    async def _search_single_query(self, query: str, target_count: int) -> List[str]:
        """搜索单个查询并返回URL列表"""
        try:
            # 根据目标数量调整每个查询的结果数 - 大幅增加
            results_per_query = min(max(target_count // 20, 20), 100)  # 每个查询最多100个结果
            
            results = await asyncio.wait_for(
                self.web_service.search_google(query, num_results=results_per_query),
                timeout=10  # 单个搜索最多10秒
            )
            
            if results:
                urls = [r.get('url') for r in results if r.get('url')]
                logger.info(f"Query '{query}' returned {len(urls)} URLs")
                return urls
            
        except Exception as e:
            logger.warning(f"Search failed for query '{query}': {e}")
        
        return []
    
    async def _process_single_article_fast(self, url: str, task_info: Dict, article_num: int, target_count: int = 1000, enhanced_mode: bool = False) -> List[Dict]:
        """快速处理单篇文章"""
        try:
            logger.info(f"🔍 Fast processing article {article_num}: {url[:50]}...")
            
            # 快速抓取文章
            article_data = await asyncio.wait_for(
                self.web_service.scrape_with_scrapingbee(url),
                timeout=15  # 抓取最多15秒
            )
            
            if not article_data or not article_data.get('content'):
                logger.warning(f"No content for article {article_num}")
                return []
            
            content = article_data['content']
            
            # 快速AI拆分 - 关键优化！
            if enhanced_mode:
                # 使用增强版收集器处理全文
                from app.services.enhanced_ai_collector import enhanced_ai_collector
                article_data = {'url': url, 'content': content}
                ai_samples = await enhanced_ai_collector.collect_from_article(article_data, task_info)
            else:
                # 使用标准快速处理
                ai_samples = await self._ai_split_article_fast(content, task_info, url, target_count)
            
            if ai_samples:
                logger.info(f"✨ Article {article_num} -> {len(ai_samples)} samples")
                return ai_samples
            else:
                logger.warning(f"❌ No samples from article {article_num}")
                return []
                
        except asyncio.TimeoutError:
            logger.warning(f"Article {article_num} timed out")
            return []
        except Exception as e:
            logger.warning(f"Article {article_num} failed: {e}")
            return []
    
    async def _ai_split_article_fast(self, content: str, task_info: Dict, url: str, target_count: int = 1000) -> List[Dict]:
        """快速AI拆分文章 - 核心性能优化"""
        
        # 根据目标数量动态调整内容长度限制
        if target_count <= 1000:
            max_chars = 6000
        elif target_count <= 5000:
            max_chars = 8000
        else:
            max_chars = 10000  # 大目标数量需要处理更多内容
        
        if len(content) > max_chars:
            content = content[:max_chars] + "..."
        
        task_description = task_info.get('description', '')
        task_type = task_info.get('type', 'classification')
        labels = task_info.get('labels', [])
        
        # 构建快速提示词
        if task_type == 'classification':
            prompt = f"""
从以下文章中尽可能多地提取训练样本：

任务：{task_description}
分类标签：{', '.join(labels)}

文章内容：
{content}

要求：
1. 提取尽可能多的有用样本（无数量限制，能提取多少就提取多少）
2. 每个样本应该是独立的句子或段落
3. 确保样本质量高，标签准确
4. 样本要有多样性，覆盖不同情感倾向
5. 不要有任何数量限制，文章内容允许的话可以提取100个或更多样本

请返回JSON格式：
{{"samples": [{{"text": "样本文本", "label": "标签"}}]}}

只返回JSON，不要其他内容。
"""
        else:
            prompt = f"""
从以下文章中尽可能多地提取训练样本：

任务：{task_description}
任务类型：{task_type}

文章内容：
{content}

要求：
1. 提取尽可能多的有用样本（无数量限制，能提取多少就提取多少）
2. 每个样本应该是独立且有意义的
3. 确保输入输出对应准确
4. 样本要有多样性
5. 不要有任何数量限制，文章内容允许的话可以提取100个或更多样本

请返回JSON格式：
{{"samples": [{{"input": "输入", "output": "输出"}}]}}

只返回JSON，不要其他内容。
"""
        
        # 快速AI处理 - 关键优化！
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await asyncio.wait_for(
                    self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",  # 使用更快的模型
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,  # 降低随机性提高速度
                        max_tokens=3000   # 大幅增加输出长度以获得更多样本
                    ),
                    timeout=self.AI_TIMEOUT  # 45秒超时
                )
                
                ai_response = response.choices[0].message.content
                
                # 改进的JSON解析 - 支持格式化的响应
                samples = []
                
                # 方法1: 直接解析整个响应（如果是纯JSON）
                try:
                    data = json.loads(ai_response.strip())
                    if 'samples' in data:
                        samples = data.get('samples', [])
                except json.JSONDecodeError:
                    # 方法2: 逐行查找JSON
                    lines = ai_response.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                data = json.loads(line)
                                if 'samples' in data:
                                    samples = data['samples']
                                    break
                            except:
                                continue
                    
                    # 方法3: 正则表达式提取JSON块 - 改进的模式
                    if not samples:
                        import re
                        # 更宽松的JSON匹配模式
                        json_pattern = r'\{[^{}]*"samples"[^{}]*\[[^\]]*\][^{}]*\}'
                        matches = re.findall(json_pattern, ai_response, re.DOTALL)
                        
                        for match in matches:
                            try:
                                data = json.loads(match)
                                if 'samples' in data:
                                    samples = data['samples']
                                    break
                            except:
                                continue
                        
                        # 方法4: 如果还是没有找到，尝试提取大括号内的内容
                        if not samples:
                            brace_pattern = r'\{.*?"samples".*?\[.*?\].*?\}'
                            matches = re.findall(brace_pattern, ai_response, re.DOTALL)
                            for match in matches:
                                try:
                                    # 尝试修复常见的JSON格式错误
                                    fixed_match = match.replace("'", '"')
                                    data = json.loads(fixed_match)
                                    if 'samples' in data:
                                        samples = data['samples']
                                        break
                                except:
                                    continue
                
                if samples:
                    # 快速验证样本
                    valid_samples = []
                    for sample in samples:  # 处理所有样本，不限制数量
                        if isinstance(sample, dict) and (sample.get('text') or sample.get('input')):
                            sample['source'] = url
                            sample['confidence'] = 0.8  # 固定置信度，提高速度
                            valid_samples.append(sample)
                    
                    if valid_samples:
                        logger.info(f"✅ Fast AI extracted {len(valid_samples)} samples (attempt {attempt + 1})")
                        return valid_samples
                
                logger.warning(f"Invalid AI response format (attempt {attempt + 1})")
                
            except asyncio.TimeoutError:
                logger.warning(f"AI processing timed out (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"AI processing failed (attempt {attempt + 1}): {e}")
            
            # 快速重试，不等待
            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(1)
        
        logger.warning("Fast AI splitting failed after all attempts")
        return []
    
    def get_job_status(self, job_id: str) -> Dict:
        """获取任务状态"""
        return self.jobs.get(job_id, {"status": "not_found"})
    
    def get_job_data(self, job_id: str) -> List[Dict]:
        """获取任务数据 - 这里应该从数据库获取"""
        # TODO: 实现真正的数据持久化
        return []

# 创建全局实例
fast_collector = FastDataCollector()