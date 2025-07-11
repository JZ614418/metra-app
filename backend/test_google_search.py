import requests
import json

# Google Custom Search API 配置
API_KEY = "AIzaSyBIp4TgHag6tK4IqejDws_YBGBLs_UIEqk"
CX_ID = "31b851be19ef342a7"

def test_google_search():
    """测试 Google Custom Search API"""
    
    # 测试查询
    query = "Python programming"
    
    # 构建请求URL
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        'key': API_KEY,
        'cx': CX_ID,
        'q': query,
        'num': 5  # 返回5个结果
    }
    
    print(f"🔍 测试搜索: '{query}'")
    print("-" * 50)
    
    try:
        # 发送请求
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # 显示搜索信息
            print(f"✅ API 调用成功!")
            print(f"📊 找到约 {data.get('searchInformation', {}).get('formattedTotalResults', 'N/A')} 个结果")
            print(f"⏱️  搜索用时: {data.get('searchInformation', {}).get('formattedSearchTime', 'N/A')}")
            print("\n📋 前5个搜索结果:")
            print("-" * 50)
            
            # 显示搜索结果
            items = data.get('items', [])
            for i, item in enumerate(items, 1):
                print(f"\n{i}. {item.get('title', 'No title')}")
                print(f"   🔗 {item.get('link', 'No link')}")
                print(f"   📝 {item.get('snippet', 'No snippet')[:100]}...")
                
            # 显示配额使用情况
            print("\n" + "-" * 50)
            print("💡 提示: Google Custom Search API 每天有100次免费查询")
            
        else:
            print(f"❌ API 调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    test_google_search() 