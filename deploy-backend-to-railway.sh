#!/bin/bash

echo "🚀 部署Metra后端到Railway"
echo "========================"

# 项目信息
PROJECT_ID="d61bc1c7-1eee-4ecc-a057-ab4f8c1ed0d5"
SERVICE_ID="99627b70-4cfa-443b-826c-b11f903badd6"
ENV_ID="39d9c434-dca6-4389-9fff-9584cbbc9c6c"

echo "1. 准备部署文件..."

# 创建临时部署目录
rm -rf deploy-temp
mkdir -p deploy-temp

# 复制后端代码
cp -r backend/* deploy-temp/
cd deploy-temp

# 确保requirements.txt是最新的
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.22.0
watchfiles==0.19.0
websockets==11.0.3
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
email-validator==2.1.0
pydantic>=2.0,<3.0
pydantic-settings>=2.0,<3.0
alembic==1.12.1
openai==1.93.0
huggingface_hub==0.25.0
httpx==0.25.2
requests==2.31.0
beautifulsoup4==4.12.2
resend==0.7.0
trafilatura==1.6.1
replicate==0.25.1
EOF

# 创建runtime.txt指定Python版本
echo "python-3.10" > runtime.txt

# 创建railway.json
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "nixpacksPlan": {
      "providers": ["python"],
      "phases": {
        "setup": {
          "aptPkgs": ["libpq-dev"]
        }
      }
    }
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

echo "2. 初始化Git仓库..."
git init -q
git add .
git commit -m "Deploy Metra backend to Railway" -q

echo "3. 推送到Railway..."
echo "请访问Railway项目页面，使用GitHub连接或Railway CLI部署"
echo ""
echo "项目ID: $PROJECT_ID"
echo "服务ID: $SERVICE_ID"
echo ""
echo "或者使用Railway CLI:"
echo "railway link $PROJECT_ID"
echo "railway up"

cd ..
echo ""
echo "✅ 部署准备完成！"
echo "📁 部署文件在: deploy-temp/" 