# Metra Guideline v4.0（开发与产品实施指导）

本指南基于 Metra PRD v4.0，适用于产品管理、前后端开发、AI 工程与设计协作各方。

---

## 🎯 核心定位（更新版）

Metra 是一个面向非技术用户的增值训练平台，用户可以通过自然语言需求描述，基于开源大模型训练出自己的专属 AI 助手。

---

## 🪜 核心用户流程（闭环设计）

### Step 1：自然语言描述 → 任务结构化（Prompt-to-Schema）

* 用户用一句话表达目标，如“我想训练一个能识别评论情绪的 AI”
* Metra 通过多轮对话确认任务类型、输入输出字段、示例样本
* 输出结构化任务定义（schema）

### Step 2：基础模型推荐

* 系统基于任务类型推荐合适的开源基础模型（如 Mistral、BERT、Whisper、SAM 等）
* 显示：模型名称、架构、用途、优劣、训练成本
* 用户可接受推荐或自选模型

### Step 3：数据获取方式

用户从以下三种方式中选择构建训练数据：

1. Metra 自动爬虫（ScrapingBee 实现）
2. AI 合成数据（使用 GPT-3.5）
3. 用户手动上传（CSV、JSON、图像等）

支持进一步通过 AI 与用户沟通：数据样本格式、数量、结构。

### Step 4：数据整合引擎 DFE

* 自动字段识别（含中英文映射）
* 缺失值补全建议
* 转换为可训练格式（jsonl / image-folder 等）
* 用户可视化编辑（基于 Handsontable 实现）

### Step 5：增值训练模块（Fine-tune）

* 使用推荐模型 + 处理后数据启动训练
* 调用 Replicate API 实现模型微调
* 用户界面显示：训练进度条 + 简化术语解读 + 输出示例卡片

### Step 6：部署与交付

* 用户获得训练后的模型，以以下方式交付：

  * API + 文档 + Token
  * 本地模型导出（GGUF / .pt / ONNX）
  * 插件打包（Notion 插件、浏览器插件等）

### Step 7（可选）：社区模型市场（MVP）

* 用户可上架模型，设置：

  * API 调用价格
  * 买断价格
  * 可否 fork / 留评论 / 收藏

---

## 🛠 技术选型建议

### 核心平台组件

| 模块     | 技术栈                                     |
| ------ | --------------------------------------- |
| 前端     | React + TypeScript + TailwindCSS        |
| 后端     | FastAPI + PostgreSQL + Supabase + Redis |
| 模型调用   | Replicate API + HuggingFace 接口（预留）      |
| LLM 服务 | OpenAI GPT-4 / GPT-3.5 / Embedding      |
| 数据编辑   | Handsontable（商业版）                       |
| 文件上传   | Supabase Storage API                    |
| 用户认证   | Supabase Auth（邮箱登录）                     |
| 计费系统   | Stripe                                  |

---

## 🎨 UI/UX 设计规范（继承 V3 设计原则）

### 极简 + 科技感 + 不冷冰：六大细节规范

1. **无边框菜单分组**：左侧导航栏仅靠字体和留白层级区分，不加线条
2. **字体统一但层级分明**：Inter 字体 + Regular / Medium / Bold 构建视觉结构
3. **图标小而稳重**：统一线稿风格，尺寸 16-20px，不添加颜色
4. **配色系统极简**：主色灰色系（gray-900 #111827）、辅助蓝色系（blue-500/600）、背景纯白+浅灰卡片
5. **克制的点击区域**：所有按钮、列表项上下预留 12px padding
6. **统一圆角 + 阴影**：8px 圆角 + subtle shadow 形成视觉锚点

---

## 🧩 模块开发顺序建议（按里程碑）

| 优先级 | 模块                   | 建议阶段  |
| --- | -------------------- | ----- |
| P0  | 用户认证 + Schema 生成     | 第1周   |
| P1  | 模型推荐卡片系统             | 第2周   |
| P2  | 数据构建接口（上传 + 爬虫 + 合成） | 第2-3周 |
| P3  | 数据整合引擎 MVP           | 第3-4周 |
| P4  | 模型训练 API 接入 + 训练流程展示 | 第4-5周 |
| P5  | 模型导出 / API 封装模块      | 第5-6周 |
| P6  | 模型管理页 + 社区 MVP       | 第6-7周 |
| P7  | UI/UX 全局优化 + 动效完善    | 第8周   |

---

## 🧠 产品哲学备忘

* 用 AI 理解用户，而不是让用户理解 AI。
* 每个模型背后都蕴含着一个真实业务问题。
* Metra 的竞争力不在训练，而在“结构化思考 + 数据打理 + 输出封装”。
* 真正的价值，不是让人多造模型，而是把专属 AI 变成生产力资产。

---

如需协作启动具体开发模块，请依照本 Guideline 所列顺序对接开发者、设计师与 API 提供方。
