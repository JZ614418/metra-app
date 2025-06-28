#!/bin/bash

# 等待数据库准备就绪
echo "Waiting for database..."
sleep 5

# 修复 alembic 版本表
echo "Fixing alembic version table..."
cd /app/metra-backend
python fix_alembic.py || echo "Fix alembic failed, but continuing..."

# 运行数据库迁移
echo "Running database migrations..."
python -m alembic upgrade head || echo "Migration failed, but continuing..."

# 启动应用
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 