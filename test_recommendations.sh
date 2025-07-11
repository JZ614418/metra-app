#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTE1MDU4NDIsInN1YiI6IjA2YmNkNzEzLWU4ZWUtNGUzYi1hY2JmLWYyMzNlOTY3NTAzOSJ9._TsBioH5QQEIzNRYCCaUzCrb--gdHaN1X7BSY_tfJO8"
BASE_URL="http://localhost:8000/api/v1"

echo "======================================================================"
echo "TESTING MODEL RECOMMENDATIONS"
echo "======================================================================"

# Test 1: Chinese Medical Task
echo -e "\n\n### Test 1: Chinese Medical Task"
curl -s -X POST ${BASE_URL}/recommendations/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "task_definition": {
      "task": "为老年人提供健康饮食建议",
      "language": "chinese",
      "domain": "health"
    }
  }' | jq '{keywords: .search_keywords, models: .recommendations[:2] | map({name: .model_name, author: .author})}'

# Test 2: Auto-detect Chinese
echo -e "\n\n### Test 2: Auto-detect Chinese (no language field)"
curl -s -X POST ${BASE_URL}/recommendations/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "task_definition": {
      "task": "创建一个智能客服系统"
    }
  }' | jq '{keywords: .search_keywords, models: .recommendations[:2] | map({name: .model_name, author: .author})}'

# Test 3: Text Classification
echo -e "\n\n### Test 3: Text Classification Task"
curl -s -X POST ${BASE_URL}/recommendations/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "task_definition": {
      "task_type": "text-classification",
      "task": "Sentiment analysis",
      "language": "english"
    }
  }' | jq '{keywords: .search_keywords, models: .recommendations[:2] | map({name: .model_name, type: .pipeline_tag})}'

# Test 4: Question Answering
echo -e "\n\n### Test 4: Question Answering Task"
curl -s -X POST ${BASE_URL}/recommendations/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "task_definition": {
      "task_type": "question-answering",
      "task": "Answer questions from documents",
      "language": "english"
    }
  }' | jq '{keywords: .search_keywords, models: .recommendations[:2] | map({name: .model_name, type: .pipeline_tag})}'

# Test 5: Chinese Legal
echo -e "\n\n### Test 5: Chinese Legal Task (auto-detect)"
curl -s -X POST ${BASE_URL}/recommendations/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "task_definition": {
      "task": "分析合同条款，识别法律风险"
    }
  }' | jq '{keywords: .search_keywords, models: .recommendations[:2] | map({name: .model_name, author: .author})}'

echo -e "\n\n======================================================================"
echo "TESTING COMPLETE"
echo "======================================================================" 