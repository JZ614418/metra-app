import requests
import json
from typing import List, Dict

# API 配置
API_KEY = "AIzaSyBIp4TgHag6tK4IqejDws_YBGBLs_UIEqk"
CX_ID = "31b851be19ef342a7"

def search_and_extract_data(query: str, num_results: int = 10) -> List[Dict]:
    """
    搜索并提取可用于训练的数据
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': API_KEY,
        'cx': CX_ID,
        'q': query,
        'num': min(num_results, 10)  # API 每次最多返回10个结果
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            
            # 提取训练数据
            training_data = []
            for item in data.get('items', []):
                # 提取有用的字段
                extracted_item = {
                    'title': item.get('title', ''),
                    'content': item.get('snippet', ''),  # 摘要作为内容
                    'url': item.get('link', ''),
                    'source': 'google_search',
                    
                    # 可选的额外元数据
                    'meta': {
                        'display_link': item.get('displayLink', ''),
                        'html_snippet': item.get('htmlSnippet', ''),
                        'formatted_url': item.get('formattedUrl', ''),
                    }
                }
                training_data.append(extracted_item)
            
            return training_data
        else:
            print(f"API 错误: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return []

def prepare_sentiment_analysis_data(topic: str) -> List[Dict]:
    """
    为情感分析任务准备数据的示例
    """
    # 搜索不同情感的内容
    positive_query = f"{topic} amazing excellent love"
    negative_query = f"{topic} terrible awful hate"
    neutral_query = f"{topic} review opinion"
    
    print(f"🔍 正在收集关于 '{topic}' 的训练数据...")
    
    # 收集数据
    positive_data = search_and_extract_data(positive_query, 5)
    negative_data = search_and_extract_data(negative_query, 5)
    neutral_data = search_and_extract_data(neutral_query, 5)
    
    # 标注数据
    training_samples = []
    
    for item in positive_data:
        training_samples.append({
            'text': f"{item['title']}. {item['content']}",
            'label': 'positive',
            'source_url': item['url']
        })
    
    for item in negative_data:
        training_samples.append({
            'text': f"{item['title']}. {item['content']}",
            'label': 'negative',
            'source_url': item['url']
        })
    
    for item in neutral_data:
        training_samples.append({
            'text': f"{item['title']}. {item['content']}",
            'label': 'neutral',
            'source_url': item['url']
        })
    
    return training_samples

def save_training_data(data: List[Dict], filename: str):
    """
    保存训练数据为 JSON 格式
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存 {len(data)} 条训练数据到 {filename}")

# 使用示例
if __name__ == "__main__":
    # 示例1：为情感分析收集数据
    sentiment_data = prepare_sentiment_analysis_data("iPhone 15")
    save_training_data(sentiment_data, "iphone_sentiment_training.json")
    
    # 显示一些样本
    print("\n📋 训练数据样本:")
    print("-" * 50)
    for i, sample in enumerate(sentiment_data[:3], 1):
        print(f"\n样本 {i}:")
        print(f"文本: {sample['text'][:100]}...")
        print(f"标签: {sample['label']}")
        print(f"来源: {sample['source_url']}")
    
    print(f"\n💡 提示: 这只是使用了15次API查询（共100次/天免费配额）") 