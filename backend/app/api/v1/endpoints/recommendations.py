from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import openai
from huggingface_hub import HfApi, ModelFilter
from typing import List, Dict, Any

from app.api import deps
from app.models.user import User
from app.core.config import settings

router = APIRouter()
hf_api = HfApi()

class TaskDefinition(BaseModel):
    task: str
    task_type: str
    domain: str
    language: str
    # ... and other fields from the user's task definition

class ModelRecommendation(BaseModel):
    modelId: str
    description: str
    tags: List[str]
    downloads: int
    likes: int

RECOMMENDATION_PROMPT = """
You are an expert Hugging Face model curator. Your task is to analyze the following user's task definition (JSON) and generate a list of precise, relevant keywords and tags that can be used to search for the best possible models on the Hugging Face Hub. 

Consider all aspects like task, language, performance requirements, and domain. Output these keywords as a single, comma-separated string. Be concise and focus on terms that are effective for searching the Hub.

User's Task Definition:
{task_definition}
"""

@router.post("/recommend", response_model=List[ModelRecommendation])
async def recommend_models(
    task_definition: Dict[Any, Any],
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Recommends Hugging Face models based on a two-stage process:
    1. AI-driven keyword extraction from the task definition.
    2. API call to Hugging Face Hub using the extracted keywords.
    """
    try:
        # Stage 1: AI-driven keyword extraction
        prompt = RECOMMENDATION_PROMPT.format(task_definition=task_definition)
        
        response = await openai.Completion.acreate(
            engine="gpt-4o-mini", # Or any suitable model
            prompt=prompt,
            max_tokens=50,
            temperature=0.2,
            stop=None
        )
        search_keywords = response.choices[0].text.strip()

        # Stage 2: Search Hugging Face Hub
        models = hf_api.list_models(
            search=search_keywords,
            sort="likes",
            direction=-1,
            limit=5
        )
        
        recommendations = []
        for model in models:
            recommendations.append(ModelRecommendation(
                modelId=model.modelId,
                description=getattr(model, 'description', 'No description available.'),
                tags=model.tags,
                downloads=getattr(model, 'downloads', 0),
                likes=getattr(model, 'likes', 0)
            ))
            
        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 