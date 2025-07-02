from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


# Message schemas
class MessageBase(BaseModel):
    role: str
    content: str


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


class ConversationList(BaseModel):
    id: str
    title: Optional[str] = None
    is_completed: bool
    created_at: datetime
    message_count: int
    
    class Config:
        from_attributes = True


class Conversation(ConversationBase):
    id: str
    user_id: str
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[Message] = []
    
    class Config:
        from_attributes = True


# Task Definition schemas
class TaskDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None


class TaskDefinitionCreate(TaskDefinitionBase):
    conversation_id: str


class TaskDefinition(TaskDefinitionBase):
    id: str
    conversation_id: str
    user_id: str
    json_schema: Optional[Any] = None
    recommended_models: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Model Recommendation Schemas
class ModelRecommendationRequest(BaseModel):
    task_definition: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_definition": {
                    "task_name": "Customer Complaint Classification",
                    "task_type": "text-classification",
                    "domain": "customer_service",
                    "language": "english",
                    "requirements": {
                        "accuracy": "high",
                        "speed": "medium"
                    }
                }
            }
        }


class ModelRecommendation(BaseModel):
    model_id: str
    model_name: str
    description: Optional[str] = None
    tags: List[str] = []
    downloads: int = 0
    likes: int = 0
    author: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "distilbert-base-uncased-finetuned-sst-2-english",
                "model_name": "DistilBERT base uncased (SST-2)",
                "description": "This model is a fine-tune checkpoint of DistilBERT-base-uncased, fine-tuned on SST-2.",
                "tags": ["text-classification", "distilbert", "english"],
                "downloads": 1234567,
                "likes": 234,
                "author": "huggingface"
            }
        }


class ModelRecommendationResponse(BaseModel):
    recommendations: List[ModelRecommendation]
    search_keywords: str  # AI 生成的搜索关键词
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "model_id": "distilbert-base-uncased-finetuned-sst-2-english",
                        "model_name": "DistilBERT base uncased (SST-2)",
                        "description": "Fine-tuned on sentiment analysis",
                        "tags": ["text-classification", "distilbert"],
                        "downloads": 1234567,
                        "likes": 234
                    }
                ],
                "search_keywords": "text-classification, sentiment-analysis, english, customer-service"
            }
        } 