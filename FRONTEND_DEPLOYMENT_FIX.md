# 前端登录问题修复指南

## 问题原因
前端还在使用默认的 localhost API URL，需要更新为 Railway 的生产环境 URL。

## 解决方案

### 方案 1：在 Vercel 设置环境变量（推荐）

1. 登录 Vercel 控制台：https://vercel.com/dashboard
2. 找到你的 Metra 项目
3. 进入 Settings -> Environment Variables
4. 添加新的环境变量：
   - Key: `VITE_API_URL`
   - Value: `https://metra-backend-production.up.railway.app/api/v1`
   - Environment: Production
5. 重新部署项目

### 方案 2：临时修复（快速测试）

在本地修改 `metra-ai-factory-main/src/lib/api.ts` 文件：

```typescript
// 将这行：
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// 改为：
const API_URL = import.meta.env.VITE_API_URL || 'https://metra-backend-production.up.railway.app/api/v1'
```

然后重新部署到 Vercel。

### 方案 3：使用 Vercel CLI

```bash
# 安装 Vercel CLI
npm i -g vercel

# 在项目目录中
cd metra-ai-factory-main

# 设置环境变量并部署
vercel env add VITE_API_URL production
# 输入: https://metra-backend-production.up.railway.app/api/v1

# 重新部署
vercel --prod
```

## 验证修复

修复后，你应该能够：
1. 成功登录（使用 jzhe614@gmail.com / Jz061407）
2. 在浏览器开发者工具的 Network 标签中看到请求发送到 Railway URL
3. 成功进入 Dashboard

## 注意事项

- 确保 CORS 已经正确配置（后端已经配置了 metratraining.com）
- 如果仍有问题，检查浏览器控制台的错误信息 