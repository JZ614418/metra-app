from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
import json
from huggingface_hub import list_models
import re

from app import schemas
from app.api import deps
from app.models.user import User
from app.core.config import settings

router = APIRouter()

# System prompt for AI to extract search keywords
KEYWORD_EXTRACTION_PROMPT = """You are a Hugging Face model curator expert. Your task is to analyze a task definition JSON and extract the most relevant keywords for searching models on Hugging Face Hub.

CRITICAL: Pay special attention to the "language" field in the task definition. This is the most important factor.

Guidelines:
1. LANGUAGE FIRST: If the task specifies "chinese" or "中文", prioritize Chinese model keywords:
   - Start with: "chinese", "zh", "中文"
   - Include Chinese model names: "chatglm", "baichuan", "qwen", "chinese-llama", "chinese-alpaca", "yi", "bloom-zh"
   - For medical/health tasks in Chinese, add: "medical-chinese", "health-chinese", "huatuo", "bianque"

2. Extract keywords that match Hugging Face model naming conventions and tags
3. Focus on task types that exist on Hugging Face (text-generation, text-classification, etc.)
4. Include model architecture names when relevant (gpt2, bert, llama, etc.)
5. Format: Return ONLY a comma-separated string of keywords
6. Return keywords in order from most specific to most general
7. Language-specific models should always come before general models

Examples:
- For {"language": "chinese", "task": "medical advice"}: "chinese, zh, chatglm, baichuan, qwen, huatuo, medical, health, text-generation, chinese-llama"
- For {"language": "english", "task": "sentiment analysis"}: "english, en, sentiment-analysis, text-classification, bert, roberta"
- For {"language": "chinese", "task": "饮食建议"}: "chinese, zh, chatglm, baichuan, health, dietary, text-generation, chinese-alpaca, yi"

Remember: If the language is Chinese, prioritize Chinese models (ChatGLM, Baichuan, Qwen, Yi) over general models.
"""

# Model filtering configurations
EXCLUDED_MODEL_TYPES = [
    'audio', 'speech', 'wav2vec', 'whisper', 'asr',  # Audio models
    'vision', 'image', 'clip', 'vit', 'resnet',      # Vision models
    'video', 'videomae',                              # Video models
    'multimodal',                                     # Multimodal models (unless specifically needed)
]

def extract_keywords_simple(task_definition):
    """
    Simple keyword extraction fallback when AI is unavailable.
    Analyzes task definition using rule-based patterns.
    """
    keywords = []
    task_str = str(task_definition).lower()
    
    # Language detection
    chinese_indicators = ['中', '医', '中文', 'chinese', '中医', '饮食', '养生', '诊断', '治疗']
    if any(indicator in task_str for indicator in chinese_indicators):
        keywords.extend(['chinese', 'zh', 'chatglm', 'baichuan', 'qwen', 'yi'])
        print("🇨🇳 Detected Chinese task")
    else:
        keywords.extend(['english', 'en'])
        print("🇺🇸 Detected English task")
    
    # Domain/Task type detection
    if any(word in task_str for word in ['medical', '医疗', 'health', '健康', '医', 'tcm', '中医']):
        keywords.extend(['medical', 'health', 'biomedical', 'clinical'])
        print("🏥 Detected medical domain")
    elif any(word in task_str for word in ['code', '代码', 'programming', 'python', 'javascript']):
        keywords.extend(['code', 'programming', 'codellama', 'starcoder'])
        print("💻 Detected coding domain")
    elif any(word in task_str for word in ['chat', '对话', 'conversation', 'dialog']):
        keywords.extend(['chat', 'conversation', 'instruct', 'assistant'])
        print("💬 Detected chat domain")
    elif any(word in task_str for word in ['sentiment', '情感', 'emotion', 'feeling']):
        keywords.extend(['sentiment', 'emotion', 'classification'])
        print("😊 Detected sentiment domain")
    elif any(word in task_str for word in ['translate', '翻译', 'translation']):
        keywords.extend(['translation', 'multilingual'])
        print("🌍 Detected translation domain")
    
    # Always add general text generation
    keywords.extend(['text-generation', 'language-model', 'llm'])
    
    # Remove duplicates and join
    unique_keywords = list(dict.fromkeys(keywords))
    return ', '.join(unique_keywords)

CHINESE_MODEL_KEYWORDS = [
    'chatglm', 'baichuan', 'qwen', 'yi', 'chinese-llama', 'chinese-alpaca',
    'bloom-zh', 'pangu', 'ernie', 'nezha', 'macbert', 'wobert',
    'huatuo', 'bianque', 'shennong',  # Medical Chinese models
    'luotuo', 'ziya', 'aquila',        # Other Chinese models
]

