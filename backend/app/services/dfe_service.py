"""
DFE (Data Fusion Engine) Core Service
Handles the logic for cleaning, fetching full content, and refining data.
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import logging

import httpx
from trafilatura import fetch_url, extract
from bs4 import BeautifulSoup
import pandas as pd
from openai import AsyncOpenAI

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class DFEService:
    """Data Fusion Engine Service - 数据融合引擎服务"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def start_extraction(self, task_id: str, urls: List[str], options: Optional[Dict] = None) -> Dict:
        """
        启动数据提取任务
        
        Args:
            task_id: 任务ID
            urls: 要抓取的URL列表
            options: 提取选项（V2功能配置）
        """
        # 创建任务记录
        task = {
            "id": task_id,
            "status": "processing",
            "progress": 0,
            "total": len(urls),
            "results": [],
            "options": options or {},
            "created_at": datetime.utcnow().isoformat(),
            "error": None
        }
        self.tasks[task_id] = task
        
        # 异步执行提取任务
        asyncio.create_task(self._process_extraction(task_id, urls, options))
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": f"Started processing {len(urls)} URLs"
        }
    
    async def _process_extraction(self, task_id: str, urls: List[str], options: Optional[Dict] = None):
        """异步处理数据提取"""
        task = self.tasks[task_id]
        
        try:
            # V1: 基础网页抓取
            extracted_data = await self._extract_content_from_urls(task_id, urls)
            task["results"] = extracted_data
            
            # V2: 高级数据处理（如果启用）
            if options and options.get("enable_v2_features", False):
                task["results"] = await self._apply_v2_features(extracted_data, options)
            
            task["status"] = "completed"
            task["progress"] = 100
            
        except Exception as e:
            logger.error(f"Error in task {task_id}: {str(e)}")
            task["status"] = "failed"
            task["error"] = str(e)
    
    async def _extract_content_from_urls(self, task_id: str, urls: List[str]) -> List[Dict]:
        """V1: 基础网页内容提取"""
        results = []
        task = self.tasks[task_id]
        
        # 允许自动跟随重定向
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for i, url in enumerate(urls):
                try:
                    # 更新进度
                    task["progress"] = int((i / len(urls)) * 100)
                    
                    # 抓取网页内容
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    # 使用trafilatura提取主要内容
                    main_content = extract(response.text, include_comments=False, include_tables=True)
                    
                    # 使用BeautifulSoup提取额外信息
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title = soup.find('title').text if soup.find('title') else ""
                    meta_description = ""
                    if soup.find('meta', {'name': 'description'}):
                        meta_description = soup.find('meta', {'name': 'description'}).get('content', '')
                    
                    # 提取所有文本（备用）
                    all_text = soup.get_text(separator=' ', strip=True)[:5000]  # 限制长度
                    
                    result = {
                        "url": url,
                        "title": title,
                        "meta_description": meta_description,
                        "main_content": main_content or all_text,
                        "extracted_at": datetime.utcnow().isoformat(),
                        "success": True
                    }
                    
                except Exception as e:
                    logger.error(f"Error extracting {url}: {str(e)}")
                    result = {
                        "url": url,
                        "error": str(e),
                        "success": False
                    }
                
                results.append(result)
        
        return results
    
    async def _apply_v2_features(self, data: List[Dict], options: Dict) -> List[Dict]:
        """V2: 高级数据处理功能"""
        processed_data = data.copy()
        
        # 1. 字段对齐
        if options.get("field_alignment"):
            processed_data = await self._align_fields(processed_data, options["field_alignment"])
        
        # 2. 缺失值填充
        if options.get("fill_missing_values"):
            processed_data = await self._fill_missing_values(processed_data)
        
        # 3. 数据增强
        if options.get("data_augmentation"):
            processed_data = await self._augment_data(processed_data)
        
        # 4. 格式转换
        if options.get("output_format"):
            processed_data = self._convert_format(processed_data, options["output_format"])
        
        return processed_data
    
    async def _align_fields(self, data: List[Dict], field_mapping: Dict) -> List[Dict]:
        """字段对齐 - 自动映射同义词字段"""
        aligned_data = []
        
        for item in data:
            aligned_item = {}
            
            for target_field, source_fields in field_mapping.items():
                # 查找匹配的源字段
                for source_field in source_fields:
                    if source_field in item and item[source_field]:
                        aligned_item[target_field] = item[source_field]
                        break
                else:
                    # 如果没找到，使用AI生成
                    if item.get("main_content"):
                        aligned_item[target_field] = await self._extract_field_with_ai(
                            item["main_content"], 
                            target_field
                        )
            
            # 保留原始数据
            aligned_item["_original"] = item
            aligned_data.append(aligned_item)
        
        return aligned_data
    
    async def _fill_missing_values(self, data: List[Dict]) -> List[Dict]:
        """使用AI填充缺失值"""
        filled_data = []
        
        for item in data:
            filled_item = item.copy()
            
            # 检查每个字段
            for key, value in item.items():
                if not value or value == "":
                    # 使用AI基于上下文生成缺失值
                    context = {k: v for k, v in item.items() if v and k != key}
                    filled_value = await self._generate_missing_value(key, context)
                    filled_item[key] = filled_value
            
            filled_data.append(filled_item)
        
        return filled_data
    
    async def _augment_data(self, data: List[Dict]) -> List[Dict]:
        """数据增强 - 生成相似样本"""
        augmented_data = data.copy()
        
        for item in data:
            if item.get("main_content"):
                # 生成相似内容
                similar_content = await self._generate_similar_content(item["main_content"])
                augmented_item = item.copy()
                augmented_item["main_content"] = similar_content
                augmented_item["is_augmented"] = True
                augmented_data.append(augmented_item)
        
        return augmented_data
    
    def _convert_format(self, data: List[Dict], format_type: str) -> List[Dict]:
        """格式转换"""
        if format_type == "jsonl":
            # 转换为JSONL格式（每行一个JSON对象）
            return [{"text": json.dumps(item, ensure_ascii=False)} for item in data]
        elif format_type == "csv":
            # 扁平化数据结构
            flattened = []
            for item in data:
                flat_item = self._flatten_dict(item)
                flattened.append(flat_item)
            return flattened
        else:
            return data
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """递归扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    async def _extract_field_with_ai(self, content: str, field_name: str) -> str:
        """使用AI从内容中提取特定字段"""
        try:
            prompt = f"""
            从以下内容中提取 {field_name} 信息：
            
            内容：{content[:2000]}
            
            如果找不到相关信息，返回"未找到"。
            只返回提取的信息，不要加其他说明。
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI extraction error: {str(e)}")
            return ""
    
    async def _generate_missing_value(self, field_name: str, context: Dict) -> str:
        """基于上下文生成缺失值"""
        try:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)[:1000]
            
            prompt = f"""
            基于以下上下文，生成 {field_name} 字段的合理值：
            
            上下文：
            {context_str}
            
            生成一个简短、合理的值。如果无法推断，返回"N/A"。
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
            return "N/A"
    
    async def _generate_similar_content(self, original_content: str) -> str:
        """生成相似内容用于数据增强"""
        try:
            prompt = f"""
            基于以下内容，生成一个相似但不完全相同的版本（保持主题和关键信息不变）：
            
            原始内容：{original_content[:1500]}
            
            要求：
            1. 保持相同的主题和核心信息
            2. 改变表达方式和句子结构
            3. 可以添加合理的细节
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI augmentation error: {str(e)}")
            return original_content
    
    async def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        task = self.tasks[task_id]
        return {
            "id": task["id"],
            "status": task["status"],
            "progress": task["progress"],
            "total": task["total"],
            "created_at": task["created_at"],
            "error": task.get("error")
        }
    
    async def get_task_results(self, task_id: str) -> Dict:
        """获取任务结果"""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        task = self.tasks[task_id]
        if task["status"] != "completed":
            return {
                "error": f"Task is {task['status']}, not completed",
                "status": task["status"]
            }
        
        return {
            "id": task["id"],
            "status": task["status"],
            "results": task["results"],
            "total": len(task["results"]),
            "options": task.get("options", {})
        }

# 创建全局服务实例
dfe_service = DFEService() 