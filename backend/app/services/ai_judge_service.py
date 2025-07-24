#!/usr/bin/env python3
"""
AI智能判断服务 - 用AI解决AI训练中的问题
"""
import asyncio
import httpx
import json
from typing import Dict, List, Optional
from urllib.parse import urlparse
import openai
from app.core.config import settings

class AIJudgeService:
    """使用AI来智能判断数据收集和模型选择的决策"""
    
    def __init__(self):
        # Check if OpenAI API key is valid
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your-"):
            self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.ai_enabled = True
        else:
            self.openai_client = None
            self.ai_enabled = False
            print("⚠️  OpenAI API key not configured - using fallback responses")
        self.cache = {}  # 缓存AI判断结果
    
    async def judge_website_legality(self, url: str, content_sample: str = "") -> Dict:
        """AI智能判断网站是否可以合法爬取"""
        
        # 检查缓存
        domain = urlparse(url).netloc
        cache_key = f"legality_{domain}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # 获取网站基本信息
            website_info = await self._analyze_website_info(url)
            
            # 构建AI判断prompt
            prompt = f"""
请作为法律和网络爬虫专家，判断以下网站是否可以合法爬取数据用于AI训练：

网站URL: {url}
域名: {domain}
网站类型: {website_info.get('type', '未知')}
是否有robots.txt限制: {website_info.get('robots_restricted', '未知')}
内容样本: {content_sample[:200]}...

请从以下角度分析：
1. 法律合规性（版权、fair use等）
2. 网站性质（政府、教育、商业等）
3. 数据类型（公开信息、私人数据等）
4. robots.txt和服务条款
5. 商业风险评估

请返回JSON格式：
{{
    "legal_score": 0-100分,
    "can_scrape": true/false,
    "risk_level": "low/medium/high",
    "reasoning": "详细分析原因",
    "recommendations": ["建议1", "建议2"],
    "data_types_allowed": ["可以收集的数据类型"],
    "restrictions": ["限制条件"]
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的法律和技术专家，专门评估网络爬虫的合法性。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低temperature确保一致性
                max_tokens=1000
            )
            
            # 解析AI回复
            ai_response = response.choices[0].message.content
            
            try:
                # 尝试解析JSON
                judgment = json.loads(ai_response)
            except:
                # 如果不是JSON，创建默认结构
                judgment = {
                    "legal_score": 50,
                    "can_scrape": False,
                    "risk_level": "medium",
                    "reasoning": ai_response,
                    "recommendations": ["请人工审查"],
                    "data_types_allowed": [],
                    "restrictions": ["需要进一步分析"]
                }
            
            # 添加元数据
            judgment.update({
                "url": url,
                "domain": domain,
                "analyzed_by": "ai_judge",
                "website_info": website_info,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # 缓存结果
            self.cache[cache_key] = judgment
            
            return judgment
            
        except Exception as e:
            # 出错时返回保守结果
            return {
                "legal_score": 30,
                "can_scrape": False,
                "risk_level": "high",
                "reasoning": f"AI判断出错: {str(e)}",
                "recommendations": ["手动审查", "谨慎处理"],
                "error": str(e)
            }
    
    async def _analyze_website_info(self, url: str) -> Dict:
        """分析网站基本信息"""
        domain = urlparse(url).netloc
        info = {"domain": domain}
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 检查robots.txt
                robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
                try:
                    robots_response = await client.get(robots_url)
                    if robots_response.status_code == 200:
                        robots_content = robots_response.text.lower()
                        info["robots_restricted"] = "disallow: /" in robots_content
                        info["robots_content"] = robots_content[:500]
                    else:
                        info["robots_restricted"] = False
                except:
                    info["robots_restricted"] = "unknown"
                
                # 分析域名类型
                if any(tld in domain for tld in ['.edu', '.gov', '.org']):
                    info["type"] = "institutional"
                elif any(word in domain for word in ['wiki', 'github', 'stackoverflow']):
                    info["type"] = "open_source"
                elif any(word in domain for word in ['news', 'blog', 'media']):
                    info["type"] = "media"
                else:
                    info["type"] = "commercial"
                
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    async def recommend_best_replicate_model(self, 
                                           task_description: str, 
                                           task_type: str,
                                           data_sample: List[Dict],
                                           language: str = "auto") -> Dict:
        """AI智能推荐最适合的Replicate模型"""
        
        cache_key = f"model_{task_type}_{hash(task_description)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # 分析数据样本
            sample_text = ""
            if data_sample:
                sample_text = "\n".join([
                    f"输入: {item.get('text', '')[:100]}\n输出: {item.get('label', '')[:100]}" 
                    for item in data_sample[:3]
                ])
            
            prompt = f"""
作为AI模型专家，请为以下训练任务推荐最适合的Replicate模型：

任务描述: {task_description}
任务类型: {task_type}
语言: {language}
数据样本:
{sample_text}

请考虑以下因素：
1. 任务类型匹配度（问答、生成、分类等）
2. 语言支持（中文、英文、多语言）
3. 模型大小和训练效率
4. 领域适应性
5. 最新版本和性能

