"""
Data Collection Service
Integrates multiple data sources for Metra's Data Builder
"""

import httpx
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse, quote
from urllib.robotparser import RobotFileParser

from app.core.config import settings
from app.services.ai_judge_service import ai_judge_service


class DataCollectionService:
    """Unified data collection service"""
    
    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        self.google_cx_id = settings.GOOGLE_CX_ID
        self.serper_api_key = settings.SERPER_API_KEY
        self.scrapingbee_api_key = settings.SCRAPINGBEE_API_KEY
        
        # Legal sources whitelist (通用知识库 - 支持任何领域的数据收集)
        self.legal_sources = {
            # Educational and reference
            "wikipedia.org": {"license": "CC BY-SA", "can_scrape": True},
            "wikihow.com": {"license": "CC BY-NC-SA", "can_scrape": True},
            "wiktionary.org": {"license": "CC BY-SA", "can_scrape": True},
            "baike.baidu.com": {"license": "fair_use", "can_scrape": True},
            
            # Academic and research
            "pubmed.ncbi.nlm.nih.gov": {"license": "public_domain", "can_scrape": True},
            "arxiv.org": {"license": "various_open", "can_scrape": True},
            "scholar.google.com": {"license": "fair_use", "can_scrape": True},
            
            # Government and public data (Chinese and International)
            "cdc.gov": {"license": "public_domain", "can_scrape": True},
            "who.int": {"license": "public_domain", "can_scrape": True},
            "data.gov": {"license": "public_domain", "can_scrape": True},
            "gov.cn": {"license": "public_domain", "can_scrape": True},
            "nhc.gov.cn": {"license": "public_domain", "can_scrape": True},  # National Health Commission
            "satcm.gov.cn": {"license": "public_domain", "can_scrape": True},  # State Administration of TCM
            
            # Chinese Universities and Medical Institutions
            "edu.cn": {"license": "educational", "can_scrape": True},
            "beijing.edu.cn": {"license": "educational", "can_scrape": True},
            
            # 通用知识领域网站 (各行业通用)
            "hanspub.org": {"license": "academic", "can_scrape": True},  # 学术期刊
            "tech.sina.com.cn": {"license": "public_media", "can_scrape": True},  # 科技新闻
            "finance.sina.com.cn": {"license": "public_media", "can_scrape": True},  # 财经资讯
            "sports.sina.com.cn": {"license": "public_media", "can_scrape": True},  # 体育新闻
            "auto.sina.com.cn": {"license": "public_media", "can_scrape": True},  # 汽车资讯
            "cctv.com": {"license": "public_media", "can_scrape": True},
            "xinhuanet.com": {"license": "public_media", "can_scrape": True},
            "china.com.cn": {"license": "public_media", "can_scrape": True},
            "news.cn": {"license": "public_media", "can_scrape": True},
            "people.com.cn": {"license": "public_media", "can_scrape": True},
            "tsinghua.edu.cn": {"license": "educational", "can_scrape": True},
            "pku.edu.cn": {"license": "educational", "can_scrape": True},
            "mit.edu": {"license": "educational", "can_scrape": True},
            "stanford.edu": {"license": "educational", "can_scrape": True},
            "harvard.edu": {"license": "educational", "can_scrape": True},
            
            # 多领域知识网站
            "baike.so.com": {"license": "fair_use", "can_scrape": True},  # 360百科
            "hudong.com": {"license": "fair_use", "can_scrape": True},  # 互动百科
            "sciencenet.cn": {"license": "academic", "can_scrape": True},  # 科学网
            "cnki.net": {"license": "academic", "can_scrape": True},  # 中国知网
            "researchgate.net": {"license": "academic", "can_scrape": True},  # 学术网络
            "ieee.org": {"license": "academic", "can_scrape": True},  # IEEE
            "acm.org": {"license": "academic", "can_scrape": True},  # ACM
            
            # News and media (with restrictions)
            "reuters.com": {"license": "fair_use", "can_scrape": True, "limit": "snippets"},
            "bbc.com": {"license": "fair_use", "can_scrape": True, "limit": "snippets"},
            "npr.org": {"license": "fair_use", "can_scrape": True, "limit": "snippets"},
            "xinhuanet.com": {"license": "fair_use", "can_scrape": True, "limit": "snippets"},
            "people.com.cn": {"license": "fair_use", "can_scrape": True, "limit": "snippets"},
            
            # Technical documentation
            "stackoverflow.com": {"license": "CC BY-SA", "can_scrape": True},
            "github.com": {"license": "various", "can_scrape": True},
            "readthedocs.io": {"license": "various_open", "can_scrape": True},
            
            # E-commerce reviews (public data)
            "trustpilot.com": {"license": "public_reviews", "can_scrape": True},
            "yelp.com": {"license": "public_reviews", "can_scrape": True, "limit": "reviews_only"},
        }
        
        self.robots_cache = {}
    
    async def search_google(self, query: str, num_results: int = 10, lang: str = None) -> List[Dict]:
        """Search using Google Custom Search API with pagination support"""
        url = "https://www.googleapis.com/customsearch/v1"
        results = []
        
        # Calculate how many pages we need (Google returns max 10 per page)
        max_per_page = 10
        pages_needed = min((num_results + max_per_page - 1) // max_per_page, 10)  # Max 10 pages (100 results)
        
        async with httpx.AsyncClient() as client:
            for page in range(pages_needed):
                start_index = page * max_per_page + 1
                current_page_results = min(max_per_page, num_results - len(results))
                
                if current_page_results <= 0:
                    break
                
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_cx_id,
                    'q': query,
                    'num': current_page_results,
                    'start': start_index
                }
                
                if lang:
                    params['lr'] = f'lang_{lang}'
                
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    page_results = []
                    for item in data.get('items', []):
                        page_results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'url': item.get('link', ''),
                            'source': 'google_search'
                        })
                    
                    results.extend(page_results)
                    
                    # If we got fewer results than requested, we've reached the end
                    if len(page_results) < current_page_results:
                        break
                        
                    # Minimal delay for maximum speed
                    await asyncio.sleep(0.02)
                    
                except Exception as e:
                    print(f"Google search error for page {page + 1}: {e}")
                    # Continue with other pages even if one fails
                    continue
                    
        return results
    
    async def search_serper(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search using Serper API (simpler alternative to Google)"""
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        data = {
            'q': query,
            'num': num_results
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get('organic', []):
                    results.append({
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'url': item.get('link', ''),
                        'source': 'serper'
                    })
                return results
            except Exception as e:
                print(f"Serper search error: {e}")
                return []
    
    async def get_wikipedia_content(self, topic: str) -> Optional[Dict]:
        """Get content from Wikipedia API"""
        # Search for the page
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': topic,
            'srlimit': 1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Search for the topic
                response = await client.get(search_url, params=search_params)
                response.raise_for_status()
                data = response.json()
                
                if not data['query']['search']:
                    return None
                
                page_title = data['query']['search'][0]['title']
                
                # Get page content
                content_params = {
                    'action': 'query',
                    'format': 'json',
                    'prop': 'extracts',
                    'exintro': True,
                    'explaintext': True,
                    'titles': page_title
                }
                
                response = await client.get(search_url, params=content_params)
                response.raise_for_status()
                data = response.json()
                
                pages = data['query']['pages']
                for page_id, page_data in pages.items():
                    if 'extract' in page_data:
                        return {
                            'title': page_data['title'],
                            'content': page_data['extract'],
                            'url': f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
                            'source': 'wikipedia',
                            'license': 'CC BY-SA'
                        }
                
                return None
            except Exception as e:
                print(f"Wikipedia API error: {e}")
                return None
    
    async def get_arxiv_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search and get papers from arXiv"""
        url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # Parse XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                results = []
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns).text.strip()
                    summary = entry.find('atom:summary', ns).text.strip()
                    link = entry.find('atom:id', ns).text
                    
                    results.append({
                        'title': title,
                        'content': summary,
                        'url': link,
                        'source': 'arxiv',
                        'license': 'open_access'
                    })
                
                return results
            except Exception as e:
                print(f"arXiv API error: {e}")
                return []
    
    def check_legal_status(self, url: str) -> Dict:
        """Check if URL is legal to scrape"""
        domain = urlparse(url).netloc
        
        # Check whitelist
        for legal_domain, info in self.legal_sources.items():
            if legal_domain in domain:
                return {
                    'status': 'whitelisted',
                    'can_scrape': info.get('can_scrape', False),
                    'license': info.get('license', 'unknown')
                }
        
        # Check robots.txt
        if self.check_robots_txt(url):
            return {
                'status': 'robots_allowed',
                'can_scrape': True,
                'license': 'unknown'
            }
        
        return {
            'status': 'not_verified',
            'can_scrape': False,
            'license': 'unknown'
        }
    
    def check_robots_txt(self, url: str) -> bool:
        """Check robots.txt for permission"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            if robots_url in self.robots_cache:
                return self.robots_cache[robots_url]
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            allowed = rp.can_fetch("*", url)
            self.robots_cache[robots_url] = allowed
            
            return allowed
        except:
            return False
    
    async def scrape_with_scrapingbee(self, url: str) -> Optional[Dict]:
        """Scrape content using ScrapingBee (only for legal sources)"""
        # Check legal status first
        legal_status = self.check_legal_status(url)
        
        if not legal_status['can_scrape']:
            return None
        
        params = {
            'api_key': self.scrapingbee_api_key,
            'url': url,
            'render_js': 'false'  # Faster scraping without JS rendering
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    'https://app.scrapingbee.com/api/v1/',
                    params=params
                )
                
                if response.status_code == 200:
                    # Extract content from HTML
                    html_content = response.text
                    
                    # Simple content extraction (remove HTML tags)
                    import re
                    # Remove script and style elements
                    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                    
                    # Extract title
                    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                    title = title_match.group(1).strip() if title_match else ''
                    
                    # Extract text content (remove all HTML tags)
                    text_content = re.sub(r'<[^>]+>', ' ', html_content)
                    text_content = ' '.join(text_content.split())  # Normalize whitespace
                    
                    return {
                        'title': title[:200],  # Limit title length
                        'content': text_content[:8000],  # Increased content limit for better training
                        'snippet': text_content[:300],  # Short snippet for preview
                        'url': url,
                        'source': 'scrapingbee_enhanced',
                        'legal_status': legal_status,
                        'collected_at': datetime.utcnow().isoformat()
                    }
                else:
                    print(f"ScrapingBee HTTP error: {response.status_code}")
            except Exception as e:
                print(f"ScrapingBee error for {url}: {e}")
        
        return None
    
    async def _enhance_with_scrapingbee(self, item: Dict, url: str) -> Dict:
        """Helper function to enhance a single item with ScrapingBee"""
        try:
            enhanced_content = await self.scrape_with_scrapingbee(url)
            if enhanced_content:
                # Merge enhanced content with original item
                item.update({
                    'full_content': enhanced_content['content'],
                    'enhanced_title': enhanced_content['title'],
                    'enhanced_by': 'scrapingbee',
                    'enhanced_at': enhanced_content['collected_at'],
                    'enhanced': True
                })
                return item
            else:
                return {'enhanced': False, 'url': url, 'error': 'ScrapingBee failed'}
        except Exception as e:
            return {'enhanced': False, 'url': url, 'error': str(e)}
    
    async def collect_data_for_task(self, task_type: str, task_description: str, 
                                   data_requirements: Dict) -> Dict:
        """🤖 AI智能数据收集 - 基于任务需求智能收集数据"""
        
        # 🤖 使用AI优化数据收集策略
        try:
            ai_strategy = await ai_judge_service.optimize_data_collection_strategy(
                task_description=task_description,
                current_data_count=0,
                data_quality_score=5.0  # 初始分数
            )
            
            print(f"🤖 AI数据收集策略:")
            print(f"   目标数据量: {ai_strategy.get('target_data_count', 1000)}")
            print(f"   推荐数据源: {ai_strategy.get('recommended_sources', [])}")
            print(f"   优化搜索查询: {ai_strategy.get('search_queries', [])}")
            
            # 使用AI优化的搜索查询
            ai_queries = ai_strategy.get('search_queries', [])
            if ai_queries:
                queries = ai_queries[:10]  # 使用AI生成的查询
            else:
                queries = self._generate_search_queries(task_type, task_description)  # 备用方案
                
        except Exception as e:
            print(f"🤖 AI策略生成失败，使用传统方法: {e}")
            queries = self._generate_search_queries(task_type, task_description)
        
        all_data = []
        stats = {
            'total_collected': 0,
            'by_source': {},
            'with_full_content': 0
        }
        
        # Phase 1: Quick search collection
        for query in queries[:5]:  # Limit initial queries
            # Try multiple search engines
            google_results = await self.search_google(query)
            serper_results = await self.search_serper(query)
            
            all_data.extend(google_results)
            all_data.extend(serper_results)
            
            stats['by_source']['google'] = len(google_results)
            stats['by_source']['serper'] = len(serper_results)
        
        # Phase 2: Enrich with full content from legal sources
        enriched_data = []
        for item in all_data[:20]:  # Limit to avoid too many requests
            url = item.get('url', '')
            
            # Try to get full content if legal
            if 'wikipedia.org' in url:
                # Extract topic from URL
                topic = url.split('/wiki/')[-1].replace('_', ' ')
                wiki_content = await self.get_wikipedia_content(topic)
                if wiki_content:
                    item.update(wiki_content)
                    stats['with_full_content'] += 1
            
            enriched_data.append(item)
            await asyncio.sleep(0.05)  # Reduced rate limiting
        
        # Phase 3: Add specialized sources if needed
        if 'academic' in task_type.lower() or 'research' in task_description.lower():
            arxiv_results = await self.get_arxiv_papers(queries[0])
            enriched_data.extend(arxiv_results)
            stats['by_source']['arxiv'] = len(arxiv_results)
        
        stats['total_collected'] = len(enriched_data)
        
        return {
            'data': enriched_data,
            'stats': stats,
            'queries_used': queries
        }
    
    def _generate_search_queries(self, task_type: str, description: str) -> List[str]:
        """智能生成基于任务类型的搜索查询 - 支持任何领域"""
        queries = []
        
        # 基础查询
        base_terms = description.lower().split()[:5]
        queries.append(' '.join(base_terms))
        
        # 通用任务类型查询生成
        if 'sentiment' in task_type.lower() or 'emotion' in task_type.lower():
            queries.extend([
                f"{description} positive reviews",
                f"{description} negative feedback", 
                f"{description} customer opinions",
                f"{description} sentiment analysis examples"
            ])
        elif 'classification' in task_type.lower():
            queries.extend([
                f"{description} examples",
                f"{description} categories types",
                f"{description} classification",
                f"{description} machine learning dataset"
            ])
        elif 'qa' in task_type.lower() or 'question' in task_type.lower():
            queries.extend([
                f"{description} frequently asked questions",
                f"{description} Q&A",
                f"{description} common questions answers",
                f"{description} interview questions"
            ])
        elif 'generation' in task_type.lower() or 'text' in task_type.lower():
            queries.extend([
                f"{description} examples",
                f"{description} templates",
                f"{description} writing samples",
                f"{description} content generation"
            ])
        elif 'translation' in task_type.lower():
            queries.extend([
                f"{description} translation examples",
                f"{description} bilingual text",
                f"{description} parallel corpus"
            ])
        elif 'summarization' in task_type.lower():
            queries.extend([
                f"{description} summary examples",
                f"{description} article summaries",
                f"{description} text summarization"
            ])
        elif 'code' in task_type.lower() or 'programming' in task_type.lower():
            queries.extend([
                f"{description} code examples",
                f"{description} programming tutorial",
                f"{description} coding problems",
                f"{description} software development"
            ])
        else:
            # 通用fallback查询
            queries.extend([
                f"{description} tutorial",
                f"{description} guide",
                f"{description} examples",
                f"{description} best practices"
            ])
        
        return queries[:10]  # Limit number of queries
    
    async def search_wikipedia(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search Wikipedia"""
        result = await self.get_wikipedia_content(query)
        if result:
            return [result]
        return []
    
    async def search_arxiv(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search arXiv papers"""
        return await self.get_arxiv_papers(query, num_results)
    
    async def search_pubmed(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search PubMed (placeholder for now)"""
        # TODO: Implement PubMed API
        return []
    
    async def _is_whitelisted(self, url: str) -> bool:
        """AI智能判断URL是否可以合法爬取"""
        domain = urlparse(url).netloc
        
        # 1. 快速检查预定义白名单
        for legal_domain in self.legal_sources:
            if legal_domain in domain:
                return True
        
        # 2. AI智能判断 - 这是关键创新！
        try:
            ai_judgment = await ai_judge_service.judge_website_legality(url)
            
            # AI评分系统：70分以上认为可以爬取
            if ai_judgment.get('legal_score', 0) >= 70 and ai_judgment.get('can_scrape', False):
                print(f"🤖 AI判断允许爬取: {url[:50]}... (评分: {ai_judgment['legal_score']})")
                print(f"   理由: {ai_judgment.get('reasoning', '')[:100]}...")
                return True
            elif ai_judgment.get('legal_score', 0) >= 50:
                print(f"⚠️  AI建议谨慎爬取: {url[:50]}... (评分: {ai_judgment['legal_score']})")
                # 中等评分的网站，检查具体建议
                if 'public' in ai_judgment.get('reasoning', '').lower():
                    return True
        except Exception as e:
            print(f"🤖 AI判断出错，使用传统方法: {e}")
        
        # 3. 传统判断作为备用
        if await self._check_robots_permission(url):
            return True
            
        if await self._auto_detect_legal_domain(domain):
            return True
            
        return False
    
    async def _check_robots_permission(self, url: str) -> bool:
        """异步检查robots.txt权限"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(robots_url)
                if response.status_code == 200:
                    robots_content = response.text.lower()
                    # 简单检查是否允许爬取
                    if "disallow: /" not in robots_content or "allow: /" in robots_content:
                        return True
        except:
            pass
        return False
    
    async def _auto_detect_legal_domain(self, domain: str) -> bool:
        """自动检测域名是否为合法可爬取类型"""
        legal_indicators = [
            # 政府网站
            '.gov', '.gov.cn', '.org.cn', 
            # 教育机构
            '.edu', '.edu.cn', '.ac.cn',
            # 开放数据
            'wikipedia', 'wikidata', 'wikimedia',
            # 学术期刊
            'arxiv', 'pubmed', 'scholar',
            # 开源社区
            'github', 'gitlab', 'stackoverflow',
            # 新闻媒体（公共信息）
            'news', 'xinhua', 'people', 'cctv',
            # 医疗健康（公共信息）
            'health', 'medical', 'medicine'
        ]
        
        domain_lower = domain.lower()
        for indicator in legal_indicators:
            if indicator in domain_lower:
                return True
        
        return False
    
    async def scrape_full_content(self, url: str) -> Optional[str]:
        """Scrape full content from URL if legal"""
        result = await self.scrape_with_scrapingbee(url)
        if result:
            return result.get('content', '')
        return None
    
    async def collect_from_multiple_sources(
        self,
        query: str,
        sources: List[str] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """Collect data from multiple sources in parallel"""
        
        if sources is None:
            sources = ['google', 'serper', 'wikipedia']
        
        # Collect from all sources in parallel
        tasks = []
        for source in sources:
            if source == 'google' and self.google_api_key:
                tasks.append(self.search_google(query, max_results // len(sources)))
            elif source == 'serper' and self.serper_api_key:
                tasks.append(self.search_serper(query, max_results // len(sources)))
            elif source == 'wikipedia':
                tasks.append(self.search_wikipedia(query, max_results // len(sources)))
            elif source == 'arxiv':
                tasks.append(self.search_arxiv(query, max_results // len(sources)))
            elif source == 'pubmed':
                tasks.append(self.search_pubmed(query, max_results // len(sources)))
        
        # Wait for all searches to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_data = []
        for result in results:
            if isinstance(result, list):
                all_data.extend(result)
            elif isinstance(result, Exception):
                print(f"Error in source: {result}")
        
        return all_data[:max_results]
    
    async def collect_web_data(
        self,
        query: str = None,
        urls: List[str] = None,
        max_results: int = 100,
        include_full_content: bool = False,
        sources: List[str] = None
    ) -> List[Dict]:
        """Main entry point for web data collection"""
        
        all_data = []
        
        # If specific URLs provided, scrape them
        if urls:
            for url in urls[:max_results]:
                if await self._is_whitelisted(url):
                    content = await self.scrape_full_content(url)
                    if content:
                        all_data.append({
                            'content': content,
                            'source': url,
                            'type': 'full_page',
                            'timestamp': datetime.utcnow().isoformat()
                        })
        
        # If query provided, search multiple sources
        elif query:
            search_results = await self.collect_from_multiple_sources(
                query, sources, max_results
            )
            
            # Aggressive ScrapingBee integration for maximum data quality
            enhanced_count = 0
            max_enhancements = min(len(search_results), 200)  # Process up to 200 URLs
            
            print(f"Starting ScrapingBee enhancement for {len(search_results)} results (max {max_enhancements})...")
            
            # Large batch processing for maximum speed
            batch_size = 25  # Increased to 25 concurrent requests
            for i in range(0, len(search_results), batch_size):
                batch = search_results[i:i+batch_size]
                enhancement_tasks = []
                
                for item in batch:
                    if enhanced_count >= max_enhancements:
                        break
                        
                    url = item.get('url', '')
                    
                    # Skip if already has substantial content (increased threshold)
                    if 'full_content' in item or ('content' in item and len(item['content']) > 500):
                        continue
                    
                    # Try to enhance with ScrapingBee if whitelisted
                    if await self._is_whitelisted(url):
                        enhancement_tasks.append(self._enhance_with_scrapingbee(item, url))
                        enhanced_count += 1
                
                # Process batch concurrently
                if enhancement_tasks:
                    enhanced_items = await asyncio.gather(*enhancement_tasks, return_exceptions=True)
                    for enhanced in enhanced_items:
                        if isinstance(enhanced, dict) and enhanced.get('enhanced'):
                            print(f"✓ Enhanced: {enhanced['url'][:50]}...")
                        elif isinstance(enhanced, Exception):
                            print(f"✗ Enhancement failed: {enhanced}")
                    
                    # Minimal rate limiting for maximum speed
                    await asyncio.sleep(0.05)  # Reduced to 0.05 seconds
                
                if enhanced_count >= max_enhancements:
                    break
            
            print(f"ScrapingBee enhancement complete: {enhanced_count} URLs processed")
            
            all_data.extend(search_results)
        
        # Add consistent structure
        for i, item in enumerate(all_data):
            if 'id' not in item:
                item['id'] = f"data_{i}"
            if 'timestamp' not in item:
                item['timestamp'] = datetime.utcnow().isoformat()
            if 'content' not in item and 'snippet' in item:
                item['content'] = item['snippet']
            
            # Merge full content into main content if available
            if 'full_content' in item:
                item['content'] = item['full_content'][:2000]  # Limit for display
                item['has_full_content'] = True
        
        return all_data


# Singleton instance
data_collection_service = DataCollectionService() 