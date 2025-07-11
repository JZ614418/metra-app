import requests
import json
from typing import List, Dict, Optional
import time

# API 配置
GOOGLE_API_KEY = "AIzaSyBIp4TgHag6tK4IqejDws_YBGBLs_UIEqk"
GOOGLE_CX_ID = "31b851be19ef342a7"
SCRAPINGBEE_API_KEY = "POZ62WX2FEH3EFD9NL8OF2AF1PFKTGDCE6MB1WF2S6WJT2TJ2V91UD1ITGG53LO595JPSZ80O9OWAEB6"

def google_search(query: str, num_results: int = 10) -> List[Dict]:
    """使用 Google 搜索获取初始结果"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CX_ID,
        'q': query,
        'num': min(num_results, 10)
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('items', [])
    return []

def get_full_content(url: str) -> Optional[str]:
    """使用 ScrapingBee 获取完整内容（仅在需要时使用）"""
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'false',
        'extract_rules': {
            'text': 'body'
        }
    }
    
    try:
        response = requests.get('https://app.scrapingbee.com/api/v1/', params=params)
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None

def smart_data_collection(query: str, task_type: str) -> List[Dict]:
    """
    智能数据收集：根据任务类型决定是否需要完整内容
    """
    print(f"🔍 搜索: {query}")
    search_results = google_search(query, 10)
    
    collected_data = []
    
    for i, result in enumerate(search_results):
        data_item = {
            'title': result.get('title', ''),
            'snippet': result.get('snippet', ''),
            'url': result.get('link', ''),
            'source': 'google_search'
        }
        
        # 根据任务类型决定是否需要完整内容
        if task_type in ['summarization', 'detailed_analysis', 'long_text']:
            print(f"  📄 获取完整内容 {i+1}/{len(search_results)}: {data_item['url'][:50]}...")
            full_content = get_full_content(data_item['url'])
            if full_content:
                data_item['full_content'] = full_content[:5000]  # 限制长度
                data_item['has_full_content'] = True
            else:
                data_item['has_full_content'] = False
            time.sleep(1)  # 避免请求过快
        else:
            # 对于分类、情感分析等任务，摘要就够了
            data_item['content'] = data_item['snippet']
            data_item['has_full_content'] = False
        
        collected_data.append(data_item)
    
    return collected_data

# 示例：不同任务的数据收集策略
def demonstrate_data_strategies():
    """展示不同任务的数据收集策略"""
    
    print("=== 1. 情感分析任务（摘要就够） ===")
    sentiment_data = smart_data_collection(
        "iPhone 15 reviews good bad", 
        task_type="sentiment_analysis"
    )
    print(f"✅ 收集了 {len(sentiment_data)} 条数据（仅使用摘要）")
    print(f"示例: {sentiment_data[0]['snippet'][:100]}...\n")
    
    print("=== 2. 文本摘要任务（需要完整内容） ===")
    summary_data = smart_data_collection(
        "artificial intelligence impact on society", 
        task_type="summarization"
    )
    full_content_count = sum(1 for d in summary_data if d.get('has_full_content'))
    print(f"✅ 收集了 {len(summary_data)} 条数据，其中 {full_content_count} 条有完整内容")
    
    return sentiment_data, summary_data

# 数据质量评估
def evaluate_data_sufficiency(data: List[Dict], task_type: str) -> Dict:
    """评估数据是否足够用于特定任务"""
    
    total_items = len(data)
    avg_snippet_length = sum(len(d.get('snippet', '')) for d in data) / total_items if total_items > 0 else 0
    full_content_items = sum(1 for d in data if d.get('has_full_content'))
    
    evaluation = {
        'total_items': total_items,
        'avg_snippet_length': avg_snippet_length,
        'full_content_items': full_content_items,
        'task_type': task_type,
        'is_sufficient': False,
        'recommendation': ''
    }
    
    # 根据任务类型评估
    if task_type in ['classification', 'sentiment_analysis', 'keyword_extraction']:
        if total_items >= 10 and avg_snippet_length >= 50:
            evaluation['is_sufficient'] = True
            evaluation['recommendation'] = '摘要数据足够用于此任务'
    elif task_type in ['summarization', 'detailed_analysis']:
        if full_content_items >= 5:
            evaluation['is_sufficient'] = True
            evaluation['recommendation'] = '有足够的完整内容进行深度分析'
        else:
            evaluation['recommendation'] = '建议获取更多完整内容'
    
    return evaluation

if __name__ == "__main__":
    # 演示不同策略
    sentiment_data, summary_data = demonstrate_data_strategies()
    
    # 评估数据充分性
    print("\n=== 数据充分性评估 ===")
    sentiment_eval = evaluate_data_sufficiency(sentiment_data, 'sentiment_analysis')
    print(f"情感分析数据: {sentiment_eval['recommendation']}")
    
    summary_eval = evaluate_data_sufficiency(summary_data, 'summarization')
    print(f"摘要生成数据: {summary_eval['recommendation']}") 