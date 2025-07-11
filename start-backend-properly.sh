#!/bin/bash

echo "=== 启动 Metra 后端服务 ==="
echo ""

# 进入backend目录
cd backend

# 检查虚拟环境是否存在
if [ -f "../venv/bin/uvicorn" ]; then
    echo "✅ 找到虚拟环境"
    
    # 检查端口是否被占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  端口8000已被占用，正在关闭旧进程..."
        PID=$(lsof -ti:8000)
        kill $PID
        sleep 2
    fi
    
    # 使用虚拟环境的Python启动uvicorn
    echo "🚀 启动后端服务..."
    ../venv/bin/python -m uvicorn app.main:app --reload --port 8000 &
    BACKEND_PID=$!
    echo "后端PID: $BACKEND_PID"
    
    # 等待服务启动
    echo "等待服务启动..."
    for i in {1..10}; do
        sleep 1
        if curl -s http://localhost:8000/docs | grep -q "FastAPI"; then
            echo ""
            echo "✅ 后端服务启动成功！"
            echo "📍 API文档: http://localhost:8000/docs"
            echo "📍 前端地址: http://localhost:8081"
            echo ""
            echo "现在您可以使用 Data Builder 了！"
            exit 0
        fi
        echo -n "."
    done
    
    echo ""
    echo "❌ 后端启动失败，请检查错误信息"
else
    echo "❌ 未找到虚拟环境"
    echo "请先创建虚拟环境:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
fi 