TASK_TYPE_MAPPING = {
    'text-generation': ['text-generation', 'causal-lm', 'text2text-generation'],
    'text-classification': ['text-classification', 'sentiment-analysis', 'zero-shot-classification'],
    'token-classification': ['token-classification', 'ner', 'named-entity-recognition'],
    'question-answering': ['question-answering', 'qa'],
    'summarization': ['summarization', 'text2text-generation'],
    'translation': ['translation', 'text2text-generation'],
}


def is_model_relevant(model, task_type: str, language: str, domain: str) -> bool:
    """Check if a model is relevant for the given task requirements."""
    model_id_lower = model.modelId.lower()
    model_tags = [tag.lower() for tag in getattr(model, 'tags', [])]
    
    # Exclude irrelevant model types
    for excluded in EXCLUDED_MODEL_TYPES:
        if excluded in model_id_lower or excluded in model_tags:
            # Exception: multimodal is OK if specifically requested
            if excluded == 'multimodal' and 'multimodal' in str(task_type).lower():
                continue
            return False
    
    # For Chinese language requirement
    if language == 'chinese':
        # Must have Chinese model indicators
        has_chinese = any(cn in model_id_lower for cn in ['chinese', 'zh', 'cn'] + CHINESE_MODEL_KEYWORDS)
        if not has_chinese:
            # Check tags as well
            has_chinese = any(cn in tag for tag in model_tags for cn in ['chinese', 'zh', 'cn'])
        if not has_chinese:
            return False
    
    # Check task type compatibility
    if task_type in TASK_TYPE_MAPPING:
        acceptable_tags = TASK_TYPE_MAPPING[task_type]
        has_task_match = any(tag in model_tags for tag in acceptable_tags)
        # Also check model ID for task indicators
        if not has_task_match:
            has_task_match = any(task in model_id_lower for task in acceptable_tags)
        # For text-generation, be more lenient
        if not has_task_match and task_type == 'text-generation':
            # Accept general language models
            general_lm_indicators = ['gpt', 'llama', 'llm', 'lm', 'chatglm', 'baichuan', 'qwen']
            has_task_match = any(ind in model_id_lower for ind in general_lm_indicators)
    else:
        has_task_match = True  # If task type not specified, don't filter by it
    
    return has_task_match


