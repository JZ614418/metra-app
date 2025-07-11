#!/bin/bash

echo "=== 修复 Data Builder ==="
echo ""

# 检查后端是否在运行
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ 后端正在运行"
    echo "重启后端以应用修复..."
    
    # 找到进程并终止
    PID=$(lsof -ti:8000)
    kill $PID
    sleep 2
else
    echo "❌ 后端未运行"
fi

# 启动后端
echo ""
echo "启动后端服务..."
cd backend
python3 -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# 等待后端启动
echo "等待后端启动..."
sleep 5

# 测试API
echo ""
echo "测试 Data Builder API..."
curl -s http://localhost:8000/docs | grep -q "FastAPI" && echo "✅ API 正常运行" || echo "❌ API 启动失败"

echo ""
echo "=== 修复完成 ==="
echo ""
echo "现在您可以："
echo "1. 访问 http://localhost:8081/dashboard"
echo "2. 进入 Data Builder"
echo "3. 选择收集数量（如1000个样本）"
echo "4. 点击 'Start Intelligent Collection'"
echo "5. 查看实时进度"
echo "6. 收集完成后查看数据"
echo ""
echo "注意：这是模拟版本，生成的是示例数据，但功能流程完整。" 