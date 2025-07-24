"""
Optimized data collection service with parallel processing and batching
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
import time
from datetime import datetime
import aiohttp
import random
import json
import logging

from app.core.config import settings
from app.services.data_collection import DataCollectionService
from app.services.data_generation import DataGenerationService
from app.services.enhanced_ai_collector import enhanced_ai_collector
from openai import AsyncOpenAI

# Configure logging for better monitoring
logger = logging.getLogger(__name__)


class OptimizedDataCollector:
    """Optimized data collection with smart batching and parallel processing"""
    
    def __init__(self):
        self.web_service = DataCollectionService()
        self.ai_service = DataGenerationService()
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def calculate_optimal_strategy(self, 
                                       target_count: int,
                                       task_type: str,
                                       language: str) -> Dict[str, Any]:
        """Calculate optimal data collection strategy based on target count"""
        
        # Optimized strategy for faster web collection
        if target_count <= 1000:
            strategy = {"web_percentage": 0.7, "ai_percentage": 0.3, "batch_size": 200, "parallel_workers": 10, "estimated_time_minutes": 3}
        elif target_count <= 5000:
            strategy = {"web_percentage": 0.5, "ai_percentage": 0.5, "batch_size": 1000, "parallel_workers": 15, "estimated_time_minutes": 10}
        elif target_count <= 20000:
            strategy = {"web_percentage": 0.3, "ai_percentage": 0.7, "batch_size": 2000, "parallel_workers": 20, "estimated_time_minutes": 30}
        else:
            # For large datasets, with smart article splitting, web becomes much more valuable!
            strategy = {"web_percentage": 0.25, "ai_percentage": 0.75, "batch_size": 5000, "parallel_workers": 25, "estimated_time_minutes": target_count / 3000}  # Faster due to article splitting
        
        if language == "chinese":
            strategy["web_percentage"] *= 0.7
            strategy["ai_percentage"] = 1 - strategy["web_percentage"]
            strategy["estimated_time_minutes"] *= 1.2
        
        return strategy
    
    async def _web_producer(self, queue: asyncio.Queue, target_count: int, task_info: Dict, strategy: Dict):
        """Producer for web scraping with retries"""
        collected_count = 0
        base_query = f"{task_info.get('type', '')} {task_info.get('description', '')}"
        # Generate more query variations for better coverage
        queries = self._generate_query_variations(base_query, min(int(target_count / 50), 50))  # Up to 50 different queries
        
        retry_count = 0
        max_retries = 5
        
        while collected_count < target_count and retry_count < max_retries:
            try:
                # Massive parallel search with multiple queries
                batch_tasks = []
                queries_to_use = random.sample(queries, min(len(queries), 10))  # Use 10 different queries in parallel
                
                for query in queries_to_use:
                    # Each query gets multiple searches with higher result counts
                    batch_tasks.extend([
                        asyncio.create_task(self.web_service.search_google(query, 100)),  # 100 results per query
                        asyncio.create_task(self.web_service.search_serper(query, 100)),  # 100 results per query
                        asyncio.create_task(self.web_service.search_wikipedia(query, 20))  # Wikipedia for each query
                    ])
                
                # Wait for all massive parallel searches
                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*batch_tasks, return_exceptions=True),
                        timeout=30.0  # Longer timeout for more requests
                    )
                    
                    batch_data = []
                    for result in results:
                        if isinstance(result, list):
                            batch_data.extend(result)
                    
                    # Remove duplicates by URL
                    seen_urls = set()
                    unique_data = []
                    for item in batch_data:
                        url = item.get('url', '')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            unique_data.append(item)
                    
                    batch_data = unique_data
                    print(f"Web batch collected {len(batch_data)} unique results from {len(batch_tasks)} searches")
                    
                except asyncio.TimeoutError:
                    print("Web search batch timeout, continuing...")
                    batch_data = []
                
                if batch_data:
                    # 🚀 Smart Strategy: Split each article into multiple training samples!
                    enhanced_items = []
                    
                    # First, use ScrapingBee to get complete articles
                    enhancement_tasks = []
                    for item in batch_data[:15]:  # Limit to control costs
                        url = item.get('url', '')
                        if await self.web_service._is_whitelisted(url):
                            enhancement_tasks.append({
                                'task': self.web_service.scrape_with_scrapingbee(url),
                                'original_item': item
                            })
                    
                    # Concurrently fetch complete articles
                    if enhancement_tasks:
                        tasks = [task_info['task'] for task_info in enhancement_tasks]
                        enhanced_contents = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        for i, enhanced in enumerate(enhanced_contents):
                            if isinstance(enhanced, dict) and enhanced.get('content'):
                                content_length = len(enhanced['content'])
                                
                                # 🤖 Use AI to filter and split ALL articles for quality
                                try:
                                    extracted_samples = await self._extract_training_samples_from_article(
                                        enhanced['content'], task_info
                                    )
                                    
                                    # Add original URL info to each sample
                                    original_url = enhancement_tasks[i]['original_item'].get('url', '')
                                    for sample in extracted_samples:
                                        sample['original_url'] = original_url
                                        sample['article_length'] = content_length
                                    
                                    enhanced_items.extend(extracted_samples)
                                    print(f"✨ AI filtered and extracted {len(extracted_samples)} quality samples from article ({content_length} chars)")
                                    
                                except Exception as e:
                                    print(f"AI filtering failed: {e}, skipping article")
                                    # If AI fails, skip this article entirely - we want quality only
                                    continue
                    
                    # Add split samples to queue
                    all_samples = list(batch_data) + enhanced_items  # 包含原始数据和拆分数据
                    
                    for item in all_samples:
                        if collected_count < target_count:
                            await queue.put(item)
                            collected_count += 1
                        else:
                            break
                    
                    retry_count = 0  # Reset retry count on success
                    print(f"📦 Web批次收集: {len(all_samples)} 个样本 (包含 {len(enhanced_items)} 个AI拆分样本)")
                else:
                    retry_count += 1
                    print(f"Web producer: No data returned, retry {retry_count}/{max_retries}")
                    await asyncio.sleep(2)

            except Exception as e:
                retry_count += 1
                print(f"Web producer error (retry {retry_count}/{max_retries}): {e}")
                await asyncio.sleep(min(5 * retry_count, 30))  # Exponential backoff
                
        print(f"Web producer finished: collected {collected_count}/{target_count} items")

    async def _ai_producer(self, queue: asyncio.Queue, target_count: int, task_info: Dict, strategy: Dict):
        """Producer for AI generation with retries"""
        collected_count = 0
        batch_size = min(strategy.get("batch_size", 50), 50)

        while collected_count < target_count:
            try:
                needed = target_count - collected_count
                current_batch_size = min(batch_size, needed)
                
                batch_data = await self.ai_service.generate_training_data(
                    task_type=task_info.get("type", "classification"),
                    task_description=task_info.get("description", ""),
                    count=current_batch_size,
                    labels=task_info.get("labels", []),
                    style="balanced"
                )
                
                for item in batch_data:
                    if collected_count < target_count:
                        await queue.put(item)
                        collected_count += 1
                    else:
                        break
                
                if not batch_data:
                    await asyncio.sleep(2)
            
            except Exception as e:
                print(f"AI producer error: {e}")
                await asyncio.sleep(10)

    async def collect_optimized(self,
                              task_info: Dict[str, Any],
                              target_count: int,
                              progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Main optimized collection method using a producer-consumer model"""
        
        start_time = time.time()
        
        strategy = await self.calculate_optimal_strategy(
            target_count,
            task_info.get("type", "classification"),
            task_info.get("language", "english")
        )
        
        web_target = int(target_count * strategy["web_percentage"])
        ai_target = target_count - web_target
        
        data_queue = asyncio.Queue()
        all_data = []
        
        # Start producers
        producers = []
        if web_target > 0:
            producers.append(self._web_producer(data_queue, web_target, task_info, strategy))
        if ai_target > 0:
            producers.append(self._ai_producer(data_queue, ai_target, task_info, strategy))
        
        producer_task = asyncio.gather(*producers)

        # Enhanced consumer loop with cloud-optimized timeout handling
        consecutive_timeouts = 0
        max_consecutive_timeouts = settings.MAX_CONSECUTIVE_TIMEOUTS
        queue_timeout = settings.QUEUE_TIMEOUT
        
        logger.info(f"Starting SUPER PATIENT consumer: timeout={queue_timeout}s, max_timeouts={max_consecutive_timeouts}")
        logger.info(f"🤖 AI splitting enabled - will wait patiently for quality data!")
        
        start_time = time.time()
        while len(all_data) < target_count:
            # Check total job timeout
            if time.time() - start_time > settings.TOTAL_JOB_TIMEOUT:
                logger.warning(f"Total job timeout ({settings.TOTAL_JOB_TIMEOUT}s) reached")
                break
                
            try:
                # Use environment-aware timeout - MUCH longer for AI processing
                item = await asyncio.wait_for(data_queue.get(), timeout=queue_timeout)
                
                # Process item(s) - could be single item or batch
                if isinstance(item, list):
                    all_data.extend(item)
                    logger.info(f"Received batch of {len(item)} items")
                else:
                    all_data.append(item)
                
                consecutive_timeouts = 0  # Reset timeout counter
                
                if progress_callback:
                    await progress_callback({
                        "status": "collecting",
                        "total": target_count,
                        "collected": len(all_data),
                        "percentage": min((len(all_data) / target_count) * 100, 100),
                        "sources_active": not producer_task.done()
                    })
                    
            except asyncio.TimeoutError:
                consecutive_timeouts += 1
                logger.warning(f"Consumer timeout #{consecutive_timeouts}/{max_consecutive_timeouts}. Collected: {len(all_data)}/{target_count}")
                
                # Check if producers are still alive
                if producer_task.done():
                    logger.info("Producers finished. Breaking consumer loop.")
                    break
                    
                # More lenient timeout handling for cloud environments
                if consecutive_timeouts >= max_consecutive_timeouts:
                    logger.error(f"Maximum consecutive timeouts ({max_consecutive_timeouts}) reached. Breaking loop.")
                    # In production, we might want to continue with partial data
                    if settings.ENVIRONMENT == "production" and len(all_data) > target_count * 0.5:
                        logger.info(f"Production mode: Continuing with {len(all_data)} items (>{target_count*0.5} threshold)")
                        break
                    break
                    
                # Update progress even during timeout
                if progress_callback:
                    await progress_callback({
                        "status": "collecting",
                        "total": target_count,
                        "collected": len(all_data),
                        "percentage": (len(all_data) / target_count) * 100
                    })
        
        # Ensure producer tasks are cancelled to avoid them running forever
        producer_task.cancel()
        try:
            await producer_task
        except asyncio.CancelledError:
            print("Producers cancelled successfully.")

        # Final stats
        end_time = time.time()
        actual_time = (end_time - start_time) / 60  # minutes
        
        return {
            "data": all_data,
            "stats": {
                "total_collected": len(all_data),
                "actual_time_minutes": actual_time,
                "estimated_time_minutes": strategy["estimated_time_minutes"],
                "sources_used": {
                    "web": web_target,
                    "ai": ai_target
                },
                "strategy": strategy
            }
        }
    
    def _generate_query_variations(self, base_query: str, count: int) -> List[str]:
        """Generate comprehensive query variations for maximum coverage"""
        variations = {base_query}
        
        # Expanded modifiers for more variations
        prefix_modifiers = [
            "example", "sample", "real", "actual", "typical", "common", "frequent", 
            "recent", "latest", "best", "top", "popular", "effective", "practical",
            "professional", "expert", "advanced", "basic", "simple", "detailed"
        ]
        
        suffix_modifiers = [
            "guide", "tutorial", "examples", "samples", "cases", "methods", 
            "techniques", "strategies", "approaches", "tips", "advice", "solutions",
            "practices", "procedures", "steps", "instructions", "guidelines"
        ]
        
        # Language variations for Chinese tasks
        chinese_terms = ["中文", "中国", "汉语", "简体", "繁体"]
        
        # Generate variations
        while len(variations) < count and len(variations) < 200:  # Max 200 to avoid infinite loop
            # Add prefix modifiers
            if random.random() < 0.3:
                variations.add(f"{random.choice(prefix_modifiers)} {base_query}")
            
            # Add suffix modifiers  
            if random.random() < 0.3:
                variations.add(f"{base_query} {random.choice(suffix_modifiers)}")
            
            # Add both prefix and suffix
            if random.random() < 0.2:
                variations.add(f"{random.choice(prefix_modifiers)} {base_query} {random.choice(suffix_modifiers)}")
            
            # Add Chinese context for Chinese tasks
            if "中" in base_query or "chinese" in base_query.lower():
                if random.random() < 0.3:
                    variations.add(f"{base_query} {random.choice(chinese_terms)}")
            
            # Add quoted versions for exact matches
            if random.random() < 0.1:
                variations.add(f'"{base_query}"')
        
        result = list(variations)[:count]
        print(f"Generated {len(result)} query variations for: {base_query[:50]}...")
        return result
    
    async def _extract_training_samples_from_articles(self, articles: List[str], task_info: Dict) -> List[Dict]:
        """Batch process multiple articles for efficiency - cloud optimized!"""
        
        if not articles:
            return []
            
        # Process in smaller batches to avoid token limits
        batch_size = min(settings.BATCH_SIZE, len(articles))
        all_samples = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            try:
                batch_samples = await self._process_article_batch(batch, task_info)
                all_samples.extend(batch_samples)
                logger.info(f"Processed batch {i//batch_size + 1}, got {len(batch_samples)} samples")
            except Exception as e:
                logger.error(f"Batch processing failed: {e}, falling back to individual processing")
                # Fallback to individual processing
                for article in batch:
                    try:
                        individual_samples = await self._extract_training_samples_from_article(article, task_info)
                        all_samples.extend(individual_samples)
                    except Exception as individual_error:
                        logger.warning(f"Individual article processing failed: {individual_error}")
                        continue
        
        return all_samples
    
    async def _process_article_batch(self, articles: List[str], task_info: Dict) -> List[Dict]:
        """Process a batch of articles in a single AI call"""
        
        task_description = task_info.get('description', '')
        task_type = task_info.get('type', 'classification')
        labels = task_info.get('labels', [])
        
        # Combine articles with separators
        combined_content = "\n\n=== ARTICLE SEPARATOR ===\n\n".join(articles)
        
        # Limit content to avoid token limits
        max_chars = 8000 if settings.ENVIRONMENT == "production" else 4000
        if len(combined_content) > max_chars:
            combined_content = combined_content[:max_chars] + "\n\n[Content truncated due to length]"
        
        return await self._extract_training_samples_from_article(combined_content, task_info)
    
    async def _extract_training_samples_from_article(self, article_content: str, task_info: Dict) -> List[Dict]:
        """Smart article splitting using enhanced AI collector - supports full content!"""
        
        # 使用增强版AI收集器，支持长文章全文处理
        article_data = {
            'url': 'batch_processed',
            'content': article_content
        }
        
        try:
            # 使用增强版收集器处理整篇文章
            samples = await enhanced_ai_collector.collect_from_article(article_data, task_info)
            
            if samples:
                logger.info(f"🚀 Enhanced AI extracted {len(samples)} training samples from article")
                return samples
            else:
                logger.info("Enhanced AI found no relevant samples, trying fallback")
                
        except Exception as e:
            logger.error(f"Enhanced AI collection failed: {e}")
        
        # If enhanced collection fails, use simple paragraph splitting as backup
        logger.warning("Using fallback paragraph splitting")
        return self._simple_paragraph_split(article_content, task_info)
    
    async def _robust_openai_call(self, **kwargs):
        """SUPER ROBUST OpenAI API call - NEVER GIVES UP ON AI SPLITTING!"""
        max_retries = settings.MAX_RETRIES
        base_delay = settings.RETRY_DELAY_BASE
        
        logger.info(f"Starting robust OpenAI call with {max_retries} retries")
        
        for attempt in range(max_retries):
            try:
                # Use much longer timeout for AI processing
                timeout = kwargs.pop('timeout', settings.AI_PROCESSING_TIMEOUT)
                logger.info(f"Attempt {attempt + 1}/{max_retries} with {timeout}s timeout")
                
                async with asyncio.timeout(timeout):
                    response = await self.openai_client.chat.completions.create(**kwargs)
                    logger.info(f"OpenAI API success on attempt {attempt + 1}")
                    return response
                    
            except asyncio.TimeoutError:
                logger.warning(f"OpenAI API timeout ({timeout}s) on attempt {attempt + 1}/{max_retries}")
            except Exception as e:
                logger.warning(f"OpenAI API error on attempt {attempt + 1}/{max_retries}: {str(e)[:200]}")
            
            if attempt < max_retries - 1:
                # More aggressive retry with longer delays
                delay = min(base_delay * (attempt + 1) * 2, 60)  # 最多等60秒
                logger.info(f"Will retry in {delay} seconds... (AI splitting is important!)")
                await asyncio.sleep(delay)
        
        logger.error(f"OpenAI API failed after {max_retries} attempts with max timeout {settings.AI_PROCESSING_TIMEOUT}s")
        return None
    
    def _simple_paragraph_split(self, content: str, task_info: Dict) -> List[Dict]:
        """简单的段落拆分作为AI拆分的备用方案"""
        
        # 按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        training_samples = []
        for i, para in enumerate(paragraphs):
            # 过滤掉过短或过长的段落
            if 50 <= len(para) <= 800:
                training_samples.append({
                    'content': para,
                    'source': 'paragraph_split_from_web',
                    'original_url': 'from_article',
                    'extraction_method': 'simple_paragraph_split',
                    'sample_id': f"para_{i}",
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        print(f"📝 段落拆分获得 {len(training_samples)} 个样本")
        return training_samples 