from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.base import get_db
from app.models import User, Conversation, TaskDefinition as TaskDefinitionModel
from app.schemas.conversation import TaskDefinitionCreate, TaskDefinition
from app.api.v1.endpoints.auth import get_current_user
from app.services.openai_service import OpenAIService

router = APIRouter()

@router.post("/", response_model=TaskDefinition)
async def create_task_definition(
    task_def: TaskDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务定义（保存生成的Schema）"""
    # 验证对话存在且属于当前用户
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == task_def.conversation_id,
            Conversation.user_id == current_user.id
        )
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # 检查是否已经有任务定义
    existing_task = await db.execute(
        select(TaskDefinitionModel)
        .where(TaskDefinitionModel.conversation_id == task_def.conversation_id)
    )
    if existing_task.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task definition already exists for this conversation"
        )
    
    # 如果没有提供schema，尝试从最后的AI消息中提取
    if not task_def.json_schema:
        # 获取最后的AI消息
        ai_messages = [m for m in conversation.messages if m.role.value == "assistant"]
        if ai_messages:
            last_ai_message = sorted(ai_messages, key=lambda m: m.created_at)[-1]
            openai_service = OpenAIService()
            extracted_schema = openai_service.extract_json_schema(last_ai_message.content)
            if extracted_schema:
                task_def.json_schema = extracted_schema
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid JSON schema found in conversation"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No AI response found in conversation"
            )
    
    # 创建任务定义
    db_task_def = TaskDefinitionModel(
        conversation_id=task_def.conversation_id,
        user_id=current_user.id,
        name=task_def.name,
        description=task_def.description,
        json_schema=task_def.json_schema,
        recommended_models=task_def.recommended_models
    )
    
    # 更新对话状态
    conversation.is_completed = True
    
    db.add(db_task_def)
    await db.commit()
    await db.refresh(db_task_def)
    
    return db_task_def

@router.get("/", response_model=List[TaskDefinition])
async def list_task_definitions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的所有任务定义"""
    result = await db.execute(
        select(TaskDefinitionModel)
        .where(TaskDefinitionModel.user_id == current_user.id)
        .order_by(TaskDefinitionModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    return result.scalars().all()

@router.get("/{task_id}", response_model=TaskDefinition)
async def get_task_definition(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取特定的任务定义"""
    result = await db.execute(
        select(TaskDefinitionModel)
        .where(
            TaskDefinitionModel.id == task_id,
            TaskDefinitionModel.user_id == current_user.id
        )
    )
    task_def = result.scalar_one_or_none()
    
    if not task_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task definition not found"
        )
    
    return task_def

@router.delete("/{task_id}")
async def delete_task_definition(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务定义"""
    result = await db.execute(
        select(TaskDefinitionModel)
        .where(
            TaskDefinitionModel.id == task_id,
            TaskDefinitionModel.user_id == current_user.id
        )
    )
    task_def = result.scalar_one_or_none()
    
    if not task_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task definition not found"
        )
    
    await db.delete(task_def)
    await db.commit()
    
    return {"detail": "Task definition deleted successfully"} 