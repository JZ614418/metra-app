"""
Optimized data collection service with parallel processing and batching
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
import time
from datetime import datetime
import aiohttp
import random

from app.core.config import settings
from app.services.data_collection import DataCollectionService
from app.services.data_generation import DataGenerationService


class OptimizedDataCollector:
    """Optimized data collection with smart batching and parallel processing"""
    
    def __init__(self):
        self.web_service = DataCollectionService()
        self.ai_service = DataGenerationService()
        
    async def calculate_optimal_strategy(self, 
                                       target_count: int,
                                       task_type: str,
                                       language: str) -> Dict[str, Any]:
        """Calculate optimal data collection strategy based on target count"""
        
        # Adjust strategy based on volume and language
        if target_count <= 1000:
            strategy = {"web_percentage": 0.9, "ai_percentage": 0.1, "batch_size": 100, "parallel_workers": 5, "estimated_time_minutes": 5}
        elif target_count <= 5000:
            strategy = {"web_percentage": 0.8, "ai_percentage": 0.2, "batch_size": 500, "parallel_workers": 8, "estimated_time_minutes": 20}
        elif target_count <= 20000:
            strategy = {"web_percentage": 0.6, "ai_percentage": 0.4, "batch_size": 1000, "parallel_workers": 10, "estimated_time_minutes": 60}
        else:
            strategy = {"web_percentage": 0.4, "ai_percentage": 0.6, "batch_size": 2000, "parallel_workers": 12, "estimated_time_minutes": target_count / 500}
        
        if language == "chinese":
            strategy["web_percentage"] *= 0.7
            strategy["ai_percentage"] = 1 - strategy["web_percentage"]
            strategy["estimated_time_minutes"] *= 1.2
        
        return strategy
    
    async def _web_producer(self, queue: asyncio.Queue, target_count: int, task_info: Dict, strategy: Dict):
        """Producer for web scraping with retries"""
        collected_count = 0
        base_query = f"{task_info.get('type', '')} {task_info.get('description', '')}"
        queries = self._generate_query_variations(base_query, min(int(target_count / 10), 10))
        
        retry_count = 0
        max_retries = 5
        
        while collected_count < target_count and retry_count < max_retries:
            try:
                # Try Google search first
                batch_data = await self.web_service.search_google(random.choice(queries), 10)
                
                # If Google fails, try Wikipedia
                if not batch_data:
                    batch_data = await self.web_service.search_wikipedia(random.choice(queries), 10)
                
                if batch_data:
                    for item in batch_data:
                        if collected_count < target_count:
                            await queue.put(item)
                            collected_count += 1
                        else:
                            break
                    retry_count = 0  # Reset retry count on success
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

        # Main consumer loop with improved timeout handling
        consecutive_timeouts = 0
        max_consecutive_timeouts = 3
        
        while len(all_data) < target_count:
            try:
                # Wait for an item from the queue, with a shorter timeout
                item = await asyncio.wait_for(data_queue.get(), timeout=10.0)
                all_data.append(item)
                consecutive_timeouts = 0  # Reset timeout counter
                
                if progress_callback:
                    await progress_callback({
                        "status": "collecting",
                        "total": target_count,
                        "collected": len(all_data),
                        "percentage": (len(all_data) / target_count) * 100
                    })
                    
            except asyncio.TimeoutError:
                consecutive_timeouts += 1
                print(f"Consumer timeout #{consecutive_timeouts}. Collected: {len(all_data)}/{target_count}")
                
                # Check if producers are still alive
                if producer_task.done():
                    print("Producers finished. Breaking consumer loop.")
                    break
                    
                # If too many consecutive timeouts, break to avoid infinite loop
                if consecutive_timeouts >= max_consecutive_timeouts:
                    print(f"Too many consecutive timeouts ({consecutive_timeouts}). Breaking.")
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
        """Generate query variations for better coverage"""
        variations = {base_query}
        
        modifiers = [
            "example", "sample", "real", "actual", "typical",
            "common", "frequent", "recent", "latest", "best"
        ]
        
        while len(variations) < count:
            variations.add(f"{random.choice(modifiers)} {base_query}")
            
        return list(variations) 