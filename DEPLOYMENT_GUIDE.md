# Metra 部署指南

## 🎉 GitHub 仓库已创建
- 仓库地址：https://github.com/JZ614418/metra-app
- 状态：代码已推送成功（无敏感信息）

## 📋 下一步部署流程

### 1. 部署后端到 Railway

1. 访问 [Railway](https://railway.app)
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择 `JZ614418/metra-app` 仓库
5. 选择部署目录：`/metra-backend`
6. 添加环境变量（见下方列表）
7. 添加 PostgreSQL 数据库服务

### 2. 部署前端到 Vercel

1. 访问 [Vercel](https://vercel.com)
2. 点击 "New Project"
3. 导入 `JZ614418/metra-app` 仓库
4. 设置 Root Directory：`metra-ai-factory-main`
5. 添加环境变量：
   - `VITE_API_URL`: 从 Railway 获取的后端 URL
   - `VITE_SUPABASE_URL`: https://lcoxwbeeuukryxtdfljc.supabase.co
   - `VITE_SUPABASE_ANON_KEY`: [从你的文档中复制]

### 3. 配置域名

1. 在 Vercel 中添加自定义域名：`metratraining.com`
2. 在 Cloudflare 中添加 CNAME 记录指向 Vercel

## 🔐 Railway 环境变量配置

```env
# 基础配置
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=[生成一个随机密钥]

# 数据库 (Railway 自动提供)
DATABASE_URL=[Railway 自动生成]

# CORS
BACKEND_CORS_ORIGINS=["https://metratraining.com", "https://www.metratraining.com", "http://localhost:3000"]

# API Keys - 从你的 Metra_Tech_Requirements.md 文件复制
OPENAI_API_KEY=[你的密钥]
HUGGINGFACE_TOKEN=[你的密钥]
REPLICATE_API_TOKEN=[你的密钥]
SCRAPINGBEE_API_KEY=[你的密钥]

# Supabase
SUPABASE_URL=https://lcoxwbeeuukryxtdfljc.supabase.co
SUPABASE_ANON_KEY=[你的密钥]
SUPABASE_SERVICE_KEY=[你的密钥]

# Redis
UPSTASH_REDIS_REST_URL=https://bright-monkfish-52619.upstash.io
UPSTASH_REDIS_REST_TOKEN=[你的密钥]

# Email
RESEND_API_KEY=[你的密钥]
RESEND_FROM_EMAIL=noreply@metratraining.com
RESEND_FROM_NAME=Metra

# Cloudflare
CLOUDFLARE_API_TOKEN=[你的密钥]
CLOUDFLARE_ZONE_ID=72002a6ffe61b36e3bf206bae8d94f7d
CLOUDFLARE_ACCOUNT_ID=66a509c6d77d7eb871cfb30d03b6eec2

# Inngest
INNGEST_EVENT_KEY=[你的密钥]
INNGEST_SIGNING_KEY=[你的密钥]

# Sentry
SENTRY_DSN=[你的密钥]

# Free tier limits
FREE_MODELS_PER_MONTH=3
FREE_API_CALLS_PER_MONTH=1000
FREE_TRAINING_MINUTES_PER_MONTH=120
```

## 🚀 部署后检查清单

- [ ] 后端 API 文档可访问：`https://[railway-url]/docs`
- [ ] 前端可以正常访问
- [ ] 登录功能正常
- [ ] 数据库连接正常
- [ ] 环境变量都已配置

## 💡 提示

1. **密钥安全**：所有 API 密钥都在你的本地文档中，不在 GitHub 上
2. **数据库迁移**：Railway 部署后，可能需要运行数据库迁移
3. **监控**：使用 Railway 和 Vercel 的日志功能调试问题

## 🎯 预计时间

- Railway 部署：5-10 分钟
- Vercel 部署：3-5 分钟
- DNS 配置：5-30 分钟（等待生效）

需要我帮你自动化这个过程吗？ 