@router.post("/recommend", response_model=schemas.conversation.ModelRecommendationResponse)
async def get_model_recommendations(
    *,
    db: Session = Depends(deps.get_db),
    recommendation_request: schemas.conversation.ModelRecommendationRequest,
    # current_user: User = Depends(deps.get_current_user)  # Temporarily disabled for testing
) -> Any:
    """
    Get model recommendations based on task definition.
    Two-stage process:
    1. Use AI to extract relevant search keywords from task definition
    2. Search Hugging Face Hub using these keywords with smart filtering
    """
    
    # Hybrid Strategy: AI first, fallback to simple keyword extraction
    search_keywords = None
    
    try:
        # Strategy 1: Use AI to extract search keywords (Primary)
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": KEYWORD_EXTRACTION_PROMPT},
                {"role": "user", "content": f"Task definition:\n{json.dumps(recommendation_request.task_definition, indent=2)}"}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        search_keywords = response.choices[0].message.content.strip()
        print(f"✅ AI generated keywords: {search_keywords}")
        
    except Exception as ai_error:
        # Strategy 2: Fallback to simple keyword extraction
        print(f"⚠️ AI keyword extraction failed, using fallback: {ai_error}")
        search_keywords = extract_keywords_simple(recommendation_request.task_definition)
        print(f"📝 Fallback keywords: {search_keywords}")
    
    # Stage 2: Search Hugging Face Hub with prioritized strategy (works for both AI and fallback)
    # Extract task requirements
    task_type = 'text-generation'  # default
    language = 'english'  # default
    domain = 'general'  # default
    
    if isinstance(recommendation_request.task_definition, dict):
        # Try to extract structured fields
        task_type = recommendation_request.task_definition.get('task_type', 'text-generation').lower()
        language = recommendation_request.task_definition.get('language', 'english').lower()
        domain = recommendation_request.task_definition.get('domain', 'general').lower()
        
        # Auto-detect language from task description if not specified
        task_str = str(recommendation_request.task_definition).lower()
        
        # Check if language field is not explicitly set
        if 'language' not in recommendation_request.task_definition:
            # Check for Chinese characters in any field
            chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
            full_str = json.dumps(recommendation_request.task_definition, ensure_ascii=False)
            if chinese_pattern.search(full_str):
                language = 'chinese'
                print(f"Auto-detected Chinese language from task content")
            
            # Also check for language indicators in the content
            if 'chinese' in task_str or '中文' in task_str or '中医' in task_str:
                language = 'chinese'
            if 'health' in task_str or '健康' in task_str or '医' in task_str:
                domain = 'health'
            if 'legal' in task_str or '法律' in task_str or '法' in task_str:
                domain = 'legal'
            if 'education' in task_str or '教育' in task_str or '教学' in task_str:
                domain = 'education'
            if 'finance' in task_str or '金融' in task_str or '财务' in task_str:
                domain = 'finance'
                
        print(f"Task requirements - Type: {task_type}, Language: {language}, Domain: {domain}")
        
        # Build search strategy based on requirements
        search_strategies = []
        
        # Strategy 1: Most specific - all requirements
        if task_type == 'text-generation' and language == 'chinese' and domain == 'health':
            search_strategies.append({
                'name': 'Chinese health text generation',
                'keywords': ['chinese medical text-generation', 'chinese health llm', '中医 模型'],
                'model_names': ['huatuo', 'bianque', 'shennong', 'chatglm-med', 'baichuan-health', 'medical-gpt']
            })
        
        # Strategy 2: Task type + Language
        if task_type == 'text-generation' and language == 'chinese':
            search_strategies.append({
                'name': 'Chinese text generation',
                'keywords': ['chinese text-generation', 'chinese llm', 'chinese language model'],
                'model_names': ['chatglm', 'baichuan', 'qwen', 'yi', 'chinese-llama', 'chinese-alpaca', 'bloom-zh', 'pangu', 'aquila']
            })
        
        # Strategy 3: Task type + Domain (for any language)
        if task_type == 'text-generation' and domain == 'health':
            search_strategies.append({
                'name': 'Health text generation',
                'keywords': ['medical text-generation', 'health llm', 'biomedical language model'],
                'model_names': ['biogpt', 'medalpaca', 'clinical-bert', 'pubmedbert']
            })
        
        # Strategy 4: General task type
        search_strategies.append({
            'name': 'General text generation',
            'keywords': [task_type, 'language-model', 'llm'],
            'model_names': ['gpt2', 'bloom', 'opt', 'llama', 'falcon', 'mpt']
        })
        
        # Execute search strategies in order
        models_dict = {}
        
        for strategy in search_strategies:
            print(f"\nTrying strategy: {strategy['name']}")
            
            # Try specific model names first
            for model_name in strategy['model_names']:
                if len(models_dict) >= 15:  # Increase limit for better selection
                    break
                    
                try:
                    models = list(list_models(
                        search=model_name,
                        sort="downloads",
                        direction=-1,
                        limit=5
                    ))
                    
                    for model in models:
                        # Apply relevance filter
                        if is_model_relevant(model, task_type, language, domain):
                            models_dict[model.modelId] = model
                            print(f"Added model: {model.modelId}")
                        else:
                            print(f"Filtered out: {model.modelId}")
                        
                except Exception as e:
                    print(f"Error searching for {model_name}: {str(e)}")
            
            # Try keyword search
            for keyword in strategy['keywords']:
                if len(models_dict) >= 15:
                    break
                    
                try:
                    models = list(list_models(
                        search=keyword,
                        sort="downloads",
                        direction=-1,
                        limit=5
                    ))
                    
                    for model in models:
                        if model.modelId not in models_dict:
                            # Apply relevance filter
                            if is_model_relevant(model, task_type, language, domain):
                                models_dict[model.modelId] = model
                                print(f"Added model from keyword '{keyword}': {model.modelId}")
                            
                except Exception as e:
                    print(f"Error searching with keyword {keyword}: {str(e)}")
        
        # If still not enough models, use the original keyword-based search
        if len(models_dict) < 5:
            print("\nFalling back to keyword-based search...")
            keyword_list = [k.strip() for k in search_keywords.split(",") if k.strip()]
            
            # Try progressively reducing keywords
            for i in range(len(keyword_list), 0, -1):
                if len(models_dict) >= 10:
                    break
                    
                current_keywords = keyword_list[:i]
                search_query = " ".join(current_keywords)
                
                try:
                    models = list(list_models(
                        search=search_query,
                        sort="downloads",
                        direction=-1,
                        limit=5
                    ))
                    
                    if models:
                        print(f"Found {len(models)} models with {i} keywords: {search_query}")
                        for model in models:
                            if model.modelId not in models_dict:
                                # Apply relevance filter
                                if is_model_relevant(model, task_type, language, domain):
                                    models_dict[model.modelId] = model
                                
                except Exception as e:
                    print(f"Error searching with {search_query}: {str(e)}")
        
        # Convert dict back to list and sort by relevance
        all_models = list(models_dict.values())
        
        # Sort models by relevance (Chinese models first for Chinese tasks)
        if language == 'chinese':
            def chinese_priority(model):
                model_id_lower = model.modelId.lower()
                # Priority order for Chinese models
                for i, keyword in enumerate(CHINESE_MODEL_KEYWORDS):
                    if keyword in model_id_lower:
                        return i
                return 999  # Lower priority for non-Chinese models
            
            all_models.sort(key=lambda m: (chinese_priority(m), -getattr(m, 'downloads', 0)))
        else:
            # Sort by downloads for non-Chinese tasks
            all_models.sort(key=lambda m: -getattr(m, 'downloads', 0))
        
        # Limit to top 10 models
        all_models = all_models[:10]
        
        print(f"Total unique models found: {len(all_models)}")
        
        # Format the results
        recommendations = []
        for model in all_models:
            # Get model card info if available
            model_card = getattr(model, 'card_data', {}) or {}
            
            recommendation = schemas.conversation.ModelRecommendation(
                model_id=model.modelId,
                model_name=model.modelId.split('/')[-1] if '/' in model.modelId else model.modelId,
                description=getattr(model, 'description', None) or model_card.get('description', f'Popular model with {getattr(model, "downloads", 0):,} downloads'),
                tags=getattr(model, 'tags', []),
                downloads=getattr(model, 'downloads', 0),
                likes=getattr(model, 'likes', 0),
                author=model.modelId.split('/')[0] if '/' in model.modelId else None,
                # Add additional metadata
                pipeline_tag=getattr(model, 'pipeline_tag', None),
                library_name=getattr(model, 'library_name', None)
            )
            recommendations.append(recommendation)
        
        # If no models found, provide better default recommendations
        if not recommendations:
            if language == 'chinese':
                # Chinese default models
                default_models = [
                    {
                        "model_id": "THUDM/chatglm3-6b",
                        "model_name": "ChatGLM3-6B",
                        "description": "ChatGLM3 is a conversational pre-trained model jointly released by Zhipu AI and Tsinghua University KEG Lab",
                        "tags": ["text-generation", "chinese", "chatglm"],
                        "downloads": 1000000,
                        "likes": 1000,
                        "author": "THUDM"
                    },
                    {
                        "model_id": "baichuan-inc/Baichuan2-7B-Chat",
                        "model_name": "Baichuan2-7B-Chat",
                        "description": "Large-scale pre-trained language model developed by Baichuan Intelligence with open source commercial license",
                        "tags": ["text-generation", "chinese", "baichuan"],
                        "downloads": 500000,
                        "likes": 500,
                        "author": "baichuan-inc"
                    },
                    {
                        "model_id": "Qwen/Qwen-7B-Chat",
                        "model_name": "Qwen-7B-Chat",
                        "description": "Tongyi Qianwen is a large language model developed by Alibaba Cloud",
                        "tags": ["text-generation", "chinese", "qwen"],
                        "downloads": 800000,
                        "likes": 800,
                        "author": "Qwen"
                    }
                ]
            else:
                # English default models
                default_models = [
                    {
                        "model_id": "meta-llama/Llama-2-7b-chat-hf",
                        "model_name": "Llama-2-7B-Chat",
                        "description": "Llama 2 is a collection of pretrained and fine-tuned generative text models",
                        "tags": ["text-generation", "llama", "english"],
                        "downloads": 5000000,
                        "likes": 5000,
                        "author": "meta-llama"
                    },
                    {
                        "model_id": "mistralai/Mistral-7B-Instruct-v0.1",
                        "model_name": "Mistral-7B-Instruct",
                        "description": "The Mistral-7B-Instruct Large Language Model",
                        "tags": ["text-generation", "mistral", "english"],
                        "downloads": 3000000,
                        "likes": 3000,
                        "author": "mistralai"
                    }
                ]
            
            for model_data in default_models:
                    recommendations.append(schemas.conversation.ModelRecommendation(**model_data))
        
        return schemas.conversation.ModelRecommendationResponse(
            recommendations=recommendations,
            search_keywords=search_keywords
        )
 