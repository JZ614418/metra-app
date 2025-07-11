"""
AI Data Generation Service
Uses OpenAI to generate high-quality training data
"""

from openai import AsyncOpenAI
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings


class DataGenerationService:
    """AI-powered data generation service"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_training_data(
        self, 
        task_type: str,
        task_description: str,
        count: int = 100,
        labels: Optional[List[str]] = None,
        examples: Optional[List[Dict]] = None,
        style: str = "balanced"
    ) -> List[Dict]:
        """Generate training data using AI"""
        
        # Build the prompt based on task
        prompt = self._build_generation_prompt(
            task_type, task_description, labels, examples, style
        )
        
        generated_data = []
        
        if labels:
            # Generate balanced data for each label
            per_label = count // len(labels)
            
            for label in labels:
                label_prompt = f"{prompt}\n\nGenerate {per_label} examples for the label '{label}'."
                
                # Generate in batches
                batch_size = 10
                for i in range(0, per_label, batch_size):
                    batch_count = min(batch_size, per_label - i)
                    
                    try:
                        response = await self._call_openai(
                            label_prompt + f"\n\nGenerate {batch_count} diverse examples."
                        )
                        
                        # Parse the response
                        examples = self._parse_generation_response(response)
                        
                        for example in examples[:batch_count]:
                            generated_data.append({
                                'content': example,
                                'label': label,
                                'source': 'ai_generated',
                                'model': 'gpt-3.5-turbo',
                                'timestamp': datetime.utcnow().isoformat()
                            })
                    
                    except Exception as e:
                        print(f"Generation error: {e}")
                        # Generate fallback data
                        for j in range(batch_count):
                            generated_data.append({
                                'content': f"Sample {label} text {i+j}",
                                'label': label,
                                'source': 'ai_generated_fallback',
                                'timestamp': datetime.utcnow().isoformat()
                            })
                    
                    await asyncio.sleep(0.5)  # Rate limiting
        
        else:
            # Generate unlabeled data
            batch_size = 20
            for i in range(0, count, batch_size):
                batch_count = min(batch_size, count - i)
                
                try:
                    response = await self._call_openai(
                        prompt + f"\n\nGenerate {batch_count} diverse examples."
                    )
                    
                    examples = self._parse_generation_response(response)
                    
                    for example in examples[:batch_count]:
                        generated_data.append({
                            'content': example,
                            'source': 'ai_generated',
                            'model': 'gpt-3.5-turbo',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                
                except Exception as e:
                    print(f"Generation error: {e}")
                    # Generate fallback data
                    for j in range(batch_count):
                        generated_data.append({
                            'content': f"Generated sample {i+j}",
                            'source': 'ai_generated_fallback',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                
                await asyncio.sleep(0.5)
        
        return generated_data
    
    def _build_generation_prompt(
        self,
        task_type: str,
        description: str,
        labels: Optional[List[str]],
        examples: Optional[List[Dict]],
        style: str
    ) -> str:
        """Build prompt for data generation"""
        
        prompt = f"Generate training data for the following task:\n"
        prompt += f"Task Type: {task_type}\n"
        prompt += f"Description: {description}\n"
        
        if labels:
            prompt += f"Labels: {', '.join(labels)}\n"
        
        if style:
            prompt += f"Style: {style}\n"
        
        # Add task-specific instructions
        if 'sentiment' in task_type.lower():
            prompt += "\nGenerate realistic text samples that clearly express the sentiment."
            prompt += "\nInclude both short and long texts, formal and informal styles."
        
        elif 'classification' in task_type.lower():
            prompt += "\nGenerate diverse examples that clearly belong to their categories."
            prompt += "\nVary the length, style, and complexity."
        
        elif 'qa' in task_type.lower():
            prompt += "\nGenerate question-answer pairs relevant to the topic."
            prompt += "\nInclude different types of questions (what, how, why, etc.)"
        
        if examples:
            prompt += "\n\nHere are some examples of the desired format:\n"
            for ex in examples[:3]:
                prompt += f"- {ex.get('content', '')}\n"
        
        prompt += "\nGenerate diverse, realistic examples. Return only the text content, one per line."
        
        return prompt
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            # In production, use actual API call
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates training data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1000
            )
            return response.choices[0].message.content
            
            # Fallback to mock data if API fails
            
            # Mock response for testing
            if 'sentiment' in prompt.lower():
                if 'positive' in prompt.lower():
                    return """Great product! Exceeded my expectations.
Love the quality and fast shipping.
Excellent customer service, highly recommend!
Amazing experience, will definitely buy again.
Perfect! Exactly what I was looking for."""
                elif 'negative' in prompt.lower():
                    return """Terrible quality, very disappointed.
Worst purchase ever, complete waste of money.
Customer service was rude and unhelpful.
Product broke after one day of use.
Never buying from this company again."""
                else:
                    return """The product is okay, nothing special.
Average quality for the price.
Shipping was on time, product as described.
It works, but could be better.
Neutral experience overall."""
            
            elif 'classification' in prompt.lower():
                return """This is a sample text for classification.
Another example with different characteristics.
Here's a third sample with unique features.
Classification example number four.
Final sample for the classification task."""
            
            else:
                return """Generated sample text.
Another generated example.
Third sample of generated content.
Fourth example text.
Fifth and final sample."""
        
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise
    
    def _parse_generation_response(self, response: str) -> List[str]:
        """Parse AI response into individual examples"""
        # Split by newlines and filter empty lines
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        # Remove any numbering or bullet points
        cleaned_lines = []
        for line in lines:
            # Remove common prefixes
            line = line.lstrip('- •·123456789.')
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        return cleaned_lines
    
    async def augment_existing_data(
        self,
        existing_data: List[Dict],
        augmentation_factor: int = 2
    ) -> List[Dict]:
        """Augment existing data with variations"""
        
        augmented_data = []
        
        for item in existing_data:
            # Keep original
            augmented_data.append(item)
            
            # Generate variations
            content = item.get('content', '')
            label = item.get('label')
            
            prompt = f"Generate {augmentation_factor} variations of this text while keeping the same meaning:\n'{content}'"
            
            try:
                response = await self._call_openai(prompt)
                variations = self._parse_generation_response(response)
                
                for var in variations[:augmentation_factor]:
                    augmented_data.append({
                        'content': var,
                        'label': label,
                        'source': 'ai_augmented',
                        'original_id': item.get('id'),
                        'timestamp': datetime.utcnow().isoformat()
                    })
            
            except Exception as e:
                print(f"Augmentation error: {e}")
                # Simple augmentation fallback
                augmented_data.append({
                    'content': content.upper(),
                    'label': label,
                    'source': 'simple_augmented',
                    'original_id': item.get('id')
                })
        
        return augmented_data


# Singleton instance
data_generation_service = DataGenerationService() 