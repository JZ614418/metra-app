#!/bin/bash

echo "🧪 测试Metra后端所有功能"
echo "=========================="

# 后端URL
API_URL="https://backend-api-production-e944.up.railway.app/api/v1"

# 测试账号
EMAIL="jzhe614@gmail.com"
PASSWORD="Jz061407"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "1. 测试后端健康状态..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$API_URL/../")
if [[ $HEALTH_RESPONSE == *"HTTP_STATUS:200"* ]]; then
    echo -e "${GREEN}✓ 后端运行正常${NC}"
else
    echo -e "${RED}✗ 后端可能有问题${NC}"
fi

echo -e "\n2. 测试用户登录..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

if [[ $LOGIN_RESPONSE == *"access_token"* ]]; then
    echo -e "${GREEN}✓ 登录成功${NC}"
    TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "获取到Token: ${TOKEN:0:20}..."
else
    echo -e "${RED}✗ 登录失败${NC}"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "\n3. 测试获取用户信息..."
ME_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
    -H "Authorization: Bearer $TOKEN")

if [[ $ME_RESPONSE == *"email"* ]]; then
    echo -e "${GREEN}✓ 用户信息获取成功${NC}"
else
    echo -e "${RED}✗ 用户信息获取失败${NC}"
fi

echo -e "\n4. 测试模型推荐API..."
RECOMMEND_RESPONSE=$(curl -s -X POST "$API_URL/recommendations/recommend" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "task_definition": {
            "task_type": "text_classification",
            "description": "测试情感分析"
        }
    }')

if [[ $RECOMMEND_RESPONSE == *"models"* ]]; then
    echo -e "${GREEN}✓ 模型推荐API正常${NC}"
else
    echo -e "${RED}✗ 模型推荐API异常${NC}"
fi

echo -e "\n5. 测试数据收集API..."
DATA_RESPONSE=$(curl -s -X GET "$API_URL/data-collection/sources" \
    -H "Authorization: Bearer $TOKEN")

if [[ $DATA_RESPONSE == *"sources"* ]] || [[ $DATA_RESPONSE == *"google"* ]]; then
    echo -e "${GREEN}✓ 数据收集API正常${NC}"
else
    echo -e "${RED}✗ 数据收集API异常${NC}"
fi

echo -e "\n=========================="
echo "测试完成！"
echo ""
echo "📋 总结："
echo "- 后端URL: $API_URL"
echo "- 所有核心API都已测试"
echo "- 如果都是绿色✓，说明后端完全正常"
echo ""
echo "🚀 下一步："
echo "1. 按照 DEPLOY_FRONTEND_NOW.md 部署前端"
echo "2. 部署后访问前端URL测试完整流程" 