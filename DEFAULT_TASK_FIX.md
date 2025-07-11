# 默认任务显示问题修复

## 问题原因

Data Builder 中硬编码了"中医饮食指导AI"作为默认任务，导致：
1. 没有实际任务时显示中医任务
2. 模型默认显示 ChatGLM2-6B
3. 数据生成也是中医相关内容

## 修复内容

### 1. DataBuilder.tsx - 默认任务修改
```javascript
// 旧代码
return {
  task: '中医饮食指导AI',
  type: 'recommendations',
  language: 'chinese',
  labels: [],
  description: '提供基于中医理论的个性化饮食建议'
};

// 新代码
return {
  task: 'Your Custom Task',
  type: 'classification',
  language: 'english',
  labels: [],
  description: 'Please define your task in the Task Builder first'
};
```

### 2. DataBuilder.tsx - 默认模型修改
```javascript
// 旧代码
return {
  id: 'chatglm2-6b',
  name: 'ChatGLM2-6B',
  provider: 'THUDM',
  modelType: 'General',
  size: '6B'
};

// 新代码
return {
  id: 'default-model',
  name: 'Select a Model',
  provider: 'Unknown',
  modelType: 'General',
  size: 'base'
};
```

### 3. data_builder_mock.py - 动态数据生成
现在根据实际任务类型生成相应的数据：
- 如果任务名包含"中医"，生成中医相关数据
- 如果是情感分析任务，生成产品评论数据
- 其他情况生成通用分类数据

## 使用说明

1. **正确流程**：
   - 先在 Task Builder 中定义任务
   - 再到 Model Recommend 选择模型
   - 最后到 Data Builder 收集数据

2. **如果直接访问 Data Builder**：
   - 会看到 "Your Custom Task" 而不是中医任务
   - 提示用户先定义任务

## 重要提示

这些修改确保了：
- ✅ 不会误导用户以为系统只能做中医相关任务
- ✅ 数据生成会根据实际任务动态调整
- ✅ 保持了对中医任务的支持（如果用户确实需要）
- ✅ 提供了更通用的默认体验 