#!/bin/bash

echo "修复 Vercel 部署..."

cd metra-ai-factory-main

# 1. 创建正确的 vercel.json
cat > vercel.json << EOF
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
EOF

# 2. 创建 .env.production 文件
cat > .env.production << EOF
VITE_API_URL=https://metra-backend-production.up.railway.app/api/v1
EOF

echo "文件已创建。现在你需要："
echo "1. 在 Vercel 仪表板中设置环境变量 VITE_API_URL"
echo "2. 手动部署或等待自动部署"
echo ""
echo "或者使用 Vercel CLI："
echo "vercel --prod" 