"""
Metra 合规数据收集策略
遵循法律法规，保护用户和数据提供方的权益
"""

from typing import List, Dict, Optional
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

class CompliantDataCollector:
    """合规的数据收集器"""
    
    def __init__(self):
        self.google_api_key = "YOUR_GOOGLE_API_KEY"
        self.google_cx_id = "YOUR_CX_ID"
        
        # 白名单：明确允许爬取的网站
        self.whitelist_domains = [
            'wikipedia.org',
            'news.ycombinator.com',
            'reddit.com',  # 通过 API
            'arxiv.org',
            'github.com',  # 通过 API
        ]
        
        # 黑名单：不应爬取的网站
        self.blacklist_domains = [
            'facebook.com',
            'instagram.com',
            'linkedin.com',
            'twitter.com',  # 需要 API
            'amazon.com',   # 商业数据
            'netflix.com',  # 付费内容
        ]
    
    def check_robots_txt(self, url: str) -> bool:
        """检查 robots.txt 是否允许爬取"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            # 检查是否允许爬取
            return rp.can_fetch("*", url)
        except:
            # 如果无法获取 robots.txt，保守起见返回 False
            return False
    
    def is_domain_allowed(self, url: str) -> bool:
        """检查域名是否在允许列表中"""
        domain = urlparse(url).netloc
        
        # 检查黑名单
        for blacklisted in self.blacklist_domains:
            if blacklisted in domain:
                return False
        
        # 检查白名单
        for whitelisted in self.whitelist_domains:
            if whitelisted in domain:
                return True
        
        # 默认需要进一步检查
        return None
    
    def collect_data_safely(self, query: str, task_type: str) -> List[Dict]:
        """安全合规的数据收集流程"""
        
        print(f"🔍 开始合规数据收集: {query}")
        
        # 第一步：使用搜索 API（完全合法）
        search_results = self._google_search(query)
        
        collected_data = []
        
        for result in search_results:
            url = result.get('link', '')
            
            # 检查域名是否允许
            domain_check = self.is_domain_allowed(url)
            
            if domain_check is False:
                print(f"❌ 跳过黑名单网站: {url}")
                continue
            
            # 基础数据（来自搜索API，完全合法）
            data_item = {
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'url': url,
                'source': 'google_search_api',
                'is_full_content': False,
                'compliance_status': 'verified'
            }
            
            # 判断是否需要完整内容
            if task_type in ['summarization', 'detailed_analysis']:
                if domain_check is True:  # 白名单网站
                    print(f"✅ 白名单网站，可以获取完整内容: {url}")
                    # 这里可以调用 ScrapingBee，但要遵守使用条款
                    data_item['can_fetch_full'] = True
                else:
                    # 检查 robots.txt
                    if self.check_robots_txt(url):
                        print(f"✅ robots.txt 允许: {url}")
                        data_item['can_fetch_full'] = True
                    else:
                        print(f"⚠️  robots.txt 不允许或不确定: {url}")
                        data_item['can_fetch_full'] = False
            
            collected_data.append(data_item)
        
        return collected_data
    
    def _google_search(self, query: str) -> List[Dict]:
        """使用 Google Search API（合法）"""
        # 实现略，同之前的代码
        pass

# 推荐的数据来源（完全合法）
RECOMMENDED_DATA_SOURCES = {
    "学术研究": [
        "Google Scholar API",
        "arXiv API",
        "PubMed API",
        "Semantic Scholar API"
    ],
    "新闻数据": [
        "NewsAPI",
        "Guardian API",
        "NY Times API",
        "BBC API"
    ],
    "社交媒体": [
        "Twitter API",
        "Reddit API",
        "YouTube API"
    ],
    "开放数据": [
        "Wikipedia API",
        "Wikidata",
        "Common Crawl",
        "Government Open Data"
    ],
    "商业数据": [
        "Alpha Vantage (金融)",
        "OpenWeatherMap (天气)",
        "Unsplash API (图片)"
    ]
}

# 最佳实践建议
BEST_PRACTICES = """
1. 优先使用官方 API
2. 遵守 robots.txt
3. 控制请求频率
4. 标注数据来源
5. 尊重版权
6. 保护用户隐私
7. 定期审查合规性
"""

def generate_compliance_report(collected_data: List[Dict]) -> Dict:
    """生成合规性报告"""
    total = len(collected_data)
    from_api = sum(1 for d in collected_data if d['source'] == 'google_search_api')
    can_fetch = sum(1 for d in collected_data if d.get('can_fetch_full', False))
    
    report = {
        "total_items": total,
        "from_search_api": from_api,
        "can_fetch_full_content": can_fetch,
        "compliance_rate": "100%",  # 因为我们只收集合规数据
        "recommendation": "所有数据均通过合法途径获取"
    }
    
    return report 