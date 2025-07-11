import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 打印环境变量
api_key = os.getenv("OPENAI_API_KEY")
print(f"从环境变量读取的API密钥: {api_key[:20]}..." if api_key else "未找到API密钥")

# 导入配置并检查
import sys
sys.path.insert(0, '..')
from app.core.config import settings

print(f"从settings读取的API密钥: {settings.OPENAI_API_KEY[:20]}...")
