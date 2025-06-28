#!/bin/bash

echo "Starting Metra Backend..."

# 启动应用
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 