#!/usr/bin/env python3
"""
DataBuilderv3 + TogetherAI 真实数据收集
使用Google搜索API和ScrapingBee进行真实的网页抓取和数据提取
"""

import asyncio
import json
import time
import httpx
import requests
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from app.core.config import settings

class RealDataCollector:
    def __init__(self, together_api_key: str):
        self.together_api_key = together_api_key
        self.google_api_key = settings.GOOGLE_SEARCH_API_KEY
        self.google_cx = settings.GOOGLE_SEARCH_CX
        self.serper_api_key = settings.SERPER_API_KEY
        self.scrapingbee_api_key = settings.SCRAPINGBEE_API_KEY
        
        self.together_models = {
            "high_quality": "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
            "balanced": "mistralai/Mixtral-8x7B-Instruct-v0.1", 
            "fast": "meta-llama/Llama-3-8b-chat-hf"
        }
        
    async def call_together_ai(self, prompt: str, model_type: str = "balanced", max_tokens: int = 1500) -> str:
        """调用TogetherAI API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.together_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.together_models[model_type],
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.3
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"TogetherAI调用失败: {response.status_code} - {response.text}")

    def google_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """使用Google自定义搜索API"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cx,
                "q": query,
                "num": min(num_results, 10),  # Google API限制每次最多10个结果
                "lr": "lang_zh"  # 限制中文结果
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "google_custom_search"
                    })
                
                print(f"✅ Google搜索成功: 查询'{query}' 返回{len(results)}个结果")
                return results
            else:
                print(f"❌ Google搜索失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Google搜索异常: {str(e)}")
            return []

    def scrape_with_scrapingbee(self, url: str) -> Dict[str, Any]:
        """使用ScrapingBee抓取网页内容"""
        try:
            api_url = "https://app.scrapingbee.com/api/v1/"
            params = {
                "api_key": self.scrapingbee_api_key,
                "url": url,
                "render_js": False,  # 不渲染JavaScript，速度更快
                "premium_proxy": False,  # 不使用高级代理
                "country_code": "CN"  # 使用中国IP
            }
            
            response = requests.get(api_url, params=params, timeout=60)
            
            if response.status_code == 200:
                # 解析HTML内容
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 提取标题
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else ""
                
                # 移除脚本和样式标签
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # 提取主要内容
                content = ""
                
                # 尝试找到主要内容区域
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))
                
                if main_content:
                    content = main_content.get_text()
                else:
                    # 如果找不到主要内容区域，提取所有段落
                    paragraphs = soup.find_all(['p', 'div'], string=True)
                    content = '\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
                
                # 清理内容
                content = re.sub(r'\n+', '\n', content)
                content = re.sub(r'\s+', ' ', content)
                content = content.strip()
                
                result = {
                    "url": url,
                    "title": title,
                    "content": content,
                    "content_length": len(content),
                    "scrape_success": True,
                    "scrape_time": time.time()
                }
                
                print(f"✅ ScrapingBee抓取成功: {url} ({len(content)}字符)")
                return result
                
            else:
                print(f"❌ ScrapingBee抓取失败: {url} - {response.status_code}")
                return {"url": url, "scrape_success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ ScrapingBee抓取异常: {url} - {str(e)}")
            return {"url": url, "scrape_success": False, "error": str(e)}

    async def generate_search_queries(self, topic: str, num_queries: int = 20) -> List[str]:
        """使用TogetherAI生成搜索查询"""
        prompt = f"""
请为"{topic}"主题生成{num_queries}个多样化的中文搜索查询词。

要求：
1. 涵盖该主题的不同方面和子领域
2. 适合在搜索引擎中查找高质量内容
3. 避免商业化和广告相关词汇
4. 查询词要具体明确，不要过于宽泛

返回JSON数组格式，只包含搜索词：
["查询词1", "查询词2", "查询词3", ...]

只返回JSON数组，无其他内容。
"""
        
        response = await self.call_together_ai(prompt, "balanced", 800)
        
        # 提取JSON数组
        json_match = re.search(r'\[.*?\]', response, re.DOTALL)
        if json_match:
            try:
                queries = json.loads(json_match.group())
                print(f"✅ TogetherAI生成查询: {len(queries)}个")
                return queries[:num_queries]
            except json.JSONDecodeError:
                print("❌ 查询解析失败，使用备用查询")
                
        # 备用查询
        return [f"{topic} 介绍", f"{topic} 方法", f"{topic} 原理", f"{topic} 应用", f"{topic} 技巧"]

    async def extract_qa_samples(self, pages: List[Dict[str, Any]], topic: str, max_samples: int = 100) -> List[Dict[str, Any]]:
        """从网页内容中提取问答样本"""
        all_samples = []
        
        for i, page in enumerate(pages):
            if not page.get("scrape_success") or not page.get("content"):
                continue
                
            print(f"  处理页面 {i+1}/{len(pages)}: {page['title'][:30]}...")
            
            # 限制内容长度避免token超限
            content = page["content"][:3000]
            
            prompt = f"""
从以下{topic}相关文本中提取3-5个高质量的问答对：

文本内容：
{content}

要求：
1. 问题必须完整且以"？"结尾
2. 答案详细准确，不少于30字
3. 内容必须与{topic}相关
4. 问答要有价值，不能是无意义的重复

返回JSON数组格式：
[
  {{"question": "具体问题？", "answer": "详细答案"}},
  {{"question": "另一个问题？", "answer": "另一个答案"}}
]

只返回JSON数组。
"""
            
            try:
                response = await self.call_together_ai(prompt, "balanced", 1200)
                
                # 提取JSON
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    samples = json.loads(json_match.group())
                    
                    for sample in samples:
                        if isinstance(sample, dict) and "question" in sample and "answer" in sample:
                            # 质量检查
                            question = sample["question"].strip()
                            answer = sample["answer"].strip()
                            
                            if (len(question) >= 5 and len(answer) >= 20 and 
                                (question.endswith("？") or question.endswith("?"))):
                                
                                all_samples.append({
                                    "question": question,
                                    "answer": answer,
                                    "source_url": page["url"],
                                    "source_title": page["title"],
                                    "topic": topic,
                                    "extraction_time": time.time()
                                })
                    
                    print(f"    提取样本: {len(samples)}个")
                
            except Exception as e:
                print(f"    提取失败: {str(e)}")
                continue
            
            # 达到目标数量就停止
            if len(all_samples) >= max_samples:
                break
                
        return all_samples[:max_samples]

async def main():
    """主函数 - 执行真实数据收集"""
    print("🚀 DataBuilderv3 + TogetherAI 真实数据收集")
    print("使用Google搜索API + ScrapingBee + TogetherAI")
    print("=" * 60)
    
    # 配置参数
    together_api_key = "3264b6bc8217305992032fea30c74e5b97943b0e1243ccc5dced8b09cab5c208"
    topic = "中医药养生保健"
    target_samples = 50
    
    # 初始化收集器
    collector = RealDataCollector(together_api_key)
    
    start_time = time.time()
    
    try:
        # 步骤1: 生成搜索查询
        print(f"\n🔍 步骤1: 为'{topic}'生成搜索查询...")
        queries = await collector.generate_search_queries(topic, 15)
        
        # 步骤2: 执行Google搜索
        print(f"\n🌐 步骤2: 执行Google搜索...")
        all_search_results = []
        
        for i, query in enumerate(queries[:10]):  # 限制查询数量避免API配额
            print(f"  搜索 {i+1}/10: {query}")
            results = collector.google_search(query, num_results=5)
            all_search_results.extend(results)
            
            # 避免请求过快
            await asyncio.sleep(1)
        
        # 去重URL
        unique_urls = {}
        for result in all_search_results:
            url = result["link"]
            if url not in unique_urls:
                unique_urls[url] = result
        
        unique_results = list(unique_urls.values())
        print(f"  去重后页面: {len(unique_results)}个")
        
        # 步骤3: 使用ScrapingBee抓取内容
        print(f"\n📄 步骤3: 抓取页面内容...")
        scraped_pages = []
        
        for i, result in enumerate(unique_results[:20]):  # 限制抓取数量
            print(f"  抓取 {i+1}/20: {result['title'][:40]}...")
            page_data = collector.scrape_with_scrapingbee(result["link"])
            
            if page_data.get("scrape_success") and len(page_data.get("content", "")) > 200:
                page_data.update({
                    "search_title": result["title"],
                    "search_snippet": result["snippet"]
                })
                scraped_pages.append(page_data)
            
            # 避免请求过快
            await asyncio.sleep(2)
        
        print(f"  成功抓取: {len(scraped_pages)}个页面")
        
        # 步骤4: 使用TogetherAI提取问答样本
        print(f"\n🤖 步骤4: 提取训练样本...")
        samples = await collector.extract_qa_samples(scraped_pages, topic, target_samples)
        
        # 步骤5: 保存结果
        print(f"\n💾 步骤5: 保存数据...")
        
        final_data = {
            "collection_info": {
                "topic": topic,
                "collection_time": time.time(),
                "total_time": time.time() - start_time,
                "queries_generated": len(queries),
                "search_results": len(all_search_results),
                "unique_pages": len(unique_results),
                "scraped_pages": len(scraped_pages),
                "extracted_samples": len(samples)
            },
            "samples": samples,
            "queries_used": queries,
            "scraped_pages_summary": [
                {
                    "url": page["url"],
                    "title": page["title"],
                    "content_length": page["content_length"]
                } for page in scraped_pages
            ]
        }
        
        # 保存到文件
        output_file = "/Users/jz/Desktop/Metra/backend/real_collected_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        # 总结结果
        total_time = time.time() - start_time
        
        print(f"\n🎉 真实数据收集完成!")
        print("=" * 60)
        print(f"⏱️  总耗时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
        print(f"📊 收集统计:")
        print(f"   🔍 搜索查询: {len(queries)}个")
        print(f"   🌐 搜索结果: {len(all_search_results)}个")
        print(f"   📄 成功抓取: {len(scraped_pages)}个页面")
        print(f"   🤖 提取样本: {len(samples)}个")
        print(f"   ⚡ 处理速度: {len(samples)/(total_time/60):.1f} 样本/分钟")
        print(f"   💾 保存位置: {output_file}")
        
        # 显示样本示例
        print(f"\n📋 样本示例:")
        for i, sample in enumerate(samples[:3]):
            print(f"   {i+1}. Q: {sample['question']}")
            print(f"      A: {sample['answer'][:60]}...")
            print(f"      来源: {sample['source_title'][:40]}...")
            print()
        
        print(f"🎯 这是真实的数据收集，使用了:")
        print(f"   ✅ Google自定义搜索API - 真实网页搜索")
        print(f"   ✅ ScrapingBee API - 真实网页内容抓取") 
        print(f"   ✅ TogetherAI API - 真实AI内容提取")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 数据收集失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'🎊 任务圆满成功!' if success else '💥 任务执行失败!'}")