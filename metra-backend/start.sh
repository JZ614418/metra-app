#!/bin/bash

# 等待数据库准备就绪
echo "Waiting for database..."
sleep 5

# 运行数据库迁移
echo "Running database migrations..."
cd /app/metra-backend
python -m alembic upgrade head || echo "Migration failed, but continuing..."

# 启动应用
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 