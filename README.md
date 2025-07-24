# Metra AI Training Platform

**用AI解决AI训练中的所有问题** 🤖

Metra是一个革命性的无代码AI模型训练平台，集成了AI智能判断系统，让任何人都能轻松创建、训练和部署自定义AI模型。

## 🚀 核心特性

### **AI增强的智能平台** 🤖
- **AI智能白名单判断**: GPT-4自动分析网站爬取合法性
- **AI智能模型推荐**: 根据任务自动选择最佳Replicate模型版本
- **AI数据收集优化**: 智能生成搜索策略和数据收集建议
- **AI训练参数调优**: 自动优化训练配置，提升模型效果

### **完整的训练流程** 📊
1. **Task Builder** - 对话式任务定义，智能理解用户需求
2. **Model Recommendations** - AI驱动的模型推荐系统
3. **Data Builder** - 多源数据收集（Web搜索、AI生成、文件上传）
4. **DFE Engine** - 数据字段引擎，自动处理和清洗数据
5. **Model Builder** - 云端GPU训练（Replicate集成）
6. **Model Deployment** - 一键部署（API、Widget、导出）

### **多源数据收集** 🔍
- **智能网页爬取**: Google Search + ScrapingBee + AI合法性判断
- **AI数据生成**: OpenAI GPT-4批量生成训练数据
- **文件上传支持**: CSV、JSON、Excel等格式
- **实时进度跟踪**: 可视化数据收集进度

### **云端训练集成** 🏋️
- **Replicate GPU**: 高性能云端训练
- **多模型支持**: Llama-2、Mistral、Code-Llama等
- **训练模式**: 轻量/标准/深度三种模式
- **实时监控**: 训练进度、日志、指标可视化

## 🛠️ 技术架构

### **后端 (FastAPI + Python)**
```
app/
├── api/v1/endpoints/     # API端点
│   ├── auth.py          # 用户认证
│   ├── data_collection.py # 数据收集
│   ├── training.py      # 模型训练
│   ├── deployment.py    # 模型部署
│   └── ...
├── services/            # 核心服务
│   ├── ai_judge_service.py    # 🆕 AI智能判断
│   ├── data_collection.py    # 数据收集服务
│   ├── training_service.py   # 训练服务
│   └── ...
└── core/
    └── config.py        # 配置管理
```

### **前端 (React + TypeScript)**
```
src/
├── components/          # 核心组件
│   ├── TaskBuilder.tsx  # 任务构建器
│   ├── DataBuilder.tsx  # 数据构建器  
│   ├── ModelBuilder.tsx # 模型构建器
│   └── ...
├── pages/              # 页面
│   ├── Dashboard.tsx   # 主控制台
│   └── ...
└── lib/
    └── api.ts          # API客户端
```

## 🔧 集成服务

### **AI & 数据服务**
- **OpenAI GPT-4**: AI判断、数据生成、模型推荐
- **Google Custom Search**: 网页搜索
- **Serper API**: 备用搜索服务
- **ScrapingBee**: 合法网页内容抓取

### **训练 & 部署**
- **Replicate**: GPU云训练平台
- **Supabase**: 云数据库
- **Hugging Face**: 模型托管（可选）

## ⚠️ Python版本要求

**重要**: 由于AI相关包的兼容性，推荐使用Python 3.11而非Python 3.13。

详细设置指南请参考: [PYTHON_SETUP_GUIDE.md](./PYTHON_SETUP_GUIDE.md)

## 📊 数据流程

```
Task Definition → Model Recommendation → Data Collection → DFE Processing → Model Training → Deployment
       ↓                    ↓                 ↓              ↓             ↓           ↓
   AI理解任务      →    AI推荐模型    →    AI收集数据   →   自动处理    →   GPU训练   →   一键部署
```

## 🚀 快速开始

### **1. 环境要求**
- Node.js 18+
- **Python 3.11** (推荐，避免AI包兼容性问题)
- API密钥：OpenAI、Google、Replicate等

### **2. Python环境设置**
```bash
# 使用pyenv安装Python 3.11
pyenv install 3.11.13
pyenv local 3.11.13

# 创建虚拟环境
python -m venv venv
source venv/bin/activate
```

### **3. 启动后端**
```bash
cd backend
source ../venv/bin/activate
pip install -r requirements_full.txt
uvicorn app.main:app --reload --port 8000
```

### **4. 启动前端**
```bash
cd metra-ai-factory-main
npm install
npm run dev
```

### **5. 访问应用**
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 🔑 API密钥配置

创建 `backend/.env` 文件：
```env
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
GOOGLE_CX_ID=your_cx_id
REPLICATE_API_TOKEN=your_replicate_token
SCRAPINGBEE_API_KEY=your_scrapingbee_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
```

## 🎯 核心创新

### **AI驱动的智能决策**
Metra的最大创新是用AI解决AI训练过程中的决策问题：

1. **合法性AI判断**: 不再依赖固定白名单，AI动态分析网站爬取合法性
2. **模型选择AI**: 根据任务特点、数据样本自动推荐最佳模型
3. **数据策略AI**: 智能优化数据收集策略和搜索查询
4. **参数调优AI**: 自动选择最优训练参数

### **通用化平台**
- 支持任何领域：科技、教育、医疗、金融、娱乐等
- 支持任何任务：问答、分类、生成、翻译、摘要等
- 支持任何语言：中文、英文、多语言混合训练

## 📈 平台优势

### **vs 传统AI训练平台**
- ❌ 传统：需要编程技能、复杂配置
- ✅ Metra：无代码、对话式操作

### **vs 现有无代码平台**
- ❌ 现有：固定模板、有限数据源
- ✅ Metra：AI驱动、智能决策、无限可能

### **vs 手动训练流程**
- ❌ 手动：费时费力、容易出错
- ✅ Metra：全自动化、AI优化、高成功率

## 🔮 未来规划

- **多模态支持**: 图像、视频、音频训练
- **模型市场**: 用户模型分享和交易
- **企业版本**: 私有部署、高级权限管理
- **API生态**: 第三方集成和插件系统

## 📞 联系方式

- **项目地址**: https://github.com/your-org/metra
- **演示地址**: https://metratraining.com
- **文档地址**: https://docs.metratraining.com

---

**Metra - 让AI训练变得像聊天一样简单** 🚀✨