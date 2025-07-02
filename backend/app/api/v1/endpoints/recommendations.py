from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import openai
import json
from huggingface_hub import list_models, ModelFilter

from app import schemas
from app.api import deps
from app.models.user import User
from app.core.config import settings

router = APIRouter()

# System prompt for AI to extract search keywords
KEYWORD_EXTRACTION_PROMPT = """You are a Hugging Face model curator expert. Your task is to analyze a task definition JSON and extract the most relevant keywords for searching models on Hugging Face Hub.

Guidelines:
1. Extract keywords that will help find the most suitable models
2. Consider task type, domain, language, performance requirements
3. Include both general and specific terms
4. Format: Return ONLY a comma-separated string of keywords
5. Prioritize keywords that are commonly used in Hugging Face model tags

Examples:
- For a medical NER task in Chinese: "token-classification, ner, chinese, medical, biomedical, accuracy"
- For sentiment analysis on product reviews: "text-classification, sentiment-analysis, product-reviews, e-commerce"
- For image classification of animals: "image-classification, animals, wildlife, computer-vision"
"""


@router.post("/recommend", response_model=schemas.conversation.ModelRecommendationResponse)
def get_model_recommendations(
    *,
    db: Session = Depends(deps.get_db),
    recommendation_request: schemas.conversation.ModelRecommendationRequest,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get model recommendations based on task definition.
    Two-stage process:
    1. Use AI to extract relevant search keywords from task definition
    2. Search Hugging Face Hub using these keywords
    """
    
    try:
        # Stage 1: Use AI to extract search keywords
        openai.api_key = settings.OPENAI_API_KEY
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": KEYWORD_EXTRACTION_PROMPT},
                {"role": "user", "content": f"Task definition:\n{json.dumps(recommendation_request.task_definition, indent=2)}"}
            ],
            temperature=0.3,  # Lower temperature for more consistent keyword extraction
            max_tokens=100
        )
        
        search_keywords = response.choices[0].message.content.strip()
        
        # Stage 2: Search Hugging Face Hub
        # Search for models using the AI-generated keywords
        models = list_models(
            search=search_keywords,
            sort="downloads",  # Sort by popularity
            direction=-1,  # Descending order
            limit=5  # Get top 5 models
        )
        
        # Format the results
        recommendations = []
        for model in models:
            recommendation = schemas.conversation.ModelRecommendation(
                model_id=model.modelId,
                model_name=model.modelId.split('/')[-1] if '/' in model.modelId else model.modelId,
                description=getattr(model, 'description', None),
                tags=getattr(model, 'tags', []),
                downloads=getattr(model, 'downloads', 0),
                likes=getattr(model, 'likes', 0),
                author=model.modelId.split('/')[0] if '/' in model.modelId else None
            )
            recommendations.append(recommendation)
        
        # If no models found, provide some default recommendations based on task type
        if not recommendations:
            task_type = recommendation_request.task_definition.get('task_type', '').lower()
            
            # Default recommendations for common task types
            default_models = {
                'text-classification': [
                    {
                        "model_id": "distilbert-base-uncased-finetuned-sst-2-english",
                        "model_name": "DistilBERT SST-2",
                        "description": "A distilled version of BERT fine-tuned on sentiment analysis",
                        "tags": ["text-classification", "sentiment-analysis", "distilbert"],
                        "downloads": 1000000,
                        "likes": 100
                    },
                    {
                        "model_id": "bert-base-uncased",
                        "model_name": "BERT base uncased",
                        "description": "BERT base model, suitable for fine-tuning on various tasks",
                        "tags": ["bert", "text-classification", "english"],
                        "downloads": 5000000,
                        "likes": 500
                    }
                ],
                'token-classification': [
                    {
                        "model_id": "dslim/bert-base-NER",
                        "model_name": "BERT NER",
                        "description": "BERT fine-tuned on NER task",
                        "tags": ["token-classification", "ner", "bert"],
                        "downloads": 500000,
                        "likes": 50
                    }
                ],
                'question-answering': [
                    {
                        "model_id": "distilbert-base-cased-distilled-squad",
                        "model_name": "DistilBERT SQuAD",
                        "description": "DistilBERT fine-tuned on SQuAD for question answering",
                        "tags": ["question-answering", "squad", "distilbert"],
                        "downloads": 800000,
                        "likes": 80
                    }
                ]
            }
            
            if task_type in default_models:
                for model_data in default_models[task_type]:
                    recommendations.append(schemas.conversation.ModelRecommendation(**model_data))
        
        return schemas.conversation.ModelRecommendationResponse(
            recommendations=recommendations,
            search_keywords=search_keywords
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting model recommendations: {str(e)}"
        ) 