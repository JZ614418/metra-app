"""
中医AI训练数据收集示例
展示如何为特定领域（中医）收集高质量训练数据
"""

import requests
import json
from typing import List, Dict
import time

# API 配置
GOOGLE_API_KEY = "AIzaSyBIp4TgHag6tK4IqejDws_YBGBLs_UIEqk"
GOOGLE_CX_ID = "31b851be19ef342a7"

def search_tcm_data(query: str, num_results: int = 10) -> List[Dict]:
    """使用 Google 搜索中医相关数据"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CX_ID,
        'q': query,
        'num': min(num_results, 10),
        'lr': 'lang_zh-CN|lang_zh-TW|lang_en',  # 中文和英文结果
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
    except Exception as e:
        print(f"搜索出错: {e}")
    return []

def collect_tcm_training_data():
    """收集中医AI训练数据的完整流程"""
    
    print("🏥 开始收集中医AI训练数据...")
    print("=" * 50)
    
    # 1. 定义不同类型的查询
    queries = {
        "症状诊断": [
            "中医 头痛 辨证论治",
            "中医 失眠 病因 治疗方法",
            "中医 咳嗽 分型 症状表现",
            "TCM headache diagnosis treatment",
        ],
        "中药知识": [
            "人参 功效 主治 用法用量",
            "黄芪 药性 归经 配伍禁忌",
            "中药 君臣佐使 配伍原则",
            "Chinese herbal medicine properties",
        ],
        "经络穴位": [
            "足三里 穴位 位置 功效 按摩方法",
            "合谷穴 主治 针灸手法",
            "十二经络 循行路线 主治病症",
            "acupuncture points meridians",
        ],
        "中医理论": [
            "阴阳五行 中医基础理论",
            "望闻问切 四诊方法",
            "气血津液 辨证要点",
            "TCM fundamental theory",
        ],
        "病案分析": [
            "中医 病案 医案 分析",
            "名医 验方 临床经验",
            "中医 治疗 成功案例",
            "TCM clinical cases",
        ]
    }
    
    all_training_data = []
    
    # 2. 收集各类数据
    for category, query_list in queries.items():
        print(f"\n📂 收集类别: {category}")
        category_data = []
        
        for query in query_list:
            print(f"  🔍 搜索: {query}")
            results = search_tcm_data(query, 5)
            
            for result in results:
                # 提取训练数据
                training_item = {
                    "category": category,
                    "query": query,
                    "title": result.get('title', ''),
                    "content": result.get('snippet', ''),
                    "url": result.get('link', ''),
                    "source": "google_search",
                    
                    # 判断内容质量
                    "quality_indicators": {
                        "has_chinese": any(ord(c) > 127 for c in result.get('snippet', '')),
                        "length": len(result.get('snippet', '')),
                        "has_medical_terms": any(term in result.get('snippet', '') 
                                               for term in ['症', '病', '治', '药', '穴', '脉']),
                    }
                }
                category_data.append(training_item)
            
            time.sleep(0.5)  # 避免请求过快
        
        print(f"  ✅ 收集了 {len(category_data)} 条数据")
        all_training_data.extend(category_data)
    
    return all_training_data

def prepare_tcm_qa_pairs(raw_data: List[Dict]) -> List[Dict]:
    """将原始数据转换为问答对格式"""
    qa_pairs = []
    
    # 基于收集的数据生成问答对
    for item in raw_data:
        if item['category'] == "症状诊断":
            # 提取症状和治疗方法
            qa_pairs.append({
                "question": f"中医如何看待{item['title'].split()[0]}？",
                "answer": item['content'],
                "category": "诊断",
                "source": item['url']
            })
        
        elif item['category'] == "中药知识":
            # 提取中药功效
            qa_pairs.append({
                "question": f"{item['title'].split()[0]}有什么功效？",
                "answer": item['content'],
                "category": "中药",
                "source": item['url']
            })
        
        elif item['category'] == "经络穴位":
            # 提取穴位信息
            qa_pairs.append({
                "question": f"{item['title'].split('穴')[0]}穴在哪里？有什么作用？",
                "answer": item['content'],
                "category": "针灸",
                "source": item['url']
            })
    
    return qa_pairs

def generate_tcm_training_report(data: List[Dict], qa_pairs: List[Dict]):
    """生成数据收集报告"""
    print("\n" + "=" * 50)
    print("📊 中医AI训练数据收集报告")
    print("=" * 50)
    
    # 统计信息
    total_items = len(data)
    categories = {}
    chinese_content = 0
    
    for item in data:
        cat = item['category']
        categories[cat] = categories.get(cat, 0) + 1
        if item['quality_indicators']['has_chinese']:
            chinese_content += 1
    
    print(f"\n✅ 总共收集数据: {total_items} 条")
    print(f"✅ 包含中文内容: {chinese_content} 条")
    print(f"✅ 生成问答对: {len(qa_pairs)} 对")
    
    print("\n📈 各类别数据分布:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count} 条")
    
    print("\n💡 数据质量评估:")
    avg_length = sum(item['quality_indicators']['length'] for item in data) / len(data)
    medical_terms = sum(1 for item in data if item['quality_indicators']['has_medical_terms'])
    
    print(f"  - 平均内容长度: {avg_length:.0f} 字符")
    print(f"  - 包含医学术语: {medical_terms} 条 ({medical_terms/total_items*100:.1f}%)")
    
    print("\n🎯 下一步建议:")
    print("  1. 使用 AI 生成更多相关问答对")
    print("  2. 补充权威中医典籍数据（如《黄帝内经》）")
    print("  3. 添加现代中医临床研究数据")
    print("  4. 邀请中医专家审核和标注")

def save_tcm_training_data(data: List[Dict], qa_pairs: List[Dict]):
    """保存训练数据"""
    # 保存原始数据
    with open('tcm_raw_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 保存问答对
    with open('tcm_qa_pairs.json', 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    
    # 保存为训练格式（JSONL）
    with open('tcm_training.jsonl', 'w', encoding='utf-8') as f:
        for qa in qa_pairs:
            f.write(json.dumps({
                "instruction": qa['question'],
                "output": qa['answer'],
                "category": qa['category']
            }, ensure_ascii=False) + '\n')
    
    print(f"\n💾 数据已保存:")
    print(f"  - tcm_raw_data.json (原始数据)")
    print(f"  - tcm_qa_pairs.json (问答对)")
    print(f"  - tcm_training.jsonl (训练格式)")

if __name__ == "__main__":
    # 收集数据
    raw_data = collect_tcm_training_data()
    
    # 转换为问答对
    qa_pairs = prepare_tcm_qa_pairs(raw_data)
    
    # 生成报告
    generate_tcm_training_report(raw_data, qa_pairs)
    
    # 保存数据
    save_tcm_training_data(raw_data, qa_pairs)
    
    # 展示一些样本
    print("\n📝 训练数据样本:")
    print("-" * 50)
    for i, qa in enumerate(qa_pairs[:3], 1):
        print(f"\n样本 {i}:")
        print(f"问: {qa['question']}")
        print(f"答: {qa['answer'][:100]}...")
        print(f"类别: {qa['category']}") 