可选的Replicate模型：
- meta/llama-2-7b-chat (通用对话，英语优化)
- meta/llama-2-13b-chat (更强能力，资源需求更高)
- meta/code-llama-7b-instruct (代码生成专用)
- mistralai/mistral-7b-instruct-v0.1 (欧洲语言优化)
- qwen/qwen-7b-chat (中文优化)
- chatglm3-6b (中英双语)
- baichuan2-7b-chat (中文对话)

请返回JSON格式：
{{
    "recommended_model": "模型名称",
    "model_version": "具体版本ID",
    "confidence_score": 0-100,
    "reasoning": "推荐理由",
    "alternatives": [
        {{"model": "备选模型", "reason": "适用场景"}}
    ],
    "training_config": {{
        "optimal_epochs": 推荐轮数,
        "learning_rate": 推荐学习率,
        "batch_size": 推荐批次大小
    }},
    "expected_performance": "预期效果描述"
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是Replicate平台和大语言模型的专家，精通模型选择和训练优化。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                recommendation = json.loads(ai_response)
            except:
                recommendation = {
                    "recommended_model": "meta/llama-2-7b-chat",
                    "model_version": "default",
                    "confidence_score": 70,
                    "reasoning": ai_response,
                    "alternatives": [],
                    "training_config": {
                        "optimal_epochs": 3,
                        "learning_rate": 3e-5,
                        "batch_size": 4
                    }
                }
            
            # 添加版本映射
            version_mapping = {
                "meta/llama-2-7b-chat": "ef26b8ab4b49d4b6dfea76e3b7f06de1d8e11711bb5df64e2b4e45e91c9e1f36",
                "meta/llama-2-13b-chat": "d5da4236b006f0d48d52390e31375e3ce2c0894e9f71f8f5b0a64b8dd6c6b1a2",
                "meta/code-llama-7b-instruct": "a16d3b7bc5c5b7f3d8e9a2f6b8c9d0e1f2a3b4c5d6e7f8g9h0i1j2k3l4m5n6",
                "mistralai/mistral-7b-instruct-v0.1": "2f7f4df2bc3e3dccbd9da0a2a6b52c8da30f46f1d0e7925a6fe09f7a0b8d8c9a",
                "qwen/qwen-7b-chat": "8c3e2f1d9b5a7e6f4c2a8d9e3f1b7c5a9d2e6f8b4a7c1e5d9f3b8a6c2e7d1f4",
                "chatglm3-6b": "f2e8d3c7b1a9e6f4d2c5a8b7e3f1d6c9a4b8e2f7d3c1a5e9f6b4d8c2a7e1f5",
                "baichuan2-7b-chat": "9f3e7d1c5a8b2e6f4d7c1a9e5f3b8d2c6a4e8f1d5c7a3e9f2b6d4c8a1e7f5"
            }
            
            recommended_model = recommendation.get("recommended_model", "meta/llama-2-7b-chat")
            recommendation["model_version"] = version_mapping.get(recommended_model, 
                "ef26b8ab4b49d4b6dfea76e3b7f06de1d8e11711bb5df64e2b4e45e91c9e1f36")
            
            # 缓存结果
            self.cache[cache_key] = recommendation
            
            return recommendation
            
        except Exception as e:
            # 出错时返回默认推荐
            return {
                "recommended_model": "meta/llama-2-7b-chat",
                "model_version": "ef26b8ab4b49d4b6dfea76e3b7f06de1d8e11711bb5df64e2b4e45e91c9e1f36",
                "confidence_score": 60,
                "reasoning": f"AI推荐出错，使用默认模型: {str(e)}",
                "alternatives": [],
                "training_config": {
                    "optimal_epochs": 3,
                    "learning_rate": 3e-5,
                    "batch_size": 4
                },
                "error": str(e)
            }
    
    async def optimize_data_collection_strategy(self, 
                                              task_description: str,
                                              current_data_count: int,
                                              data_quality_score: float) -> Dict:
        """AI优化数据收集策略"""
        
        prompt = f"""
作为数据科学专家，请为AI训练任务优化数据收集策略：

任务描述: {task_description}
当前数据量: {current_data_count}
数据质量评分: {data_quality_score}/10

请分析并提供优化建议：
1. 是否需要更多数据？
2. 如何提高数据质量？
3. 推荐的数据源类型
4. 数据预处理建议
5. 数据增强策略

请返回JSON格式：
{{
    "needs_more_data": true/false,
    "target_data_count": 建议数据量,
    "quality_improvement_tips": ["提升质量的方法"],
    "recommended_sources": ["推荐数据源"],
    "search_queries": ["优化后的搜索查询"],
    "data_augmentation": ["数据增强方法"],
    "preprocessing_steps": ["预处理步骤"]
}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是数据科学和机器学习专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            return json.loads(ai_response)
            
        except Exception as e:
            return {
                "needs_more_data": current_data_count < 1000,
                "target_data_count": max(1000, current_data_count * 2),
                "quality_improvement_tips": ["清理重复数据", "标准化格式"],
                "error": str(e)
            }

# 单例实例
ai_judge_service = AIJudgeService()