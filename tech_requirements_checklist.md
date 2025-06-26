# Metra 技术需求配置状态检查

> 最后更新：2025-01-25
> 状态说明：✅ 已配置 | ⚠️ 部分配置 | ❌ 未配置 | 🔄 待确认

## 📋 必需服务配置状态

### 1. OpenAI Services ✅
**状态**：已在后端配置  
**配置位置**：`metra-backend/app/core/config.py`  
```python
OPENAI_API_KEY: Optional[str] = None  # ✅ 已定义，需填写实际值
```
**待办**：
- [ ] 在 `.env` 文件中填写实际的 API Key
- [ ] 设置使用限额防止超支

---

### 2. Hugging Face ✅
**状态**：已在后端配置  
**配置位置**：`metra-backend/app/core/config.py`  
```python
HUGGINGFACE_TOKEN: Optional[str] = None  # ✅ 已定义，需填写实际值
```
**待办**：
- [ ] 在 `.env` 文件中填写实际的 Token

---

### 3. Replicate ✅
**状态**：已在后端配置  
**配置位置**：`metra-backend/app/core/config.py`  
```python
REPLICATE_API_TOKEN: Optional[str] = None  # ✅ 已定义，需填写实际值
```
**待办**：
- [ ] 在 `.env` 文件中填写实际的 API Token
- [ ] 配置训练任务的具体模型参数

---

### 4. ScrapingBee ✅
**状态**：已在后端配置  
**配置位置**：`metra-backend/app/core/config.py`  
```python
SCRAPINGBEE_API_KEY: Optional[str] = None  # ✅ 已定义，需填写实际值
```
**待办**：
- [ ] 在 `.env` 文件中填写实际的 API Key
- [ ] 实现数据采集的具体逻辑

---

### 5. Supabase ✅
**状态**：已在后端配置  
**配置位置**：`metra-backend/app/core/config.py`  
```python
SUPABASE_URL: Optional[str] = None
SUPABASE_ANON_KEY: Optional[str] = None
SUPABASE_SERVICE_KEY: Optional[str] = None
```
**待办**：
- [ ] 在 `.env` 文件中填写实际的配置值
- [ ] 创建数据库表结构
- [ ] 配置 RLS 策略
- [ ] 设置向量搜索功能

---

### 6. Paddle（支付解决方案）❌
**状态**：未配置  
**原因**：决定先发布免费版本  
**待办**：
- [ ] 后续版本添加 Paddle 集成
- [ ] 在 `config.py` 中添加 Paddle 配置项
- [ ] 实现订阅管理功能

---

### 7. Vercel ✅
**状态**：已获取部署 Token  
**配置值**：`VERCEL_TOKEN: "GdHIt4IcuTepKpynkNoT32sb"`  
**说明**：前端部署服务  
**待办**：
- [ ] 连接 GitHub 仓库
- [ ] 在 Vercel 仪表板配置环境变量
- [ ] 配置自定义域名

---

### 8. Cloudflare 🔄
**状态**：域名已注册（metratrainning.com）  
**待办**：
- [ ] 配置 DNS 记录
- [ ] 启用 CDN
- [ ] 配置安全规则

---

### 9. AWS ❌
**状态**：未配置（可选服务）  
**说明**：初期使用 Supabase Storage 替代 S3

---

### 10. Sentry ✅
**状态**：已在后端配置  
**配置位置**：`metra-backend/app/core/config.py`  
```python
SENTRY_DSN: Optional[str] = None  # ✅ 已定义，需填写实际值
```
**待办**：
- [ ] 在 `.env` 文件中填写实际的 DSN
- [ ] 在前端项目中也配置 Sentry

---

### 11. Railway/Render ✅
**状态**：已获取 Railway Token  
**配置值**：`RAILWAY_TOKEN: "cdc044fd-f0f9-4350-b2c9-080d5d2d4cf3"`  
**说明**：后端部署服务（选择了 Railway）  
**待办**：
- [ ] 创建 railway.json 配置文件
- [ ] 配置环境变量
- [ ] 设置自动部署

---

### 12. Upstash Redis ✅
**状态**：已在后端配置  
**配置位置**：`metra-backend/app/core/config.py`  
```python
UPSTASH_REDIS_REST_URL: Optional[str] = None
UPSTASH_REDIS_REST_TOKEN: Optional[str] = None
```
**待办**：
- [ ] 在 `.env` 文件中填写实际的配置值
- [ ] 实现 Redis 缓存逻辑

