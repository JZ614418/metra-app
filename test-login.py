#!/usr/bin/env python3
import requests
import json

# API 基础 URL
API_URL = "https://backend-api-production-e944.up.railway.app/api/v1"

def test_register():
    """测试注册功能"""
    print("=== 测试注册 ===")
    url = f"{API_URL}/auth/register"
    data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"错误: {e}")
    print()

def test_login():
    """测试登录功能"""
    print("=== 测试登录 ===")
    url = f"{API_URL}/auth/login"
    data = {
        "email": "jzhe614@gmail.com",
        "password": "Jz061407"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            return result.get("access_token")
    except Exception as e:
        print(f"错误: {e}")
    print()
    return None

def test_get_user_info(token):
    """测试获取用户信息"""
    print("=== 测试获取用户信息 ===")
    url = f"{API_URL}/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"错误: {e}")
    print()

def test_health():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    url = "https://backend-api-production-e944.up.railway.app/health"
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")
    print()

if __name__ == "__main__":
    # 测试健康检查
    test_health()
    
    # 测试注册（可能会失败如果用户已存在）
    test_register()
    
    # 测试登录
    token = test_login()
    
    # 如果登录成功，测试获取用户信息
    if token:
        test_get_user_info(token)
    else:
        print("登录失败，无法测试获取用户信息") 