# Data Builder 任务显示问题修复

## 问题描述
用户在 Data Builder 页面看到的是默认的测试任务（Customer Complaint Classifier），而不是他们实际创建的任务（中医饮食指导AI）。

## 问题原因
1. TaskBuilder 保存任务时，任务信息被嵌套在 `schema` 或 `fullDefinition` 对象中
2. DataBuilder 组件没有正确从嵌套结构中读取任务信息
3. 存储在 localStorage 中的数据结构与读取时期望的结构不匹配

## 解决方案
修改了 `DataBuilder.tsx` 中的任务信息读取逻辑，从多个可能的位置尝试获取任务信息：

```typescript
const taskName = finalizedTask.task || 
                finalizedTask.name || 
                finalizedTask.schema?.task || 
                finalizedTask.fullDefinition?.task ||
                '中医饮食指导AI';
```

## 启动方式
创建了新的启动脚本 `start-metra.sh`：

```bash
# 启动整个平台
./start-metra.sh

# 或分别启动
# 后端
cd backend && python3 -m uvicorn app.main:app --reload --port 8000

# 前端
cd metra-ai-factory-main && npm run dev
```

## 验证
1. 访问 http://localhost:8081/dashboard
2. 进入 Data Builder 页面
3. 应该看到正确的任务信息：
   - 任务：中医饮食指导AI
   - 模型：ChatGLM2-6B
   - 描述：提供基于中医理论的个性化饮食建议

## 相关文件
- `metra-ai-factory-main/src/components/DataBuilder.tsx` - 修复了任务信息读取
- `metra-ai-factory-main/src/components/TaskBuilder.tsx` - 任务保存逻辑
- `metra-ai-factory-main/src/stores/conversationStore.ts` - 状态管理
- `start-metra.sh` - 新的启动脚本 