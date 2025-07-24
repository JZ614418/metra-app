# llama_client.py
import httpx
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LlamaClient:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        # 如果是RunPod代理有问题，我们可以临时使用一个工作的备用方案
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def generate(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.3) -> str:
        """调用Llama 3.1 70B生成文本"""
        try:
            response = await self.client.post(
                f"{self.api_url}/v1/completions",
                json={
                    "model": "neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stop": ["</s>"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["text"]
            else:
                logger.error(f"Llama API调用失败: {response.status_code} - {response.text}")
                raise Exception(f"Llama API调用失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Llama客户端错误: {e}")
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