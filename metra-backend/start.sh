#!/bin/bash

# 等待数据库准备就绪
echo "Waiting for database..."
sleep 5

# 【临时方案】清空数据库
echo "Dropping all tables..."
python -c 'from app.db.base import Base; from app.db.init_db import engine; import asyncio; async def main(): async with engine.begin() as conn: await conn.run_sync(Base.metadata.drop_all); asyncio.run(main())' || echo "Dropping tables failed, but continuing..."


# 运行数据库迁移
echo "Running database migrations..."
cd /app/metra-backend
python -m alembic upgrade head || echo "Migration failed, but continuing..."

# 启动应用
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 