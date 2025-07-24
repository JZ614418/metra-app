"""
PageScraper - 并发网页抓取器
基于SearchQuery高并发抓取网页内容，支持动态并发调整
"""

import asyncio
import aiohttp
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup

from app.services.data_builder_v3.config import config
from app.services.data_builder_v3.query_generator import SearchQuery

logger = logging.getLogger(__name__)

@dataclass
class ScrapedPage:
    """抓取的页面数据"""
    url: str
    title: str
    content: str
    source_domain: str
    scrape_time: float
    content_length: int
    quality_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # 计算基础质量分数
        self.quality_score = self._calculate_quality_score()
    
    def _calculate_quality_score(self) -> float:
        """计算页面质量分数"""
        score = 0.0
        
        # 内容长度评分 (40%)
        if self.content_length > 2000:
            score += 0.4
        elif self.content_length > 1000:
            score += 0.3
        elif self.content_length > 500:
            score += 0.2
        
        # 标题质量评分 (20%)
        if self.title and len(self.title.strip()) > 10:
            score += 0.2
        
        # 来源可信度评分 (20%)
        trusted_indicators = ['.gov', '.edu', '.org', 'wikipedia', 'baidu', 'zhihu']
        if any(indicator in self.source_domain for indicator in trusted_indicators):
            score += 0.2
        
        # 内容质量评分 (20%)
        if self.content:
            # 检查是否包含垃圾内容
            spam_indicators = ['广告', '购买', '淘宝', '价格', '联系电话']
            spam_count = sum(1 for indicator in spam_indicators if indicator in self.content)
            if spam_count < 2:
                score += 0.2
        
        return min(score, 1.0)