---

### 13. Inngest ⚠️
**状态**：部分配置（已修正配置方式）  
**配置位置**：`metra-backend/app/tasks/inngest_app.py`  
```python
inngest_client = inngest.Inngest(
    app_id="metra-backend",
    is_production=settings.ENVIRONMENT == "production",
    logger=logging.getLogger("inngest")
)
```
**注意**：
- ✅ 开发环境不需要 Client ID
- ✅ 已创建示例任务函数
**待办**：
- [ ] 生产环境时配置 EVENT_KEY 和 SIGNING_KEY
- [ ] 实现实际的训练任务逻辑

---

### 14. Resend ✅
**状态**：已在后端配置  
**配置位置**：`metra-backend/app/core/config.py`  
```python
RESEND_API_KEY: Optional[str] = None
RESEND_FROM_EMAIL: str = "noreply@metratraining.com"
RESEND_FROM_NAME: str = "Metra"
```
**待办**：
- [ ] 在 `.env` 文件中填写实际的 API Key
- [ ] 验证域名邮箱
- [ ] 实现邮件发送功能

---

### 15. Handsontable ❌
**状态**：未配置  
**说明**：可先使用开源替代方案开发  
**待办**：
- [ ] 评估是否需要购买商业许可
- [ ] 或使用 AG-Grid 等开源替代

---

## 🔧 环境变量配置状态

### 后端环境变量
**文件**：`metra-backend/.env`（需创建）  
**模板**：
```bash
# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:password@localhost/metra_db
SUPABASE_URL=https://lcoxwbeeuukryxtdfljc.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Redis
UPSTASH_REDIS_REST_URL=https://bright-monkfish-52619.upstash.io
UPSTASH_REDIS_REST_TOKEN=Ac2LAAIjcDE...

# AI Services
OPENAI_API_KEY=sk-proj-8Sgm83QCQ...
HUGGINGFACE_TOKEN=hf_RysCcgRMRW...
REPLICATE_API_TOKEN=r8_XjoDGKFB4TV...
SCRAPINGBEE_API_KEY=POZ62WX2FEH3EFD9...

# Inngest (开发环境)
INNGEST_DEV=1

# Email
RESEND_API_KEY=re_...

# Monitoring
SENTRY_DSN=https://b6a7f1329a8c6e4c...

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### 前端环境变量
**文件**：`metra-ai-factory-main/.env`（需创建）  
**模板**：
```bash
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://lcoxwbeeuukryxtdfljc.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## ✅ 准备状态总结

### 已配置的服务（后端定义）
1. ✅ OpenAI - 需填写 API Key
2. ✅ Hugging Face - 需填写 Token
3. ✅ Replicate - 需填写 API Token
4. ✅ ScrapingBee - 需填写 API Key
5. ✅ Supabase - 需填写所有配置
6. ✅ Upstash Redis - 需填写配置
7. ✅ Inngest - 开发环境已配置
8. ✅ Resend - 需填写 API Key
9. ✅ Sentry - 需填写 DSN

### 未配置但不影响开发
1. ❌ Paddle - 先发布免费版
2. ❌ AWS - 使用 Supabase Storage 替代
3. ❌ Handsontable - 使用开源替代

### 部署时配置
1. 🔄 Vercel - 前端部署
2. 🔄 Railway/Render - 后端部署
3. 🔄 Cloudflare - DNS 和 CDN

---

## 🚀 下一步行动

### 立即需要：
1. **创建 `.env` 文件**：
   ```bash
   cd metra-backend
   cp .env.example .env  # 如果有模板
   # 填写所有必需的 API Keys
   ```

2. **验证配置**：
   ```bash
   # 启动后端测试配置
   cd metra-backend
   uvicorn app.main:app --reload
   ```

3. **测试关键服务**：
   - [ ] OpenAI API 连接
   - [ ] Supabase 数据库连接
   - [ ] Redis 缓存连接

### 开发阶段：
1. 使用提供的 API Keys 填写环境变量
2. 先专注于核心功能开发
3. 支付功能延后到 v2

### 部署前：
1. 选择并配置托管服务
2. 设置生产环境变量
3. 配置监控和日志

**大部分服务已在代码层面准备就绪，只需填写实际的 API Keys 即可开始开发！** 