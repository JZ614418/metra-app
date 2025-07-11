"""
DFE (Data Fusion Engine) API endpoints
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Optional
import uuid

from app.services.dfe_service import dfe_service

router = APIRouter()

@router.post("/start")
async def start_dfe_extraction(
    urls: List[str] = Body(..., description="List of URLs to extract content from"),
    options: Optional[Dict] = Body(None, description="V2 feature options")
):
    """
    启动DFE数据提取任务
    
    V1功能：基础网页抓取
    - 从URL列表抓取网页内容
    - 提取主要文本内容
    - 返回结构化数据
    
    V2功能（通过options启用）：
    - field_alignment: 字段对齐配置
    - fill_missing_values: 是否填充缺失值
    - data_augmentation: 是否进行数据增强
    - output_format: 输出格式（json/jsonl/csv）
    
    示例请求：
    ```json
    {
        "urls": ["https://example.com/page1", "https://example.com/page2"],
        "options": {
            "enable_v2_features": true,
            "field_alignment": {
                "title": ["标题", "title", "name", "名称"],
                "content": ["内容", "content", "text", "正文"],
                "author": ["作者", "author", "writer", "撰写人"]
            },
            "fill_missing_values": true,
            "data_augmentation": true,
            "output_format": "jsonl"
        }
    }
    ```
    """
    if not urls:
        raise HTTPException(status_code=400, detail="URLs list cannot be empty")
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 启动提取任务
    result = await dfe_service.start_extraction(task_id, urls, options)
    
    return result

@router.get("/status/{task_id}")
async def get_dfe_status(task_id: str):
    """
    获取DFE任务状态
    
    返回：
    - id: 任务ID
    - status: 状态（processing/completed/failed）
    - progress: 进度百分比
    - total: 总URL数量
    - created_at: 创建时间
    - error: 错误信息（如果有）
    """
    status = await dfe_service.get_task_status(task_id)
    
    if "error" in status and status["error"] == "Task not found":
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status

@router.get("/results/{task_id}")
async def get_dfe_results(task_id: str):
    """
    获取DFE任务结果
    
    V1结果格式：
    ```json
    {
        "url": "https://example.com",
        "title": "页面标题",
        "meta_description": "页面描述",
        "main_content": "提取的主要内容",
        "extracted_at": "2024-01-01T00:00:00",
        "success": true
    }
    ```
    
    V2结果格式（根据options配置）：
    - 字段对齐后的统一格式
    - 填充了缺失值
    - 包含增强的数据样本
    - 转换为指定的输出格式
    """
    results = await dfe_service.get_task_results(task_id)
    
    if "error" in results:
        if results["error"] == "Task not found":
            raise HTTPException(status_code=404, detail="Task not found")
        elif "not completed" in results["error"]:
            raise HTTPException(status_code=400, detail=results["error"])
    
    return results

@router.post("/demo")
async def demo_dfe_extraction():
    """
    演示DFE功能 - 使用预设的中医药URL进行测试
    
    这个端点展示了V1和V2的完整功能：
    1. 抓取中医药相关网页
    2. 提取内容
    3. 字段对齐（中英文字段名映射）
    4. 填充缺失值
    5. 数据增强
    6. 格式转换为JSONL
    """
    # 演示用的中医药相关URL
    demo_urls = [
        "https://www.webmd.com/vitamins/ai/ingredientmono-1169/turmeric",
        "https://www.healthline.com/nutrition/top-10-evidence-based-health-benefits-of-turmeric",
        "https://www.medicalnewstoday.com/articles/306981"
    ]
    
    # V2高级功能配置
    demo_options = {
        "enable_v2_features": True,
        "field_alignment": {
            "herb_name": ["name", "title", "herb", "药材名称"],
            "description": ["description", "content", "text", "描述"],
            "benefits": ["benefits", "effects", "功效", "作用"],
            "usage": ["usage", "application", "用法", "使用方法"]
        },
        "fill_missing_values": True,
        "data_augmentation": True,
        "output_format": "jsonl"
    }
    
    # 生成任务ID
    task_id = f"demo_{uuid.uuid4()}"
    
    # 启动提取
    result = await dfe_service.start_extraction(task_id, demo_urls, demo_options)
    
    return {
        **result,
        "demo_info": "This is a demo extraction with V1+V2 features. Check status and results using the task_id."
    } 

@router.get("/available-tasks")
async def get_available_tasks():
    """
    获取可用于DFE处理的Data Builder任务列表
    
    返回已完成的Data Builder任务，这些任务可以作为DFE的输入
    """
    # 在实际实现中，这应该从数据库读取Data Builder的任务
    # 现在返回模拟数据
    mock_tasks = [
        {
            "id": "task_001",
            "task_name": "TCM Diet Guidance AI",
            "status": "completed",
            "total_count": 1500,
            "collected_count": 1500,
            "created_at": "2024-03-15T10:30:00",
            "sources": {"web": 800, "ai": 500, "upload": 200}
        },
        {
            "id": "task_002",
            "task_name": "Customer Complaint Classifier",
            "status": "completed",
            "total_count": 3000,
            "collected_count": 3000,
            "created_at": "2024-03-14T15:20:00",
            "sources": {"web": 1500, "ai": 1000, "upload": 500}
        }
    ]
    
    return {"tasks": mock_tasks}

@router.post("/process-task/{task_id}")
async def process_data_builder_task(
    task_id: str,
    options: Optional[Dict] = Body(None, description="V2 feature options")
):
    """
    处理Data Builder的任务输出
    
    这个端点读取Data Builder任务的结果，并应用DFE的处理流程
    """
    # 生成DFE任务ID
    dfe_task_id = f"dfe_{task_id}_{uuid.uuid4()}"
    
    # 在实际实现中，这里应该：
    # 1. 从数据库读取Data Builder任务的结果
    # 2. 提取所有URL和数据
    # 3. 启动DFE处理
    
    # 模拟处理
    # 假设我们从Data Builder任务中获取了URL列表
    urls = [
        "https://example.com/tcm-article-1",
        "https://example.com/tcm-article-2",
        "https://example.com/tcm-article-3"
    ]
    
    # 默认启用V2功能
    if options is None:
        options = {
            "enable_v2_features": True,
            "field_alignment": {
                "text": ["content", "text", "body", "内容", "正文"],
                "label": ["category", "type", "label", "类别", "标签"]
            },
            "fill_missing_values": True,
            "data_augmentation": True,
            "output_format": "jsonl"
        }
    
    # 启动DFE处理
    result = await dfe_service.start_extraction(dfe_task_id, urls, options)
    
    return {
        **result,
        "source_task_id": task_id,
        "dfe_task_id": dfe_task_id
    } 