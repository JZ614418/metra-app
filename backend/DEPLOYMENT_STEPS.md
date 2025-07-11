# Render.com 部署步骤

## 1. 准备 GitHub 仓库

```bash
# 在 backend 目录
cd /Users/jz/Desktop/Metra/backend

# 初始化 Git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial backend for Render deployment"
```

## 2. 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 仓库名称：`metra-backend`
3. 设为 Private（如果需要）
4. 不要初始化 README（我们已经有了）

## 3. 推送代码

```bash
# 添加远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/metra-backend.git

# 推送
git branch -M main
git push -u origin main
```

## 4. 在 Render 部署

1. 访问 https://render.com
2. 点击 "New +" → "Web Service"
3. 连接 GitHub 账号
4. 选择 `metra-backend` 仓库
5. 设置：
   - Name: `metra-api`
   - Branch: `main`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

6. 环境变量（在 Environment 标签）：
   - 添加 `OPENAI_API_KEY` = 你的 OpenAI API Key

7. 点击 "Create Web Service"

## 5. 获取部署 URL

部署完成后，你会得到：
```
https://metra-api-xxxx.onrender.com
```

## 6. 更新前端配置

在前端代码中更新 API URL：

```typescript
// src/lib/api.ts
const API_URL = import.meta.env.VITE_API_URL || 'https://metra-api-xxxx.onrender.com';
```

## 7. 测试 API

```bash
# 测试健康检查
curl https://metra-api-xxxx.onrender.com/api/v1/health

# 测试文档
# 浏览器访问：https://metra-api-xxxx.onrender.com/docs
```

完成！🎉 