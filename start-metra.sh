#!/bin/bash

echo "Starting Metra AI Platform..."

# Get the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Start backend
echo "Starting backend..."
cd backend
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
else
    echo "Virtual environment not found, using system Python..."
fi

python3 -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Start frontend
echo "Starting frontend..."
cd ../metra-ai-factory-main
npm run dev &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo ""
echo "✅ Metra AI Platform is running!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:8081"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait 