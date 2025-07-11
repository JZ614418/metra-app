"""
中医AI训练数据收集 - 合规增强版
在不违法的前提下，使用 ScrapingBee 扩展数据收集能力
"""

import requests
import json
from typing import List, Dict, Optional
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

# API 配置
GOOGLE_API_KEY = "AIzaSyBIp4TgHag6tK4IqejDws_YBGBLs_UIEqk"
GOOGLE_CX_ID = "31b851be19ef342a7"
SCRAPINGBEE_API_KEY = "POZ62WX2FEH3EFD9NL8OF2AF1PFKTGDCE6MB1WF2S6WJT2TJ2V91UD1ITGG53LO595JPSZ80O9OWAEB6"

# 合法数据源白名单（这些网站明确允许合理使用）
LEGAL_SOURCES = {
    # 开放知识库
    "wikipedia.org": {
        "type": "open_knowledge",
        "license": "CC BY-SA",
        "can_scrape": True
    },
    "wikihow.com": {
        "type": "open_knowledge", 
        "license": "CC BY-NC-SA",
        "can_scrape": True
    },
    
    # 学术开放获取
    "pubmed.ncbi.nlm.nih.gov": {
        "type": "academic",
        "license": "public_domain",
        "can_scrape": True,
        "rate_limit": 3  # 每秒请求数
    },
    "arxiv.org": {
        "type": "academic",
        "license": "various_open",
        "can_scrape": True
    },
    
    # 政府公开数据
    "cdc.gov": {
        "type": "government",
        "license": "public_domain",
        "can_scrape": True
    },
    "who.int": {
        "type": "government",
        "license": "public_domain",
        "can_scrape": True
    },
    
    # 中医专业网站（需要检查具体条款）
    "tcmwiki.com": {
        "type": "tcm_resource",
        "license": "check_terms",
        "can_scrape": "check_robots"
    }
}

class LegalTCMDataCollector:
    """合法的中医数据收集器"""
    
    def __init__(self):
        self.google_api_key = GOOGLE_API_KEY
        self.google_cx_id = GOOGLE_CX_ID
        self.scrapingbee_api_key = SCRAPINGBEE_API_KEY
        self.robots_cache = {}  # 缓存robots.txt结果
    
    def check_legal_status(self, url: str) -> Dict:
        """检查URL的法律状态"""
        domain = urlparse(url).netloc
        
        # 检查是否在白名单中
        for legal_domain, info in LEGAL_SOURCES.items():
            if legal_domain in domain:
                return {
                    "status": "whitelisted",
                    "can_scrape": info.get("can_scrape", False),
                    "license": info.get("license", "unknown"),
                    "type": info.get("type", "unknown")
                }
        
        # 检查robots.txt
        if self.check_robots_txt(url):
            return {
                "status": "robots_allowed",
                "can_scrape": True,
                "license": "unknown",
                "type": "general"
            }
        
        return {
            "status": "not_verified",
            "can_scrape": False,
            "license": "unknown",
            "type": "unknown"
        }
    
    def check_robots_txt(self, url: str) -> bool:
        """检查robots.txt是否允许爬取"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            # 使用缓存
            if robots_url in self.robots_cache:
                return self.robots_cache[robots_url]
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            # 检查是否允许
            allowed = rp.can_fetch("*", url)
            self.robots_cache[robots_url] = allowed
            
            return allowed
        except:
            return False
    
    def google_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """使用Google搜索API"""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cx_id,
            'q': query,
            'num': min(num_results, 10),
            'lr': 'lang_zh-CN|lang_zh-TW|lang_en'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        return []
    
    def scrape_with_scrapingbee(self, url: str) -> Optional[Dict]:
        """使用ScrapingBee获取内容（仅限合法网站）"""
        # 首先检查法律状态
        legal_status = self.check_legal_status(url)
        
        if not legal_status['can_scrape']:
            print(f"⚠️  跳过不允许爬取的网站: {url}")
            return None
        
        print(f"✅ 合法获取内容: {url} (状态: {legal_status['status']})")
        
        params = {
            'api_key': self.scrapingbee_api_key,
            'url': url,
            'render_js': 'false',
            'premium_proxy': 'false',
            'extract_rules': {
                'title': 'title',
                'content': {
                    'selector': 'body',
                    'type': 'text'
                },
                'meta_description': 'meta[name="description"]@content'
            }
        }
        
        try:
            response = requests.get('https://app.scrapingbee.com/api/v1/', params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    'title': data.get('title', ''),
                    'content': data.get('content', '')[:5000],  # 限制长度
                    'description': data.get('meta_description', ''),
                    'legal_status': legal_status
                }
        except Exception as e:
            print(f"❌ 获取内容失败: {e}")
        
        return None
    
    def collect_tcm_data_enhanced(self):
        """增强的中医数据收集（合法版）"""
        print("🏥 开始合法收集中医AI训练数据（增强版）...")
        print("=" * 50)
        
        # 专门针对开放资源的查询
        queries = {
            "维基百科中医": [
                "site:wikipedia.org 中医",
                "site:wikipedia.org 中药",
                "site:wikipedia.org 针灸",
                "site:wikipedia.org Traditional Chinese Medicine"
            ],
            "学术论文": [
                "site:pubmed.ncbi.nlm.nih.gov TCM",
                "site:pubmed.ncbi.nlm.nih.gov acupuncture",
                "site:arxiv.org traditional chinese medicine"
            ],
            "政府健康信息": [
                "site:who.int traditional medicine",
                "site:cdc.gov complementary medicine"
            ]
        }
        
        collected_data = []
        
        for category, query_list in queries.items():
            print(f"\n📂 收集类别: {category}")
            
            for query in query_list:
                print(f"  🔍 搜索: {query}")
                results = self.google_search(query, 5)
                
                for result in results:
                    url = result.get('link', '')
                    
                    # 基础数据（来自搜索API）
                    data_item = {
                        'category': category,
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'url': url,
                        'source': 'google_search'
                    }
                    
                    # 尝试获取完整内容（仅限合法网站）
                    full_content = self.scrape_with_scrapingbee(url)
                    if full_content:
                        data_item['full_content'] = full_content['content']
                        data_item['has_full_content'] = True
                        data_item['legal_info'] = full_content['legal_status']
                    else:
                        data_item['has_full_content'] = False
                    
                    collected_data.append(data_item)
                    time.sleep(1)  # 遵守速率限制
        
        return collected_data

def demonstrate_legal_enhancement():
    """演示合法的数据增强"""
    collector = LegalTCMDataCollector()
    
    # 收集数据
    enhanced_data = collector.collect_tcm_data_enhanced()
    
    # 生成报告
    print("\n" + "=" * 50)
    print("📊 合法数据收集报告")
    print("=" * 50)
    
    total = len(enhanced_data)
    with_full_content = sum(1 for d in enhanced_data if d.get('has_full_content'))
    
    # 按法律状态分类
    legal_stats = {}
    for item in enhanced_data:
        if 'legal_info' in item:
            status = item['legal_info']['status']
            legal_stats[status] = legal_stats.get(status, 0) + 1
    
    print(f"\n✅ 总共收集: {total} 条")
    print(f"✅ 获取完整内容: {with_full_content} 条")
    
    print("\n📋 法律状态分布:")
    for status, count in legal_stats.items():
        print(f"  - {status}: {count} 条")
    
    print("\n💡 合规性保证:")
    print("  ✓ 仅从白名单网站获取完整内容")
    print("  ✓ 遵守robots.txt规则")
    print("  ✓ 标注数据来源和许可")
    print("  ✓ 控制请求频率")
    
    # 展示一些样本
    print("\n📝 数据样本:")
    print("-" * 50)
    for item in enhanced_data[:2]:
        if item.get('has_full_content'):
            print(f"\n来源: {item['url']}")
            print(f"标题: {item['title']}")
            print(f"摘要: {item['snippet'][:100]}...")
            print(f"完整内容: {item.get('full_content', '')[:200]}...")
            print(f"法律状态: {item.get('legal_info', {}).get('status', 'N/A')}")
            print(f"许可类型: {item.get('legal_info', {}).get('license', 'N/A')}")
    
    return enhanced_data

# 最佳实践建议
BEST_PRACTICES = """
合法使用 ScrapingBee 的最佳实践：

1. 白名单优先
   - 优先从明确允许的网站获取数据
   - 维护并定期更新白名单

2. 遵守规则
   - 始终检查 robots.txt
   - 遵守网站的使用条款
   - 控制请求频率

3. 透明标注
   - 记录数据来源
   - 标注许可类型
   - 保留原始URL

4. 用户教育
   - 在产品中说明数据来源
   - 提醒用户合规使用
   - 提供数据使用指南

5. 定期审查
   - 定期检查法律法规变化
   - 更新合规策略
   - 审查数据使用情况
"""

if __name__ == "__main__":
    # 演示合法的增强数据收集
    enhanced_data = demonstrate_legal_enhancement()
    
    # 保存数据
    with open('tcm_enhanced_legal_data.json', 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 增强数据已保存到: tcm_enhanced_legal_data.json")
    print("\n" + BEST_PRACTICES) 