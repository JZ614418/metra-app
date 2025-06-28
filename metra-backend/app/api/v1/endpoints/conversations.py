from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.base import get_db
from app.models import User, Conversation, Message, TaskDefinition
from app.models.message import MessageRole
from app.schemas.conversation import (
    ConversationCreate, Conversation as ConversationSchema,
    ConversationList, ConversationUpdate,
    MessageCreate, Message as MessageSchema
)
from app.services.auth import get_current_user
from app.services.openai_service import OpenAIService

router = APIRouter()

@router.post("/", response_model=ConversationSchema)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的对话"""
    db_conversation = Conversation(
        user_id=current_user.id,
        title=conversation.title,
        is_completed=False
    )
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    
    # 加载关联数据
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == db_conversation.id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one()

@router.get("/", response_model=List[ConversationList])
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的对话列表"""
    # 查询对话列表，包含消息数量
    result = await db.execute(
        select(
            Conversation.id,
            Conversation.title,
            Conversation.is_completed,
            Conversation.created_at,
            func.count(Message.id).label("message_count")
        )
        .outerjoin(Message)
        .where(Conversation.user_id == current_user.id)
        .group_by(Conversation.id)
        .order_by(Conversation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    conversations = []
    for row in result:
        conversations.append(ConversationList(
            id=row.id,
            title=row.title,
            is_completed=row.is_completed,
            created_at=row.created_at,
            message_count=row.message_count or 0
        ))
    
    return conversations

@router.get("/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取特定对话的详情和消息历史"""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
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
    
    return conversation

@router.post("/{conversation_id}/messages", response_model=MessageSchema)
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息并获取AI回复"""
    # 验证对话存在且属于当前用户
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
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
    
    # 保存用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=message.content
    )
    db.add(user_message)
    await db.commit()
    
    # 获取所有消息历史
    messages = sorted(conversation.messages + [user_message], key=lambda m: m.created_at)
    
    # 调用OpenAI服务
    try:
        openai_service = OpenAIService()
        ai_response = await openai_service.get_ai_response(messages)
        
        # 保存AI回复
        ai_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=ai_response
        )
        db.add(ai_message)
        
        # 检查是否生成了schema
        if openai_service.is_schema_complete(ai_response):
            conversation.is_completed = True
            
            # 如果是第一条消息，设置对话标题
            if not conversation.title and len(messages) == 1:
                # 使用用户的第一条消息作为标题（截取前50个字符）
                conversation.title = message.content[:50] + "..." if len(message.content) > 50 else message.content
        
        await db.commit()
        await db.refresh(ai_message)
        
        return ai_message
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating AI response: {str(e)}"
        )

@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: str,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息并获取AI的流式回复"""
    # 验证对话存在且属于当前用户
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
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
    
    # 保存用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=message.content
    )
    db.add(user_message)
    await db.commit()
    
    # 获取所有消息历史
    messages = sorted(conversation.messages + [user_message], key=lambda m: m.created_at)
    
    # 创建流式响应生成器
    async def generate():
        try:
            openai_service = OpenAIService()
            full_response = ""
            
            # 发送流式响应
            async for chunk in openai_service.get_ai_response_stream(messages):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            
            # 保存完整的AI回复
            ai_message = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=full_response
            )
            db.add(ai_message)
            
            # 检查是否生成了schema
            if openai_service.is_schema_complete(full_response):
                conversation.is_completed = True
                
                # 如果是第一条消息，设置对话标题
                if not conversation.title and len(messages) == 1:
                    conversation.title = message.content[:50] + "..." if len(message.content) > 50 else message.content
            
            await db.commit()
            
            # 发送结束信号
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            await db.rollback()
            yield f"data: ERROR: {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.patch("/{conversation_id}", response_model=ConversationSchema)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新对话信息"""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # 更新字段
    if conversation_update.title is not None:
        conversation.title = conversation_update.title
    if conversation_update.is_completed is not None:
        conversation.is_completed = conversation_update.is_completed
    
    await db.commit()
    await db.refresh(conversation)
    
    # 重新加载关联数据
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one() 