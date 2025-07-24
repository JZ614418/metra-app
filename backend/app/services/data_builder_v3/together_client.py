# together_client.py
import httpx
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from collections import deque
import json
import tenacity

logger = logging.getLogger(__name__)

class TogetherRateLimiter:
    """TogetherAI速率限制器"""
    
    def __init__(self, rpm_limit: int = 3000, tpm_limit: int = 150000):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        
        # 请求历史 (时间戳, token数)
        self.request_history = deque()
        self.token_history = deque()
        
        # 当前窗口统计
        self.current_rpm = 0
        self.current_tpm = 0
        
        # 锁
        self.lock = asyncio.Lock()
    
    async def acquire(self, estimated_tokens: int = 1000):
        """获取API调用权限"""
        async with self.lock:
            now = time.time()
            
            # 清理过期记录
            self._cleanup_history(now)
            
            # 检查是否超过限制
            if self.current_rpm >= self.rpm_limit:
                wait_time = 60 - (now - self.request_history[0])
                logger.warning(f"TogetherAI RPM限制，等待{wait_time:.1f}秒")
                await asyncio.sleep(wait_time)
                return await self.acquire(estimated_tokens)
            
            if self.current_tpm + estimated_tokens > self.tpm_limit:
                wait_time = 60 - (now - self.token_history[0][0])
                logger.warning(f"TogetherAI TPM限制，等待{wait_time:.1f}秒")
                await asyncio.sleep(wait_time)
                return await self.acquire(estimated_tokens)
            
            # 记录请求
            self.request_history.append(now)
            self.token_history.append((now, estimated_tokens))
            self.current_rpm += 1
            self.current_tpm += estimated_tokens
    
    def _cleanup_history(self, now: float):
        """清理过期的历史记录"""
        # 清理RPM历史
        while self.request_history and now - self.request_history[0] > 60:
            self.request_history.popleft()
        self.current_rpm = len(self.request_history)
        
        # 清理TPM历史
        while self.token_history and now - self.token_history[0][0] > 60:
            _, tokens = self.token_history.popleft()
            self.current_tpm -= tokens
    
    def get_current_usage(self) -> Dict[str, Any]:
        """获取当前使用情况"""
        return {
            "rpm": self.current_rpm,
            "rpm_limit": self.rpm_limit,
            "tpm": self.current_tpm,
            "tpm_limit": self.tpm_limit,
            "rpm_usage": self.current_rpm / self.rpm_limit,
            "tpm_usage": self.current_tpm / self.tpm_limit
        }

class TogetherClient:
    def __init__(self, api_key: str, base_url: str = "https://api.together.xyz/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60.0)
        self.rate_limiter = TogetherRateLimiter()
    
    async def generate_chat(
        self, 
        prompt: str, 
        model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1",
        max_tokens: int = 1500, 
        temperature: float = 0.3
    ) -> str:
        """使用Chat API生成文本"""
        try:
            # 等待速率限制
            await self.rate_limiter.acquire(estimated_tokens=max_tokens)
            
            response = await self._call_api_with_retry(
                f"{self.base_url}/chat/completions",
                {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1
                }
            )
            
            return response["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"TogetherAI Chat客户端错误: {e}")
            raise
    
    async def generate(
        self, 
        prompt: str, 
        model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1",
        max_tokens: int = 1500, 
        temperature: float = 0.3
    ) -> str:
        """使用Completions API生成文本"""
        try:
            # 等待速率限制
            await self.rate_limiter.acquire(estimated_tokens=max_tokens)
            
            response = await self._call_api_with_retry(
                f"{self.base_url}/completions",
                {
                    "model": model,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1
                }
            )
            
            return response["choices"][0]["text"]
                
        except Exception as e:
            logger.error(f"TogetherAI客户端错误: {e}")
            raise
    
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=8),
        retry=tenacity.retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError))
    )
    async def _call_api_with_retry(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """带重试的API调用"""
        try:
            response = await self.client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 速率限制错误，等待更长时间
                logger.warning(f"TogetherAI速率限制: {response.status_code}")
                await asyncio.sleep(5)
                raise httpx.HTTPStatusError("Rate limited", request=response.request, response=response)
            else:
                logger.error(f"TogetherAI API错误: {response.status_code} - {response.text}")
                raise httpx.HTTPStatusError(f"API错误: {response.status_code}", request=response.request, response=response)
                
        except httpx.RequestError as e:
            logger.error(f"TogetherAI请求错误: {e}")
            raise
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """获取速率限制状态"""
        return self.rate_limiter.get_current_usage()
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()