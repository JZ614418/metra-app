#!/bin/bash
# 测试 Data Builder 自动数据收集功能

echo "=== Data Builder 自动收集测试 ==="
echo ""

# 确保后端运行
echo "请确保后端正在运行 (http://localhost:8000)"
echo ""

# 1. 获取 AI 推荐
echo "步骤1: 获取 AI 推荐..."
curl -X POST http://localhost:8000/api/v1/data-builder/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{
    "task_info": {
      "task": "中医饮食指导AI",
      "type": "recommendations",
      "language": "chinese",
      "description": "提供基于中医理论的个性化饮食建议"
    },
    "selected_model": {
      "id": "chatglm2-6b",
      "name": "ChatGLM2-6B",
      "provider": "THUDM",
      "modelType": "General",
      "size": "6B"
    }
  }' | jq '.'

echo ""
echo "步骤2: 开始数据收集..."
echo "(这会启动一个实际的收集任务，收集100个样本作为演示)"

# 2. 启动收集
RESPONSE=$(curl -X POST http://localhost:8000/api/v1/data-builder/collect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{
    "task_info": {
      "task": "中医饮食指导AI",
      "type": "recommendations",
      "language": "chinese",
      "description": "提供基于中医理论的个性化饮食建议"
    },
    "selected_model": {
      "id": "chatglm2-6b",
      "name": "ChatGLM2-6B"
    },
    "data_count": 100,
    "quality_mode": "balanced",
    "use_recommendation": true
  }' 2>/dev/null)

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "收集任务已启动，Job ID: $JOB_ID"
echo ""

# 3. 监控进度
echo "步骤3: 监控收集进度..."
for i in {1..20}; do
  sleep 3
  PROGRESS=$(curl -s http://localhost:8000/api/v1/data-builder/job/$JOB_ID/progress \
    -H "Authorization: Bearer your_token_here" | jq '.')
  
  STATUS=$(echo $PROGRESS | jq -r '.status')
  PERCENT=$(echo $PROGRESS | jq -r '.progress')
  COLLECTED=$(echo $PROGRESS | jq -r '.collected_count')
  
  echo "[$i] 状态: $STATUS | 进度: $PERCENT% | 已收集: $COLLECTED 样本"
  
  if [ "$STATUS" = "completed" ]; then
    echo ""
    echo "✅ 数据收集完成！"
    break
  fi
done

echo ""
echo "步骤4: 查看收集的数据..."
curl -s "http://localhost:8000/api/v1/data-builder/job/$JOB_ID/data?limit=5" \
  -H "Authorization: Bearer your_token_here" | jq '.data[:2]'

echo ""
echo "=== 测试完成 ==="
echo "这就是 Data Builder 如何自动收集适合您任务的训练数据！" 