class PageScraper:
    """并发网页抓取器"""
    
    def __init__(self):
        self.session = None
        # 提升初始并发数
        self.current_concurrency = max(config.concurrency.initial_max_requests, 20)  # 至少20个并发
        self.success_count = 0
        self.failure_count = 0
        self.start_time = time.time()
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 增加连接限制以支持更高并发
        connector = aiohttp.TCPConnector(
            limit=self.current_concurrency * 3,  # 增加总连接数
            limit_per_host=100,  # 每个主机的连接数
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True,  # 自动清理关闭的连接
            force_close=True  # 强制关闭连接以释放资源
        )
        
        # 优化超时设置
        timeout = aiohttp.ClientTimeout(
            total=config.concurrency.request_timeout,
            connect=10,
            sock_read=20
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def scrape_search_results(self, queries: List[SearchQuery]) -> List[ScrapedPage]:
        """
        基于搜索查询批量抓取页面
        
        Args:
            queries: 搜索查询列表
            
        Returns:
            List[ScrapedPage]: 抓取的页面列表
        """
        logger.info(f"🕷️ 开始抓取: {len(queries)}个查询, 并发数: {self.current_concurrency}")
        
        # 获取搜索结果URL
        all_urls = []
        for query in queries:
            urls = await self._get_search_urls(query)
            all_urls.extend(urls)
        
        # 去重URL
        unique_urls = list(set(all_urls))
        logger.info(f"📋 获取到 {len(unique_urls)} 个唯一URL")
        
        # 并发抓取所有URL
        scraped_pages = []
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(self.current_concurrency)
        
        # 优化：一次性创建所有任务而不是分批
        all_tasks = []
        for url in unique_urls:
            task = self._scrape_single_page(url, semaphore)
            all_tasks.append(task)
        
        # 使用as_completed来实时处理完成的任务
        completed = 0
        for future in asyncio.as_completed(all_tasks):
            try:
                result = await future
                if isinstance(result, ScrapedPage):
                    scraped_pages.append(result)
                    self.success_count += 1
                else:
                    self.failure_count += 1
                
                completed += 1
                # 每处理10个URL打印一次进度
                if completed % 10 == 0:
                    logger.info(f"抓取进度: {completed}/{len(unique_urls)} ({completed/len(unique_urls)*100:.1f}%)")
                    
            except Exception as e:
                self.failure_count += 1
                logger.debug(f"抓取失败: {str(e)}")
            
            # 动态调整并发数
            if completed % self.current_concurrency == 0:
                await self._adjust_concurrency()
        
        # 按质量分数排序
        scraped_pages.sort(key=lambda x: x.quality_score, reverse=True)
        
        logger.info(f"✅ 抓取完成: {len(scraped_pages)}个页面, 成功率: {self._get_success_rate():.1%}")
        return scraped_pages
    
    async def _get_search_urls(self, query: SearchQuery) -> List[str]:
        """获取搜索结果URL - 支持多搜索引擎"""
        all_urls = []
        
        # 🔧 新增：支持多个搜索引擎（基于配置）
        enabled_engines = config.search_engines.enabled_engines
        search_engine_map = {
            "baidu": self._search_baidu,
            "google": self._search_google,
            "duckduckgo": self._search_duckduckgo
        }
        
        search_engines = [
            (engine_name, search_engine_map[engine_name])
            for engine_name in enabled_engines
            if engine_name in search_engine_map
        ]
        
        for engine_name, search_func in search_engines:
            try:
                urls = await search_func(query)
                if urls:
                    logger.info(f"✅ {engine_name}搜索获取到 {len(urls)} 个URL")
                    all_urls.extend(urls)
                else:
                    logger.warning(f"⚠️ {engine_name}搜索未获取到结果")
            except Exception as e:
                logger.error(f"❌ {engine_name}搜索失败: {str(e)}")
                continue
        
        # 去重并限制数量
        unique_urls = list(dict.fromkeys(all_urls))  # 保持顺序的去重
        return unique_urls[:20]  # 增加URL数量限制
    
    async def _search_baidu(self, query: SearchQuery) -> List[str]:
        """百度搜索 - 优化版本"""
        try:
            # 改进搜索URL，增加更多参数
            search_url = f"https://www.baidu.com/s?wd={query.to_search_string()}&rn=20&ie=utf-8"
            
            # 使用更完整的请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
            
            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    urls = self._parse_baidu_results(html)
                    if urls:
                        logger.info(f"✅ 百度搜索获取到 {len(urls)} 个URL")
                    else:
                        logger.warning(f"⚠️ 百度搜索未获取到结果")
                    return urls
                else:
                    logger.warning(f"百度搜索请求失败: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"百度搜索失败: {str(e)}")
            return []
    
    async def _search_google(self, query: SearchQuery) -> List[str]:
        """Google搜索 (使用Custom Search API或爬虫)"""
        try:
            # 方法1: 使用Google Custom Search API (需要API密钥)
            google_api_key = config.search_engines.google_search_api_key
            google_cx = config.search_engines.google_search_cx
            
            if google_api_key and google_cx:
                return await self._search_google_api(query, google_api_key, google_cx)
            else:
                # 方法2: 直接爬取Google搜索结果页面
                return await self._search_google_scrape(query)
                
        except Exception as e:
            logger.error(f"Google搜索失败: {str(e)}")
            return []
    
    async def _search_google_api(self, query: SearchQuery, api_key: str, cx: str) -> List[str]:
        """使用Google Custom Search API"""
        try:
            search_url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': query.to_search_string(),
                'num': 10
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    urls = []
                    for item in data.get('items', []):
                        if 'link' in item:
                            urls.append(item['link'])
                    return urls
                else:
                    logger.warning(f"Google API请求失败: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Google API搜索失败: {str(e)}")
            return []
    
    async def _search_google_scrape(self, query: SearchQuery) -> List[str]:
        """直接爬取Google搜索结果"""
        try:
            search_url = f"https://www.google.com/search?q={query.to_search_string()}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_google_results(html)
                else:
                    logger.warning(f"Google爬取请求失败: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Google爬取失败: {str(e)}")
            return []
    
    async def _search_duckduckgo(self, query: SearchQuery) -> List[str]:
        """DuckDuckGo搜索"""
        try:
            search_url = f"https://duckduckgo.com/html/?q={query.to_search_string()}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_duckduckgo_results(html)
                else:
                    logger.warning(f"DuckDuckGo请求失败: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"DuckDuckGo搜索失败: {str(e)}")
            return []
    
    def _parse_baidu_results(self, html: str) -> List[str]:
        """解析百度搜索结果页面获取URL"""
        urls = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 百度搜索结果链接提取
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and 'baidu.com' not in href:
                    urls.append(href)
                elif href.startswith('/link?url='):
                    # 百度跳转链接处理
                    real_url = self._decode_baidu_url(href)
                    if real_url:
                        urls.append(real_url)
        
        except Exception as e:
            logger.error(f"解析百度搜索结果失败: {str(e)}")
        
        return urls[:10]  # 限制每个查询的URL数量
    
    def _parse_google_results(self, html: str) -> List[str]:
        """解析Google搜索结果页面获取URL"""
        urls = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Google搜索结果链接提取
            # Google的结构: <a href="/url?q=REAL_URL&...">
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/url?q='):
                    real_url = self._decode_google_url(href)
                    if real_url:
                        urls.append(real_url)
                elif href.startswith('http') and 'google.com' not in href:
                    urls.append(href)
        
        except Exception as e:
            logger.error(f"解析Google搜索结果失败: {str(e)}")
        
        return urls[:10]
    
    def _parse_duckduckgo_results(self, html: str) -> List[str]:
        """解析DuckDuckGo搜索结果页面获取URL"""
        urls = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # DuckDuckGo搜索结果链接提取
            # DuckDuckGo的结构: <a class="result__a" href="REAL_URL">
            for link in soup.find_all('a', class_='result__a', href=True):
                href = link['href']
                if href.startswith('http'):
                    urls.append(href)
            
            # 备选方法：查找所有外部链接
            if not urls:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') and 'duckduckgo.com' not in href:
                        urls.append(href)
        
        except Exception as e:
            logger.error(f"解析DuckDuckGo搜索结果失败: {str(e)}")
        
        return urls[:10]
    
    def _decode_google_url(self, google_url: str) -> Optional[str]:
        """解码Google跳转URL"""
        try:
            import urllib.parse
            if '/url?q=' in google_url:
                start = google_url.find('/url?q=') + 7
                end = google_url.find('&', start)
                if end == -1:
                    encoded_url = google_url[start:]
                else:
                    encoded_url = google_url[start:end]
                return urllib.parse.unquote(encoded_url)
        except Exception as e:
            logger.error(f"解码Google URL失败: {str(e)}")
        return None
    
    def _decode_baidu_url(self, baidu_url: str) -> Optional[str]:
        """解码百度跳转URL"""
        try:
            # 简单的百度URL解码
            if 'url=' in baidu_url:
                import urllib.parse
                start = baidu_url.find('url=') + 4
                end = baidu_url.find('&', start)
                if end == -1:
                    end = len(baidu_url)
                return urllib.parse.unquote(baidu_url[start:end])
        except:
            pass
        return None
    
    async def _scrape_single_page(self, url: str, semaphore: asyncio.Semaphore) -> Optional[ScrapedPage]:
        """抓取单个页面"""
        async with semaphore:
            try:
                start_time = time.time()
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # 解析页面内容
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 提取标题
                        title = ""
                        if soup.title:
                            title = soup.title.string.strip()
                        
                        # 提取正文内容
                        content = self._extract_main_content(soup)
                        
                        # 过滤短内容
                        if len(content) < config.quality.minimum_content_length:
                            return None
                        
                        # 获取域名
                        domain = urlparse(url).netloc
                        
                        scraped_page = ScrapedPage(
                            url=url,
                            title=title,
                            content=content,
                            source_domain=domain,
                            scrape_time=time.time() - start_time,
                            content_length=len(content),
                            metadata={
                                'status_code': response.status,
                                'content_type': response.headers.get('content-type', ''),
                                'last_modified': response.headers.get('last-modified', '')
                            }
                        )
                        
                        return scraped_page
                    else:
                        logger.debug(f"HTTP {response.status}: {url}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.debug(f"超时: {url}")
                return None
            except Exception as e:
                logger.debug(f"抓取失败 {url}: {str(e)}")
                return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取页面主要内容"""
        # 移除脚本和样式标签
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # 尝试找到主要内容区域
        main_content = ""
        
        # 常见的主要内容标签
        content_tags = ['article', 'main', 'div[class*="content"]', 'div[class*="article"]']
        
        for tag in content_tags:
            elements = soup.select(tag)
            if elements:
                main_content = elements[0].get_text(strip=True)
                break
        
        # 如果没有找到特定标签，使用body内容
        if not main_content:
            if soup.body:
                main_content = soup.body.get_text(strip=True)
        
        # 清理文本
        main_content = self._clean_text(main_content)
        
        return main_content
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除常见的垃圾内容
        spam_patterns = [
            r'Copyright.*?All rights reserved',
            r'版权所有.*?保留所有权利',
            r'广告.*?联系.*?电话',
            r'点击.*?购买',
            r'淘宝.*?价格'
        ]
        
        for pattern in spam_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    async def _adjust_concurrency(self):
        """动态调整并发数"""
        success_rate = self._get_success_rate()
        
        if success_rate > 0.9 and self.current_concurrency < config.concurrency.target_max_requests:
            self.current_concurrency = min(
                self.current_concurrency + 10,
                config.concurrency.target_max_requests
            )
            logger.info(f"📈 提高并发数至: {self.current_concurrency}")
            
        elif success_rate < 0.7 and self.current_concurrency > 50:
            self.current_concurrency = max(
                self.current_concurrency - 10,
                50
            )
            logger.info(f"📉 降低并发数至: {self.current_concurrency}")
    
    def _get_success_rate(self) -> float:
        """获取成功率"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """获取抓取统计信息"""
        elapsed_time = time.time() - self.start_time
        total_requests = self.success_count + self.failure_count
        
        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self._get_success_rate(),
            "current_concurrency": self.current_concurrency,
            "elapsed_time": elapsed_time,
            "requests_per_second": total_requests / elapsed_time if elapsed_time > 0 else 0
        }

# 创建全局实例
page_scraper = PageScraper()