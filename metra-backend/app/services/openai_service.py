import os
import json
from typing import List, Dict, Optional, AsyncGenerator
from openai import AsyncOpenAI
from app.models.message import Message, MessageRole
from app.core.config import settings

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = AsyncOpenAI(api_key=api_key)
        
    def get_system_prompt(self) -> str:
        """获取系统提示词，指导AI如何进行对话"""
        return """You are a Data Structure Expert AI assistant for Metra, an AI training platform. Your role is to help users define clear and comprehensive data structures (JSON schemas) for their AI model training tasks.

Your conversation should follow this pattern:
1. Understand the user's task and goals
2. Ask clarifying questions to gather necessary details
3. When you have enough information, generate a complete JSON schema

Guidelines:
- Be friendly and professional
- Ask one or two focused questions at a time
- Consider data types, required fields, validation rules, and examples
- Think about the AI model that will use this data
- When ready to generate a schema, indicate it clearly

When you determine that you have enough information, respond with:
"I now have enough information to create your data schema. Here's what I've designed based on our discussion:"

Then provide the JSON schema in a code block marked as ```json```."""

    async def get_ai_response(self, messages: List[Message]) -> str:
        """获取AI的回复"""
        # 构建消息历史
        conversation_messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        for msg in messages:
            conversation_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # 调用OpenAI API
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=conversation_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content

    async def get_ai_response_stream(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """获取AI的流式回复"""
        # 构建消息历史
        conversation_messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        for msg in messages:
            conversation_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # 调用OpenAI API with streaming
        stream = await self.client.chat.completions.create(
            model="gpt-4",
            messages=conversation_messages,
            temperature=0.7,
            max_tokens=1000,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def extract_json_schema(self, content: str) -> Optional[Dict]:
        """从AI回复中提取JSON Schema"""
        # 查找```json```代码块
        import re
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, content)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                return None
        
        return None

    def is_schema_complete(self, content: str) -> bool:
        """判断AI是否已经生成了完整的schema"""
        # 检查是否包含特定的标识词
        indicators = [
            "I now have enough information",
            "Here's what I've designed",
            "```json"
        ]
        
        return any(indicator in content for indicator in indicators) 