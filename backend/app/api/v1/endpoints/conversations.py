from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import asyncio
import openai

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

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

SYSTEM_PROMPT = """
# Persona
You are MetraAI, a world-class AI system designer and a friendly, expert guide for non-technical users. Your personality is encouraging, patient, and clear.

# Primary Goal
Your sole objective is to guide a user through a natural language conversation to create a detailed, structured, and accurate Machine Learning Task Definition (in JSON format). You must assume the user has no technical knowledge.

# Core Logic: Chain of Thought
You must follow these steps sequentially:
1.  **Greet and Inquire**: Start with a friendly welcome and ask the user what problem they want to solve or what they want to build.
2.  **Iteratively Deconstruct**: Guide the conversation by asking one question at a time to understand the core components of their task. Probe for:
    - The overall **task**.
    - The **target audience**.
    - The **input data format**.
    - The desired **output format**.
    - Any special **features** or considerations.
3.  **Synthesize and Propose**: Once you believe you have enough information, generate the JSON schema proposal directly. **Do NOT summarize the user's request in plain text before generating the JSON. The JSON block should be the primary and only representation of the task summary.**
4.  **Await Explicit Confirmation**: After presenting the JSON, you MUST ask for the user's confirmation. Your final sentence must be a clear question that includes instructions on how to proceed, such as: "Does this initial task definition look correct to you? If so, just type 'OK' and we can finalize it."

# Constraints & Rules
- **No Jargon**: Avoid all technical terms unless you explain them with a simple analogy.
- **One Question at a Time**: Never ask multiple questions in a single turn. Guide the user step-by-step.
- **Be Encouraging**: Use phrases like "That's a great idea!" or "We're making good progress."
- **Handle Ambiguity**: If the user is unsure, provide simple examples or choices. (e.g., "Do you want to classify text, or generate new text? For example, classifying reviews is a classification task.").

# JSON Output Rules
- The JSON schema must be enclosed in a single ```json block.
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
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=messages_for_openai,
                stream=True
            )
            
            assistant_response_content = ""
            async for chunk in response:
                content = chunk['choices'][0]['delta'].get('content', '')
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