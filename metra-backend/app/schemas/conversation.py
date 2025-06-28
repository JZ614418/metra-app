from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Message schemas
class MessageBase(BaseModel):
    content: str
    role: MessageRole

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    conversation_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Conversation schemas
class ConversationBase(BaseModel):
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(ConversationBase):
    is_completed: Optional[bool] = None

class Conversation(ConversationBase):
    id: str
    user_id: str
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[Message] = []
    
    class Config:
        from_attributes = True

class ConversationList(BaseModel):
    id: str
    title: Optional[str]
    is_completed: bool
    created_at: datetime
    message_count: int
    
    class Config:
        from_attributes = True

# Task Definition schemas
class TaskDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None

class TaskDefinitionCreate(TaskDefinitionBase):
    conversation_id: str
    json_schema: dict
    recommended_models: Optional[List[str]] = None

class TaskDefinition(TaskDefinitionBase):
    id: str
    conversation_id: str
    user_id: str
    json_schema: dict
    recommended_models: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 