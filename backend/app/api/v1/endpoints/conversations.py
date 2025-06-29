from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import asyncio

from app.api import deps
from app.models.user import User
from app.models.conversation import Conversation, Message, TaskDefinition
from app.schemas.conversation import (
    ConversationCreate, 
    Conversation as ConversationSchema,
    ConversationList,
    MessageCreate,
    Message as MessageSchema,
    TaskDefinitionCreate,
    TaskDefinition as TaskDefinitionSchema
)
from app.db.session import get_db

router = APIRouter()


@router.post("/conversations", response_model=ConversationSchema)
def create_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_in: ConversationCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        user_id=current_user.id,
        title=conversation_in.title
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=List[ConversationList])
def list_conversations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> List[ConversationList]:
    """List all conversations for the current user."""
    conversations = db.query(
        Conversation.id,
        Conversation.title,
        Conversation.is_completed,
        Conversation.created_at,
        func.count(Message.id).label("message_count")
    ).outerjoin(Message).filter(
        Conversation.user_id == current_user.id
    ).group_by(
        Conversation.id
    ).order_by(
        Conversation.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        ConversationList(
            id=c.id,
            title=c.title,
            is_completed=c.is_completed,
            created_at=c.created_at,
            message_count=c.message_count or 0
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
def get_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Conversation:
    """Get a specific conversation with all messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.post("/conversations/{conversation_id}/messages", response_model=MessageSchema)
def create_message(
    *,
    db: Session = Depends(get_db),
    conversation_id: str,
    message_in: MessageCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Message:
    """Add a message to a conversation."""
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create message
    message = Message(
        conversation_id=conversation_id,
        role=message_in.role,
        content=message_in.content
    )
    db.add(message)
    
    # For now, just echo back the message (no AI response)
    # In a real implementation, you would call an AI service here
    if message_in.role == "user":
        ai_response = Message(
            conversation_id=conversation_id,
            role="assistant",
            content="I understand you want to create an AI model. Let me help you define your requirements. Could you tell me more about what kind of data you'll be working with and what you want the model to do?"
        )
        db.add(ai_response)
    
    db.commit()
    db.refresh(message)
    return message


@router.post("/conversations/{conversation_id}/messages/stream")
async def create_message_stream(
    *,
    db: Session = Depends(get_db),
    conversation_id: str,
    message_in: MessageCreate,
    current_user: User = Depends(deps.get_current_user)
):
    """Stream a message response."""
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create user message
    user_message = Message(
        conversation_id=conversation_id,
        role=message_in.role,
        content=message_in.content
    )
    db.add(user_message)
    db.commit()
    
    # Simulate streaming response
    async def generate():
        # Simulated AI response
        response_text = """I understand you want to create an AI model. Let me help you define your requirements.

Based on what you've told me, I'll need to understand:
1. What type of data you'll be working with
2. What you want the model to predict or generate
3. Any specific requirements or constraints

Could you provide more details about your use case?

Here's a sample JSON schema for your task:

```json
{
  "task_type": "classification",
  "input_type": "text",
  "output_type": "category",
  "categories": ["positive", "negative", "neutral"],
  "requirements": {
    "accuracy": "high",
    "latency": "low",
    "interpretability": "medium"
  }
}
```

I now have enough information to proceed with model recommendations."""
        
        # Stream the response character by character
        for char in response_text:
            yield f"data: {char}\n\n"
            await asyncio.sleep(0.01)  # Simulate typing delay
        
        # Save the complete AI response
        ai_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text
        )
        db.add(ai_message)
        
        # Mark conversation as completed if the response indicates so
        if "I now have enough information" in response_text:
            conversation.is_completed = True
        
        db.commit()
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/task-definitions", response_model=TaskDefinitionSchema)
def create_task_definition(
    *,
    db: Session = Depends(get_db),
    task_in: TaskDefinitionCreate,
    current_user: User = Depends(deps.get_current_user)
) -> TaskDefinition:
    """Create a task definition from a conversation."""
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == task_in.conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Extract JSON schema from the last AI message
    last_ai_message = db.query(Message).filter(
        Message.conversation_id == task_in.conversation_id,
        Message.role == "assistant"
    ).order_by(Message.created_at.desc()).first()
    
    json_schema = None
    if last_ai_message:
        # Simple extraction of JSON from message
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', last_ai_message.content)
        if json_match:
            try:
                json_schema = json.loads(json_match.group(1))
            except:
                pass
    
    # Create task definition
    task_definition = TaskDefinition(
        conversation_id=task_in.conversation_id,
        user_id=current_user.id,
        name=task_in.name,
        description=task_in.description,
        json_schema=json_schema,
        recommended_models=["gpt-4", "claude-2", "llama-2"]  # Example recommendations
    )
    db.add(task_definition)
    
    # Mark conversation as completed
    conversation.is_completed = True
    
    db.commit()
    db.refresh(task_definition)
    return task_definition 