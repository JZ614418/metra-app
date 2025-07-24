# Metra 技术架构文档

## 🏗️ 整体架构

Metra采用现代化的前后端分离架构，集成AI智能判断系统，实现端到端的AI模型训练平台。

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │  External APIs  │
│  React + TS     │◄──►│   FastAPI        │◄──►│   AI Services   │
│                 │    │   + Python       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎯 核心模块

### **1. Task Builder (任务构建器)**
**文件**: `src/components/TaskBuilder.tsx`
- 对话式任务定义界面
- 智能字段提取和验证
- 支持多种AI任务类型

### **2. Model Recommendations (模型推荐)**
**文件**: `src/components/ModelRecommend.tsx`, `app/api/v1/endpoints/recommendations.py`
- AI驱动的模型推荐算法
- 基于任务特征匹配最佳模型
- 实时性能预估

### **3. Data Builder (数据构建器)**
**文件**: `src/components/DataBuilder.tsx`, `app/api/v1/endpoints/data_collection.py`

#### 数据收集策略:
```python
# AI增强的数据收集
class DataCollectionService:
    async def collect_data_for_task(self, task_type, description):
        # 1. AI策略优化
        ai_strategy = await ai_judge_service.optimize_data_collection_strategy()
        
        # 2. 多源数据收集
        - Google Custom Search
        - Serper API
        - ScrapingBee (智能合法性判断)
        - OpenAI数据生成
        
        # 3. 实时进度跟踪
        return processed_data
```

### **4. DFE Engine (数据字段引擎)**
**文件**: `src/components/DataEngine.tsx`, `app/services/dfe_service.py`

#### 数据处理管道:
```python
class DFEService:
    async def process_data(self, raw_data, task_info):
        # 1. 字段对齐
        aligned_data = self._align_fields(raw_data, task_info)
        
        # 2. 数据清洗
        clean_data = self._clean_data(aligned_data)
        
        # 3. 质量验证
        validated_data = self._validate_quality(clean_data)
        
        return validated_data
```

### **5. Model Builder (模型构建器)**
**文件**: `src/components/ModelBuilder.tsx`, `app/services/training_service.py`

#### AI增强训练流程:
```python
class TrainingService:
    async def start_training(self, task_name, base_model, training_data):
        # 1. AI模型推荐
        ai_recommendation = await ai_judge_service.recommend_best_replicate_model()
        
        # 2. 训练参数优化
        optimized_config = ai_recommendation['training_config']
        
        # 3. Replicate云训练
        prediction = replicate_client.predictions.create()
        
        # 4. 实时监控
        return training_result
```

### **6. Model Deployment (模型部署)**
**文件**: `src/components/DeployedModels.tsx`, `app/services/deployment_service.py`
- REST API端点生成
- Web Widget嵌入代码
- 模型导出（ONNX、PyTorch等）

## 🤖 AI增强系统

### **核心创新: AIJudgeService**
**文件**: `app/services/ai_judge_service.py`

```python
class AIJudgeService:
    async def judge_website_legality(self, url):
        """AI智能判断网站爬取合法性"""
        # GPT-4分析: 法律合规、网站性质、商业风险
        # 返回: 评分0-100、可爬取建议、详细理由
        
    async def recommend_best_replicate_model(self, task_description, data_sample):
        """AI智能推荐最佳Replicate模型"""
        # 分析任务特征、数据样本、语言需求
        # 返回: 推荐模型、版本ID、训练配置
        
    async def optimize_data_collection_strategy(self, task_description):
        """AI优化数据收集策略"""
        # 生成搜索查询、推荐数据源、数据增强建议
        # 返回: 优化策略、目标数据量、质量要求
```

## 🔧 技术栈详情

### **前端技术栈**
```typescript
// 核心框架
React 18 + TypeScript + Vite

// UI组件库
Tailwind CSS + shadcn/ui

// 状态管理
Zustand (轻量级状态管理)

// 路由
React Router v6

// API客户端
Axios + 自定义API封装
```

### **后端技术栈**
```python
# Web框架
FastAPI (异步高性能)

# 数据库
Supabase (PostgreSQL云服务)

# 认证
JWT Token + bcrypt密码加密

# 异步处理
asyncio + aiohttp

# AI集成
OpenAI API + Replicate API
```

## 🔗 数据流设计

### **完整训练流程数据流**
```
1. 用户输入 → TaskBuilder → 任务定义JSON
   ↓
2. 任务定义 → ModelRecommend → AI推荐模型
   ↓
3. 模型+任务 → DataBuilder → 数据收集策略
   ↓
4. 收集策略 → DataCollection → 原始数据
   ↓
5. 原始数据 → DFE Engine → 清洗后数据
   ↓
6. 训练数据 → ModelBuilder → 训练任务
   ↓
7. 训练完成 → Deployment → 可用模型
```

### **API设计模式**
```python
# 统一响应格式
{
    "status": "success|error",
    "message": "描述信息",
    "data": {...},
    "job_id": "任务ID",
    "progress": 0-100
}

# 异步任务处理
POST /api/v1/data-collection/web-scraping
→ 返回job_id，开始后台任务

GET /api/v1/data-collection/job/{job_id}
→ 返回任务状态和进度

# 实时更新机制
WebSocket连接 (规划中)
或定期轮询状态更新
```

## 🔐 安全设计

### **API安全**
- JWT Token认证
- CORS跨域控制
- 速率限制 (规划中)
- 输入验证和消毒

### **数据安全**
- 用户数据隔离
- 敏感信息加密存储
- API密钥环境变量管理
- 临时文件自动清理

### **AI判断安全**
- 网站合法性AI评估
- 版权风险智能识别
- robots.txt自动检查
- 公平使用原则遵循

## 🚀 性能优化

### **前端优化**
```typescript
// 代码分割
const DataBuilder = lazy(() => import('./DataBuilder'))

// 状态缓存
const useDataCache = () => {
    const [cache, setCache] = useState(new Map())
    // 智能缓存策略
}

// 虚拟滚动 (大数据量)
// 防抖搜索
// 图片懒加载
```

### **后端优化**
```python
# 异步并发
async def collect_multiple_sources():
    tasks = [
        google_search(query),
        serper_search(query),
        ai_generation(description)
    ]
    results = await asyncio.gather(*tasks)

# 连接池管理
httpx.AsyncClient(limits=httpx.Limits(max_connections=100))

# 缓存策略
@lru_cache(maxsize=1000)
def ai_judgment_cache(url_hash):
    # AI判断结果缓存
```

## 📊 监控与日志

### **应用监控**
- FastAPI内置metrics
- 用户行为分析 (规划中)
- 错误追踪和报警
- 性能瓶颈识别

### **训练监控**
- Replicate训练进度实时同步
- 资源使用情况追踪
- 成本预估和控制
- 模型性能指标收集

## 🔮 扩展性设计

### **模块化架构**
- 服务松耦合设计
- 插件式扩展机制
- 多云服务支持
- 国际化准备

### **未来扩展点**
- 图像/视频模型训练
- 更多云训练平台集成
- 模型市场功能
- 企业级权限管理

---

**Metra的架构设计核心理念：用AI的智能化决策能力解决传统AI训练平台的复杂性问题** 🤖✨