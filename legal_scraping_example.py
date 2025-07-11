"""
合法爬虫示例 - 遵守所有法律和道德规范
"""
import httpx
import time
from urllib.robotparser import RobotFileParser
import asyncio

class LegalScraper:
    def __init__(self):
        self.session = httpx.AsyncClient()
        self.robot_parser = RobotFileParser()
        
    async def check_robots_txt(self, url):
        """检查 robots.txt 是否允许爬取"""
        domain = httpx.URL(url).host
        robots_url = f"https://{domain}/robots.txt"
        
        try:
            response = await self.session.get(robots_url)
            self.robot_parser.parse(response.text.splitlines())
            return self.robot_parser.can_fetch("*", url)
        except:
            # 如果没有 robots.txt，默认允许
            return True
    
    async def scrape_with_respect(self, url):
        """尊重网站规则的爬取"""
        # 1. 检查 robots.txt
        if not await self.check_robots_txt(url):
            print(f"❌ {url} 不允许爬取")
            return None
            
        # 2. 添加合理的请求头
        headers = {
            'User-Agent': 'Metra-Bot/1.0 (Educational Purpose; Contact: your-email@example.com)',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # 3. 控制请求频率（每次请求间隔2秒）
        await asyncio.sleep(2)
        
        # 4. 发送请求
        try:
            response = await self.session.get(url, headers=headers, timeout=10)
            return response.text
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            return None

# 使用公开数据源的例子
LEGAL_DATA_SOURCES = {
    "公开评论": [
        # 使用提供API的平台
        "https://api.example.com/public-reviews",
        # 明确允许爬取的网站
        "https://open-data.example.com/feedback",
    ],
    "学术数据": [
        # 研究用数据集
        "https://dataset.example.edu/complaints",
    ],
    "开源数据": [
        # GitHub上的公开数据
        "https://raw.githubusercontent.com/example/dataset/main/data.json",
    ]
}

# 使用 API 而不是爬虫
async def use_official_apis():
    """优先使用官方API"""
    apis = {
        "Twitter": "https://api.twitter.com/2/tweets/search/recent",
        "Reddit": "https://www.reddit.com/r/complaints.json",
        "GitHub": "https://api.github.com/search/issues?q=complaint",
    }
    
    # 这些API都是合法的数据获取方式
    for name, api_url in apis.items():
        print(f"✅ 使用 {name} 官方API获取数据")

# 最佳实践建议
BEST_PRACTICES = """
✅ 合法爬虫最佳实践：
1. 始终检查并遵守 robots.txt
2. 使用明确的 User-Agent 标识
3. 控制请求频率，避免给服务器造成负担
4. 优先使用官方 API
5. 只爬取公开可访问的数据
6. 保留数据来源信息
7. 尊重版权和隐私
8. 获取必要的许可和授权
"""

if __name__ == "__main__":
    print(BEST_PRACTICES) 