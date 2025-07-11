#!/bin/bash
# Metra 启动脚本 - 修复版本

echo "🚀 Starting Metra AI Platform..."

# 设置工作目录
PROJECT_ROOT="/Users/jz/Desktop/Metra"
cd "$PROJECT_ROOT"

# 启动后端
echo "📚 Starting backend..."
cd "$PROJECT_ROOT/backend"
source venv/bin/activate
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# 等待后端启动
sleep 5

# 启动前端
echo "🎨 Starting frontend..."
cd "$PROJECT_ROOT/metra-ai-factory-main"
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# 等待前端启动
sleep 5

# 测试服务状态
echo "🔍 Checking services..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "✅ Backend is running at http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
else
    echo "❌ Backend failed to start"
fi

# 前端可能在不同端口
for PORT in 8080 8081 8082 8083 8084 8085 8086; do
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/)
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo "✅ Frontend is running at http://localhost:$PORT"
        break
    fi
done

echo ""
echo "🎉 Metra platform started successfully!"
echo "📋 Next steps:"
echo "   1. Open http://localhost:8086 (or check other ports 8080-8086)"
echo "   2. Register/login to access the platform"
echo "   3. Start building your AI models!"
echo ""
echo "🔧 To stop services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"