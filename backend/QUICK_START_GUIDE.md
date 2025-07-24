# Metra AI Factory - 快速启动指南

## 🚨 测试前必须执行的步骤

### 1. 初始化监控数据库表
```bash
cd /Users/jz/Desktop/Metra/backend
python3 init_monitoring_tables.py
```

### 2. 运行预检测试
```bash
python3 quick_test_checklist.py
```

### 3. 启动服务器
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 基本功能测试

### 健康检查
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/monitoring/health
```

### 测试数据收集流程
```bash
# 1. 启动DataBuilder任务
curl -X POST "http://localhost:8000/api/v1/data-builder-v3/start" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "medical",
    "task_type": "question_answering", 
    "target_samples": 10,
    "language": "chinese"
  }'

# 2. 查看任务状态 (替换TASK_ID)
curl http://localhost:8000/api/v1/data-builder-v3/task/TASK_ID/status

# 3. 从DataBuilder创建DFE任务 (替换TASK_ID) 
curl -X POST "http://localhost:8000/api/v1/dfe-v2/from-databuilder/TASK_ID"

# 4. 查看监控指标
curl http://localhost:8000/api/v1/monitoring/system/overview
```

## ⚠️ 已知需要注意的问题

### 1. 数据库表创建
- **必须先运行** `init_monitoring_tables.py`
- 如果跳过这步，监控功能会报错

### 2. 环境变量检查
确保以下变量已正确设置：
- `OPENAI_API_KEY` - OpenAI API密钥
- `REPLICATE_API_TOKEN` - Replicate训练服务密钥
- `DATABASE_URL` - 数据库连接地址

### 3. Google搜索配置 (可选)
如果要使用Google搜索增强数据收集：
```bash
export GOOGLE_SEARCH_API_KEY="your-google-api-key"
export GOOGLE_SEARCH_CX="your-search-engine-id"
```

## 🔍 故障排除

### 如果遇到导入错误：
```bash
pip install -r requirements.txt
```

### 如果数据库连接失败：
检查 `metra.db` 文件是否存在且可写

### 如果监控功能报错：
```bash
# 重新初始化监控表
python3 init_monitoring_tables.py
```

## 🎯 完整测试流程

1. **预检测试**: `python3 quick_test_checklist.py`
2. **启动服务**: `uvicorn app.main:app --reload`
3. **健康检查**: 访问健康端点
4. **数据收集**: 启动DataBuilder任务
5. **数据处理**: 使用DFE处理数据
6. **训练测试**: 启动训练任务
7. **监控验证**: 查看监控指标

## 📊 成功指标

如果看到以下结果，说明Metra运行正常：
- ✅ 所有健康检查返回 "healthy"
- ✅ DataBuilder可以收集数据样本
- ✅ DFE可以处理和清洗数据
- ✅ 监控系统显示实时指标
- ✅ Training服务可以连接Replicate

## 🎉 下一步

系统测试正常后，你可以：
1. 通过前端界面操作
2. 扩大数据收集规模
3. 测试端到端训练流程
4. 查看详细监控分析

---
*由Claude Code生成 - 确保Metra AI Factory可用性*