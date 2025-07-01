from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import openai
from huggingface_hub import HfApi, ModelFilter
from typing import List, Dict, Any
import json

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
    name: str
    provider: str = Field(..., alias='author')
    architecture: str
    parameters: str
    description: str
    strengths: List[str]
    weaknesses: List[str]
    trainCost: str
    trainTime: str
    accuracy: str
    recommended: bool
    expertOpinion: str
    icon: str

RECOMMENDATION_PROMPT = """
You are an expert Hugging Face model curator. Your task is to analyze the following user's task definition (JSON) and generate a list of precise, relevant keywords and tags that can be used to search for the best possible models on the Hugging Face Hub. 

Consider all aspects like task, language, performance requirements, and domain. Output these keywords as a single, comma-separated string. Be concise and focus on terms that are effective for searching the Hub.

User's Task Definition:
{task_definition}
"""

ENRICHMENT_PROMPT = """
You are an AI model analyst. Based on the following Hugging Face model info, provide a concise analysis for a non-technical user.
Generate a JSON object with the following keys: "architecture", "parameters", "strengths" (array of 3 strings), "weaknesses" (array of 2 strings), "trainCost", "trainTime", "accuracy", "expertOpinion", "icon".
- For icon, choose a single relevant emoji.
- For trainCost, estimate a range (e.g., "$5-10").
- For trainTime, estimate a time (e.g., "~30 min").
- For accuracy, provide a qualitative rating (e.g., "High (95%+)").
- Be realistic and base your analysis on the model's known characteristics.

Model Info:
{model_info}
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
        for i, model in enumerate(models):
            # Stage 3: AI-driven data enrichment for each model
            enrichment_prompt = ENRICHMENT_PROMPT.format(model_info=str(model))
            
            enrichment_response = await openai.Completion.acreate(
                engine="gpt-4o-mini", # Or any suitable model
                prompt=enrichment_prompt,
                max_tokens=50,
                temperature=0.2,
                stop=None
            )
            enriched_data = json.loads(enrichment_response.choices[0].text.strip())

            recommendations.append(ModelRecommendation(
                modelId=model.modelId,
                name=model.modelId.split('/')[-1], # Simplified name
                author=model.author,
                description=getattr(model, 'description', 'No description available.'),
                recommended=(i == 0), # Mark the top result as recommended
                **enriched_data
            ))
            
        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 