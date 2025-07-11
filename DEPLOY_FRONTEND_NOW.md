# 🚀 立即部署前端到Vercel

## 快速部署步骤（5分钟完成）

### 方法1：使用Vercel网页界面（推荐）

1. **访问 Vercel**
   - 打开 https://vercel.com
   - 登录您的账户

2. **创建新项目**
   - 点击 "New Project"
   - 如果之前已经导入过，选择已有的项目

3. **配置项目**
   - **Root Directory**: `metra-ai-factory-main`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. **设置环境变量**（最重要！）
   在 Environment Variables 部分添加：
   ```
   VITE_API_URL = https://metra-backend-production.up.railway.app/api/v1
   ```

5. **点击 Deploy**

### 方法2：使用命令行（快速）

```bash
# 在项目根目录
cd metra-ai-factory-main

# 安装Vercel CLI（如果还没有）
npm i -g vercel

# 登录
vercel login

# 部署
vercel --prod
```

当提示时：
- Set up and deploy: `Y`
- Which scope: 选择您的账户
- Link to existing project?: `N`（如果是首次）
- Project name: `metra-ai-factory`
- In which directory: `./`
- Override settings?: `N`

### 部署后验证

1. **获取部署URL**
   - Vercel会提供一个URL，类似：`https://metra-ai-factory.vercel.app`

2. **测试功能**
   - 访问部署的URL
   - 使用测试账号登录：
     - Email: jzhe614@gmail.com
     - Password: Jz061407

3. **检查API连接**
   - 打开浏览器开发者工具（F12）
   - 查看Network标签
   - 确认API请求发送到Railway后端

## 🎯 部署成功后

您将获得：
- 生产环境URL：`https://metra-ai-factory.vercel.app`
- 可以分享给用户测试
- 所有功能都可正常使用

## 🔧 如果遇到问题

1. **CORS错误**：后端已配置，应该没问题
2. **API连接失败**：检查环境变量是否正确设置
3. **构建失败**：运行 `npm install` 后重试

## 📱 邀请用户

部署成功后，您可以：
1. 分享部署的URL给测试用户
2. 让他们注册新账号或使用测试账号
3. 收集反馈并优化

准备好了吗？让我们开始部署！ 