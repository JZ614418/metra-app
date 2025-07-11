# 部署 Metra 后端到 Supabase

## 快速部署步骤

### 1. 创建 Supabase 项目
1. 访问 [Supabase](https://supabase.com)
2. 创建新项目
3. 记录项目 URL 和 API Key

### 2. 使用 Vercel 部署后端
由于 Supabase Edge Functions 不适合完整的 FastAPI 应用，我们使用 Vercel：

```bash
# 安装 Vercel CLI
npm i -g vercel

# 在 backend 目录下
cd backend

# 创建 vercel.json
```

创建 `backend/vercel.json`:
```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

### 3. 部署
```bash
vercel --prod
```

### 4. 配置环境变量
在 Vercel 控制台设置：
- SECRET_KEY
- DATABASE_URL (使用 Supabase PostgreSQL URL)
- OPENAI_API_KEY
- BACKEND_CORS_ORIGINS
- PROJECT_NAME
- API_V1_STR

### 5. 更新前端 API URL
部署完成后，获取 Vercel URL，更新前端配置。 