#!/usr/bin/env python3
import requests
import json

# API configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTE1MDU4NDIsInN1YiI6IjA2YmNkNzEzLWU4ZWUtNGUzYi1hY2JmLWYyMzNlOTY3NTAzOSJ9._TsBioH5QQEIzNRYCCaUzCrb--gdHaN1X7BSY_tfJO8"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

# Test scenarios
test_cases = [
    {
        "name": "Chinese Medical Task",
        "task_definition": {
            "task": "为老年人提供健康饮食建议",
            "language": "chinese",
            "domain": "health",
            "target_audience": "老年人"
        }
    },
    {
        "name": "English Finance Task",
        "task_definition": {
            "task": "Analyze stock market trends",
            "language": "english",
            "domain": "finance"
        }
    },
    {
        "name": "Auto-detect Chinese (no language field)",
        "task_definition": {
            "task": "创建一个智能客服系统"
        }
    },
    {
        "name": "Mixed Language Task",
        "task_definition": {
            "task": "Build a bot that supports 中英文双语"
        }
    },
    {
        "name": "Text Classification Task",
        "task_definition": {
            "task_type": "text-classification",
            "task": "Sentiment analysis for reviews",
            "language": "english"
        }
    },
    {
        "name": "Chinese Legal Task",
        "task_definition": {
            "task": "分析合同条款，识别法律风险",
            "domain": "legal"
        }
    },
    {
        "name": "Code Generation Task",
        "task_definition": {
            "task": "Generate Python code from descriptions",
            "domain": "programming",
            "language": "english"
        }
    },
    {
        "name": "Education Task (Chinese)",
        "task_definition": {
            "task": "为小学生设计数学练习题",
            "target_audience": "小学生"
        }
    }
]

# Run tests
print("=" * 80)
print("TESTING MODEL RECOMMENDATIONS")
print("=" * 80)

for test in test_cases:
    print(f"\n\n### Test: {test['name']}")
    print(f"Task Definition: {json.dumps(test['task_definition'], ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/recommendations/recommend",
            headers=headers,
            json={"task_definition": test['task_definition']}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSearch Keywords: {data.get('search_keywords', 'N/A')}")
            print(f"\nTop 3 Recommendations:")
            
            for i, rec in enumerate(data.get('recommendations', [])[:3], 1):
                print(f"{i}. {rec['model_name']} by {rec['author']}")
                print(f"   Downloads: {rec['downloads']:,}")
                if rec.get('pipeline_tag'):
                    print(f"   Type: {rec['pipeline_tag']}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80) 