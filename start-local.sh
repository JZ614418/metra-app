#!/bin/bash

echo "🚀 Starting Metra AI locally..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Kill any existing processes on ports 8000 and 5173
echo "🧹 Cleaning up old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Start backend
echo "🔧 Starting backend..."
cd backend
source ../venv/bin/activate

# Check if local_env.sh exists
if [ ! -f "local_env.sh" ]; then
    echo "⚠️  local_env.sh not found. Using default environment variables..."
else
source local_env.sh
fi

# Install/update dependencies if needed
echo "📦 Checking backend dependencies..."
pip install -q -r requirements.txt

echo "🚀 Starting backend server on http://localhost:8000"
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000 > /dev/null; then
        echo "✅ Backend is running!"
        break
    fi
    sleep 1
done

# Check if frontend directory exists
if [ ! -d "metra-ai-factory-main" ]; then
    echo "❌ Frontend directory not found!"
    kill $BACKEND_PID
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend..."
cd metra-ai-factory-main

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "🚀 Starting frontend server on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

echo ""
echo "✅ Metra AI is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Backend:  http://localhost:8000"
echo "🔧 API Docs: http://localhost:8000/docs"
echo "🎨 Frontend: http://localhost:5173"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Test account:"
echo "   Email: jzhe614@gmail.com"
echo "   Password: Jz061407"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait 