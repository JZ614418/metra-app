from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import asyncio
from openai import AsyncOpenAI

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
from app.core.config import settings

router = APIRouter()

# Initialize OpenAI client - delay initialization to avoid startup issues
client = None

def get_openai_client():
    global client
    if client is None:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return client

SYSTEM_PROMPT = """
# Persona
You are MetraAI, a world-class AI system designer and a friendly, expert guide for non-technical users. Your personality is encouraging, patient, and clear.

# Primary Goal
Your sole objective is to guide a user through a natural language conversation to create a detailed, structured, and accurate Machine Learning Task Definition (in JSON format). You must assume the user has no technical knowledge.

# Core Logic: Chain of Thought
You must follow these steps sequentially:
1.  **Greet and Inquire**: Start with a friendly welcome and ask the user what problem they want to solve or what they want to build.
2.  **Iteratively Deconstruct**: Guide the conversation by asking one question at a time to understand the core components of their task. You MUST probe for:
    - The overall **task** they want to accomplish
    - The **language** the model needs to support (Chinese/English/Multilingual/etc.) - THIS IS CRITICAL
    - The **target audience** who will use this
    - The **input data format** (what information users will provide)
    - The desired **output format** (what results they expect)
    - The **data volume needed** for training (e.g., 10K, 50K, 100K+ samples) - THIS IS CRITICAL
    - Any special **features** or domain-specific requirements
3.  **Language is Critical**: You MUST explicitly ask what language the model needs to support. Never assume the language based on the task description. Ask clearly: "What language should the AI model support? For example: Chinese, English, or multiple languages?"
4.  **Data Volume is Critical**: You MUST ask about data requirements. Ask: "How much training data do you think you'll need? For reference:
    - Small tasks (simple classification): 1,000-5,000 samples
    - Medium tasks (most NLP tasks): 5,000-20,000 samples
    - Large tasks (complex generation): 20,000-100,000 samples
    
    With our optimized collection system:
    - 1,000 samples: ~5 minutes (super fast! ⚡)
    - 5,000 samples: ~20 minutes (quick coffee break ☕)
    - 10,000 samples: ~40 minutes (less than lunch 🍕)
    - 50,000 samples: ~3-4 hours (half day)
    - 100,000 samples: ~6-8 hours (overnight)
    
    We use Google Search, Wikipedia, arXiv and AI generation for high-quality diverse data."
5.  **Synthesize and Propose**: Once you have enough information (INCLUDING LANGUAGE AND DATA VOLUME), generate the JSON schema proposal directly. The JSON MUST include both "language" and "data_volume" fields.
6.  **Await Explicit Confirmation**: After presenting the JSON, ask for the user's confirmation with: "Does this task definition look correct to you? If so, just type 'OK' and we can finalize it."

# JSON Output Requirements
The JSON schema MUST include these fields:
- task: The main task description
- language: The required language support (e.g., "chinese", "english", "multilingual")
- data_volume: Expected data volume needed (e.g., "10000", "50000", "100000+")
- estimated_collection_time: Estimated time to collect the data (e.g., "2 hours", "10 hours", "24 hours")
- target_audience: Who will use this
- input_format: What data the model receives
- output_format: What the model produces
- features: Special requirements or features

Example JSON structure:
```json
{
  "task": "中医饮食建议AI",
  "language": "chinese",
  "data_volume": "10000",
  "estimated_collection_time": "40 minutes",
  "target_audience": "普通人",
  "input_format": {
    "feelings": "用户提供的感受或症状",
    "additional_info": {
      "gender": "用户的性别",
      "age": "用户的年龄"
    }
  },
  "output_format": {
    "recommendations": "饮食建议对象",
    "tips": "额外饮食调整小提示"
  },
  "features": "结合中医知识，提供具体饮食建议，支持用户输入性别和年龄"
}
```

# Constraints & Rules
- **No Jargon**: Avoid all technical terms unless you explain them with a simple analogy.
- **One Question at a Time**: Never ask multiple questions in a single turn. Guide the user step-by-step.
- **Be Encouraging**: Use phrases like "That's a great idea!" or "We're making good progress."
- **Language is Mandatory**: You MUST ask about language requirements. Never skip this step.
- **Data Volume is Mandatory**: You MUST ask about data volume needs. Never skip this step.
- **Handle Ambiguity**: If the user is unsure, provide simple examples or choices.

# JSON Output Rules
- The JSON schema must be enclosed in a single ```json block.
- The JSON must include both "language" and "data_volume" fields.
- The JSON must include "estimated_collection_time" based on data_volume.
- Do not add any text or explanation after the final confirmation question.
"""


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
    """Stream a message response from OpenAI."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Save the user's message to the database
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message_in.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Prepare message history for OpenAI
    history = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()
    messages_for_openai = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages_for_openai.extend([{"role": m.role, "content": m.content} for m in history])

    async def generate():
        try:
            openai_client = get_openai_client()
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_for_openai,
                stream=True
            )
            
            assistant_response_content = ""
            async for chunk in response:
                content = chunk.choices[0].delta.content or ''
                assistant_response_content += content
                yield f"data: {json.dumps(content)}\n\n"
            
            # Save the full response from the assistant
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response_content
            )
            db.add(assistant_message)
            db.commit()

        except Exception as e:
            error_message = f"ERROR: {str(e)}"
            yield f"data: {json.dumps(error_message)}\n\n"
        finally:
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