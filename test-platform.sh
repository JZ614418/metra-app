#!/bin/bash
# Metra 平台测试脚本

echo "🧪 Testing Metra Platform..."

# 测试后端API
echo "1. Testing backend API..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "✅ Backend API is responding"
    
    # 测试具体端点
    echo "   Testing /docs..."
    curl -s http://localhost:8000/docs | grep -q "swagger" && echo "   ✅ API docs available"
    
    echo "   Testing /api/v1/auth/me..."
    curl -s http://localhost:8000/api/v1/auth/me | grep -q "Not authenticated" && echo "   ✅ Auth endpoint working"
    
else
    echo "❌ Backend API not responding"
fi

# 测试前端
echo "2. Testing frontend..."
FRONTEND_FOUND=false
for PORT in 8080 8081 8082 8083 8084 8085 8086; do
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/)
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo "✅ Frontend is running at http://localhost:$PORT"
        FRONTEND_FOUND=true
        break
    fi
done

if [ "$FRONTEND_FOUND" = false ]; then
    echo "❌ Frontend not found on any port"
fi

# 测试数据库
echo "3. Testing database..."
if [ -f "/Users/jz/Desktop/Metra/backend/metra.db" ]; then
    echo "✅ SQLite database exists"
else
    echo "❌ Database not found"
fi

# 测试环境变量
echo "4. Testing environment..."
if [ -f "/Users/jz/Desktop/Metra/backend/.env" ]; then
    echo "✅ Backend environment file exists"
else
    echo "❌ Backend .env file missing"
fi

if [ -f "/Users/jz/Desktop/Metra/metra-ai-factory-main/.env" ]; then
    echo "✅ Frontend environment file exists"
else
    echo "❌ Frontend .env file missing"
fi

echo ""
echo "🎯 Platform Status Summary:"
echo "Backend:  $([ "$BACKEND_STATUS" = "200" ] && echo "✅ Running" || echo "❌ Not running")"
echo "Frontend: $([ "$FRONTEND_FOUND" = true ] && echo "✅ Running" || echo "❌ Not running")"
echo "Database: $([ -f "/Users/jz/Desktop/Metra/backend/metra.db" ] && echo "✅ Available" || echo "❌ Missing")"
echo ""
echo "🚀 Ready to use!"