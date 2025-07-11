#!/bin/bash

echo "🧪 Testing Model Recommendation API..."

# API configuration
BASE_URL="http://localhost:8000"
API_PREFIX="/api/v1"
EMAIL="jzhe614@gmail.com"
PASSWORD="Jz061407"

# Login
echo "1️⃣ Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL$API_PREFIX/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed!"
    exit 1
fi
echo "✅ Login successful"

# Test 1: Chinese task recommendation
echo ""
echo "2️⃣ Testing Chinese task recommendation..."
CHINESE_RESPONSE=$(curl -s -X POST "$BASE_URL$API_PREFIX/recommendations/recommend" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "task_definition": {
            "task": "中医饮食建议AI",
            "language": "chinese",
            "target_audience": "普通人",
            "input_format": {
                "feelings": "用户提供的感受或症状"
            },
            "output_format": {
                "recommendations": "饮食建议"
            },
            "features": "结合中医知识，提供具体饮食建议"
        }
    }')

echo "Response:"
echo "$CHINESE_RESPONSE" | jq '.recommendations[:3]' 2>/dev/null || echo "$CHINESE_RESPONSE"

# Test 2: English task recommendation
echo ""
echo "3️⃣ Testing English task recommendation..."
ENGLISH_RESPONSE=$(curl -s -X POST "$BASE_URL$API_PREFIX/recommendations/recommend" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "task_definition": {
            "task": "Customer Complaint Classifier",
            "language": "english",
            "task_type": "text-classification",
            "labels": ["complaint", "not_complaint"]
        }
    }')

echo "Response:"
echo "$ENGLISH_RESPONSE" | jq '.recommendations[:3]' 2>/dev/null || echo "$ENGLISH_RESPONSE"

echo ""
echo "✅ Test completed!" 