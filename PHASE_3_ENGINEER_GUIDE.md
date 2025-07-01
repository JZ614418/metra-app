# 第三阶段：智能模型选择与推荐

## 1. 愿景与目标

第二阶段成功地为**任务定义**建立了一个强大的、由 AI 驱动的对话系统。现在，第三阶段将把这个由用户定义的任务，与一个精心策划的、合适的开源 AI 模型列表无缝地连接起来。

本阶段的核心目标是**赋能非技术用户，让他们能够在不了解 Hugging Face 等模型仓库复杂性的情况下，做出明智的模型选择**。MetraAI 将扮演一个专家顾问的角色，**深度理解**用户任务的细微差别（如语言、领域、性能偏好），并据此推荐最适合该工作的工具。

## 2.核心用户流程

1.  **入口点**：用户在 `TaskBuilder` 组件中最终确定其任务定义后，系统将自动导航到新的 `/model-recommend` 路由。
2.  **任务回顾**：`/model-recommend` 页面将以清晰、人类可读的格式，展示刚刚定义的任务摘要，为接下来的模型推荐提供上下文。
3.  **模型推荐**：系统以交互式"模型卡片"的形式，呈现一个包含 3-5 个推荐开源模型的列表。
4.  **明智决策**：每个模型卡片将包含至关重要的、易于理解的信息：
    *   模型名称 (例如, `distilbert-base-uncased`)
    *   一段简短的、非技术性的描述。
    *   关键标签 (例如, `text-classification`, `distilbert`)。
    *   受欢迎程度指标 (例如, 下载量、点赞数)，以建立信任。
5.  **选择与过渡**：用户通过点击"选择并继续"按钮来选择一个模型。这个选择将被持久化，并且用户将被导航到平台的下一个流程（第四阶段：数据构建器）。

## 3. 技术实现计划：两阶段智能推荐

我们将采用一个更智能的两阶段推荐方案，以确保推荐结果的高度相关性和准确性。

### 3.1. 后端 (Python/FastAPI)

#### 任务一：创建模型推荐 Endpoint

-   **文件**: `backend/app/api/v1/endpoints/recommendations.py`
-   **Endpoint**: `POST /api/v1/recommend`
-   **请求体**: 该 Endpoint 将接受在第二阶段中创建的、结构化的`任务定义` JSON 对象。
-   **核心逻辑：**

    **阶段一：AI 提炼搜索关键词**
    1.  **输入**: 将完整的`任务定义` JSON 作为上下文。
    2.  **调用 OpenAI**: 使用 GPT-4o-mini 模型，并为其提供一个专门设计的 "Hugging Face 模型策展人" System Prompt。
    3.  **Prompt 指令**: 指示 AI 分析 JSON 中的所有信息（包括 `task_type`, `domain`, `language`, `requirements` 等），并生成一个用于在 Hugging Face Hub 上进行精确搜索的、由逗号分隔的关键词字符串。
    4.  **输出**: 得到一个由 AI 智能提炼的、包含多个关键词的字符串 (例如, `"token-classification, ner, chinese, medical, accuracy"`)。

    **阶段二：代码执行多关键词搜索**
    1.  **添加依赖**: 将 `huggingface_hub` 添加到 `backend/requirements.txt`。
    2.  **输入**: 使用上一阶段 AI 生成的关键词字符串。
    3.  **查询 Hugging Face Hub**: 使用 `huggingface_hub.list_models()` 函数，将整个关键词字符串传递给 `search` 参数。
        -   结果将按 `likes` 或 `downloads` 降序排序，以优先推荐流行的、经过充分验证的模型。
    4.  **处理与格式化**: 处理 API 调用返回的前 5 个结果。为每个模型提取并格式化以下字段：
        -   `modelId` (字符串)
        -   `description` (字符串)
        -   `tags` (字符串数组)
        -   `downloads` (整数)
        -   `likes` (整数)
    5.  **返回响应**: 将格式化后的推荐模型列表发送回前端。

#### 任务二：集成新 Endpoint

-   **文件**: `backend/app/api/v1/api.py`
-   **操作**: 导入并包含新的 `recommendations` 路由。

### 3.2. 前端 (React/TypeScript)

#### 任务一：创建模型选择页面组件

-   **文件**: `metra-ai-factory-main/src/pages/ModelRecommend.tsx`
-   **路由**: 在 `metra-ai-factory-main/src/App.tsx` 中为 `/model-recommend` 添加新路由。
-   **核心逻辑**:
    1.  **状态管理**: 创建一个新的 Zustand store `useModelStore` (或扩展现有 store)，用于管理所选模型和推荐列表。
    2.  **API 调用**: 页面加载时，从 `conversationStore` 中检索最终确定的`任务定义`，并将其发送到新的 `POST /api/v1/recommend` 后端 Endpoint。
    3.  **渲染界面**:
        -   在获取推荐数据时，显示加载状态。
        -   如果 API 调用失败，显示错误状态。
        -   使用 `SchemaDisplay` 组件在页面顶部显示任务摘要。
        -   遍历推荐数据，以渲染一个`模型卡片`组件列表。

#### 任务二：创建 `ModelCard` 组件

-   **文件**: `metra-ai-factory-main/src/components/ModelCard.tsx`
-   **Props**: 该组件将接受一个推荐模型对象作为 prop。
-   **界面**:
    -   使用 Shadcn `Card` 组件作为基础结构。
    -   显示模型的名称、描述、标签 (作为 `Badge` 组件) 和受欢迎程度指标。
    -   包含一个醒目的"选择并继续"按钮。
-   **操作**: 当按钮被点击时，它将用所选的 `modelId` 更新 `useModelStore`，并将用户导航到下一步 (`/data-builder`)。

## 4. 完成的定义 (Definition of Done)

当以下所有条件都满足时，第三阶段将被视为完成：
-   后端能够基于给定的任务定义，**通过两阶段智能流程**，成功地从 Hugging Face Hub 推荐**高度相关**的模型。
-   前端能够在一个干净、用户友好的界面中正确显示这些推荐。
-   用户可以选择一个模型，该选择能被持久化到应用状态中，并被导航到下一个逻辑步骤。
-   从任务定义到模型选择的整个流程是无缝、智能且稳健的。 