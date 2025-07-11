# Metra Language Model Platform - Project Overview

## 🎯 项目状态

**当前版本**: v1.0 MVP (Language Model Training Platform)
**产品定位**: 专注于语言模型的训练平台，支持文本生成、分类、NER、Q&A等NLP任务
**开发阶段**: 核心功能已实现（任务定义、模型推荐、数据构建）
**预计完成时间**: 训练和部署模块待开发（1-2个月）

## 📁 项目结构

```
Metra/
├── 📄 文档
│   ├── Metra_PRD.md              # 产品需求文档 v4.0
│   ├── Metra_Guideline.md        # 开发指南 v4.0
│   ├── Metra_Tech_Requirements.md # 技术需求和 API Keys
│   ├── Metra_Development_Manual.md # 完整开发手册
│   └── tech_requirements_checklist.md # 技术配置检查清单
│
├── 🎨 前端项目 (metra-ai-factory-main/)
│   ├── src/
│   │   ├── components/           # UI 组件
│   │   ├── pages/               # 页面组件
│   │   └── lib/                 # 工具函数
│   ├── package.json             # 依赖配置
│   └── .env.example             # 环境变量示例
│
├── 🔧 后端项目 (metra-backend/)
│   ├── app/
│   │   ├── api/v1/              # API 端点
│   │   ├── core/                # 核心配置
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务逻辑
│   │   └── tasks/               # 异步任务
│   ├── requirements.txt         # Python 依赖
│   └── example.env              # 环境变量示例
│
└── 🛠 开发工具
    ├── setup-dev.sh             # 一键环境设置脚本
    ├── start-backend.sh         # 启动后端脚本
    ├── start-frontend.sh        # 启动前端脚本
    └── start-inngest.sh         # 启动任务队列脚本
```

## ✅ 已完成的工作

### 基础设施
- [x] 项目目录结构创建
- [x] 前后端项目初始化
- [x] 开发环境配置文件
- [x] 技术栈选型和配置
- [x] API Keys 整理（大部分已获取）

### 后端
- [x] FastAPI 应用框架搭建
- [x] 数据库连接配置 (Supabase)
- [x] Redis 缓存配置 (Upstash)
- [x] Inngest 任务队列集成
- [x] 基础认证端点
- [x] 错误监控 (Sentry)

### 前端
- [x] React + TypeScript 项目结构
- [x] UI 组件库 (shadcn/ui)
- [x] 路由配置
- [x] 基础页面组件
- [x] 响应式设计

### 文档
- [x] PRD v4.0 (产品需求文档)
- [x] Guideline v4.0 (开发指南)
- [x] 技术需求清单
- [x] 完整开发手册
- [x] 环境配置说明

## 🚧 待开发功能（按优先级）

### ✅ 已完成功能
- [x] **用户系统** - JWT认证、用户注册登录、邮件服务（Resend）
- [x] **Task Definition** - 通过对话定义NLP任务，包含数据量需求和时间估算
- [x] **Model Selection** - 智能推荐语言模型（GPT、BERT、T5、ChatGLM等）
- [x] **Data Builder** - 文本数据收集（优化版）
  - Google Search：无限额！大量高质量数据 🚀
  - Web爬虫：~21个样本/秒（Wikipedia、arXiv、PubMed）
  - AI生成：~8个样本/秒（OpenAI GPT-3.5）
  - 文件上传：支持CSV、JSON、TXT等格式
  - 智能策略：优先使用快速的Web爬取
  - 实际测试时间（Google无限额）：
    - 1,000条：~5分钟 ⚡
    - 5,000条：~20分钟 ☕
    - 10,000条：~40分钟 🍕
    - 50,000条：~3-4小时
    - 100,000条：~6-8小时

### P0 - 语言模型训练（第1-2周）
- [ ] Replicate API 集成用于模型训练
- [ ] LoRA微调实现
- [ ] 训练参数自动优化
- [ ] 训练进度实时监控
- [ ] Loss曲线可视化

### P1 - 模型评估与测试（第2周）
- [ ] 文本生成质量评估
- [ ] 分类准确率测试
- [ ] 混淆矩阵展示
- [ ] 样本测试界面

### P2 - 模型部署（第3周）
- [ ] REST API自动生成
- [ ] 流式文本生成支持
- [ ] API文档生成
- [ ] 使用示例代码
- [ ] 速率限制配置

### P3 - 高级语言模型功能（第4周）
- [ ] Prompt模板管理
- [ ] Few-shot学习支持
- [ ] 多轮对话优化
- [ ] 上下文长度管理

### P4 - DFE 引擎（第4-5周）
- [ ] 语义字段对齐
- [ ] 缺失值处理
- [ ] 数据格式转换
- [ ] 可视化编辑器

### P5 - 训练管理（第5-6周）
- [ ] Replicate API 集成
- [ ] 训练进度监控
- [ ] 训练结果展示
- [ ] 模型性能分析

### P6 - 模型部署（第6-7周）
- [ ] API 端点生成
- [ ] 模型导出功能
- [ ] 使用文档生成
- [ ] 调用统计

### P7 - 社区功能（第7-8周）
- [ ] 模型市场 MVP
- [ ] 模型上架流程
- [ ] 评论和评分
- [ ] 模型复刻

## 🔑 重要配置

### 已配置的 API Keys
- ✅ OpenAI (GPT-4, Embeddings)
- ✅ Supabase (Database, Auth, Storage)
- ✅ Replicate (Model Training)
- ✅ ScrapingBee (Web Scraping)
- ✅ Hugging Face (Model Catalog)
- ✅ Upstash Redis (Caching)
- ✅ Sentry (Monitoring)
- ✅ Cloudflare (CDN)
- ✅ Inngest (Task Queue)
- ✅ Vercel (Frontend Deployment)
- ✅ Railway (Backend Deployment)

### 待配置
- ✅ Resend (Email) - 已配置并测试成功
- ⚠️ Paddle (Payment) - v2.0 再集成

## 🚀 快速开始

1. **克隆项目并进入目录**
   ```bash
   cd /Users/jz/Desktop/Metra
   ```

2. **运行环境设置脚本**
   ```bash
   ./setup-dev.sh
   ```

3. **启动开发服务器**（需要3个终端）
   ```bash
   # Terminal 1 - Backend
   ./start-backend.sh
   
   # Terminal 2 - Frontend
   ./start-frontend.sh
   
   # Terminal 3 - Inngest
   ./start-inngest.sh
   ```

4. **访问应用**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Inngest Dashboard: http://localhost:8288

## 📝 开发规范

- **Git 分支**: main (生产), develop (开发), feature/* (功能)
- **提交格式**: feat/fix/docs/style/refactor/test/chore: description
- **代码风格**: ESLint + Prettier (前端), Black + Flake8 (后端)
- **测试要求**: 单元测试覆盖率 > 80%

## 🤝 交接说明

本项目已完成基础架构搭建，所有配置文件和开发环境已准备就绪。新接手的工程师可以：

1. 阅读 `Metra_Development_Manual.md` 了解完整技术细节
2. 运行 `./setup-dev.sh` 快速搭建开发环境
3. 查看 `PROJECT_OVERVIEW.md`（本文档）了解项目状态
4. 按照待开发功能列表逐步实现各模块

祝开发顺利！🎉 