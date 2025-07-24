# r1_client.py
import httpx
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DeepSeekR1Client:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.3) -> str:
        """调用DeepSeek R1生成文本"""
        try:
            response = await self.client.post(
                f"{self.api_url}/generate",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["response"]
            else:
                logger.error(f"R1 API调用失败: {response.status_code} - {response.text}")
                raise Exception(f"R1 API调用失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"R1客户端错误: {e}")
            raise
    
    async def health_check(self) -> bool:
        """检查服务是否健康"""
        try:
            response = await self.client.get(f"{self.api_url}/health")
            return response.status_code == 200
        except:
            return False
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()