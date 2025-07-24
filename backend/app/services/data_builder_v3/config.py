"""
DataBuilder V3 配置管理
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import json
import os

# 导入主配置
try:
    from app.core.config import settings
except ImportError:
    settings = None

@dataclass
class OpenAIConfig:
    """OpenAI配置"""
    api_key: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    base_url: str = "https://api.openai.com/v1"
    
    def __post_init__(self):
        if settings and hasattr(settings, 'OPENAI_API_KEY'):
            self.api_key = settings.OPENAI_API_KEY
        else:
            self.api_key = os.getenv("OPENAI_API_KEY", "")

@dataclass
class TogetherAIConfig:
    """TogetherAI配置"""
    api_key: str = ""
    models: Dict[str, str] = None
    temperature: float = 0.3
    max_tokens: int = 1500
    base_url: str = "https://api.together.xyz/v1"
    
    def __post_init__(self):
        if settings and hasattr(settings, 'TOGETHER_API_KEY'):
            self.api_key = settings.TOGETHER_API_KEY
        else:
            self.api_key = os.getenv("TOGETHER_API_KEY", "")
        
        if self.models is None:
            self.models = {
                "high_quality": "meta-llama/Llama-2-70b-chat-hf",
                "balanced": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "fast": "meta-llama/Llama-2-13b-chat-hf"
            }

@dataclass
class SearchEngineConfig:
    """搜索引擎配置"""
    # Google Custom Search API
    google_search_api_key: str = ""
    google_search_cx: str = ""
    
    # 搜索引擎优先级
    enabled_engines: List[str] = None
    
    # 搜索参数
    max_results_per_engine: int = 10
    search_timeout: float = 10.0
    
    # 用户代理
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    def __post_init__(self):
        # 从settings读取Google Search API配置
        if settings and hasattr(settings, 'GOOGLE_SEARCH_API_KEY'):
            self.google_search_api_key = settings.GOOGLE_SEARCH_API_KEY
            self.google_search_cx = getattr(settings, 'GOOGLE_SEARCH_CX', "")
        else:
            self.google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "")
            self.google_search_cx = os.getenv("GOOGLE_SEARCH_CX", "")
        
        if self.enabled_engines is None:
            # 只使用Google搜索，禁用其他搜索引擎
            self.enabled_engines = ["google"]

@dataclass
class ConcurrencyConfig:
    """并发配置"""
    initial_max_requests: int = 100
    target_max_requests: int = 200
    aggressive_max_requests: int = 500
    request_timeout: int = 30
    retry_delay: float = 1.0
    max_retries: int = 3

@dataclass
class QualityThresholds:
    """质量阈值配置"""
    minimum_content_length: int = 60
    similarity_threshold: float = 0.6
    language_quality_threshold: float = 0.7
    source_reliability_threshold: float = 0.5
    minimum_pass_rate: float = 0.3
    target_pass_rate: float = 0.8
    alert_threshold: float = 0.2

@dataclass
class PerformanceLimits:
    """性能限制配置"""
    min_samples_per_minute: int = 100
    max_openai_rpm: int = 500
    max_openai_tpm: int = 40000
    max_together_rpm: int = 3000
    max_together_tpm: int = 150000
    batch_size: int = 300
    max_storage_batch_size: int = 800

@dataclass
class MonitoringConfig:
    """监控配置"""
    slack_webhook_url: str = ""
    enable_slack_alerts: bool = True
    enable_prometheus: bool = False
    log_level: str = "INFO"
    metrics_retention_days: int = 30

@dataclass
class InternalSpec:
    """内部任务规范"""
    domain: str
    task_type: str
    language: str
    quality_rules: Dict[str, Any]
    search_strategy: Dict[str, Any]
    extraction_template: str
    validation_rules: List[str]
    expected_output_format: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "domain": self.domain,
            "task_type": self.task_type,
            "language": self.language,
            "quality_rules": self.quality_rules,
            "search_strategy": self.search_strategy,
            "extraction_template": self.extraction_template,
            "validation_rules": self.validation_rules,
            "expected_output_format": self.expected_output_format
        }

class DataBuilderConfig:
    """DataBuilder V3 配置管理器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "config.json"
        )
        
        # AI提供商配置
        self.ai_provider = "together"  # 默认使用TogetherAI
        self.openai = OpenAIConfig()
        self.together = TogetherAIConfig()
        
        # 其他配置
        self.search_engines = SearchEngineConfig()
        self.concurrency = ConcurrencyConfig()
        self.quality = QualityThresholds()
        self.performance = PerformanceLimits()
        self.monitoring = MonitoringConfig()
        
        # 加载配置文件
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # AI提供商配置
                if 'ai_provider' in config_data:
                    self.ai_provider = config_data['ai_provider']
                if 'openai' in config_data:
                    self._update_dataclass(self.openai, config_data['openai'])
                if 'together' in config_data:
                    self._update_dataclass(self.together, config_data['together'])
                
                # 其他配置
                if 'search_engines' in config_data:
                    self._update_dataclass(self.search_engines, config_data['search_engines'])
                if 'concurrency' in config_data:
                    self._update_dataclass(self.concurrency, config_data['concurrency'])
                if 'quality' in config_data:
                    self._update_dataclass(self.quality, config_data['quality'])
                if 'performance' in config_data:
                    self._update_dataclass(self.performance, config_data['performance'])
                if 'monitoring' in config_data:
                    self._update_dataclass(self.monitoring, config_data['monitoring'])
                    
            except Exception as e:
                print(f"Warning: Failed to load config file {self.config_path}: {e}")
    
    def _update_dataclass(self, dataclass_obj, config_dict):
        """更新dataclass对象"""
        for key, value in config_dict.items():
            if hasattr(dataclass_obj, key):
                setattr(dataclass_obj, key, value)
    
    def save_config(self):
        """保存配置到文件"""
        config_data = {
            'concurrency': self.concurrency.__dict__,
            'quality': self.quality.__dict__,
            'performance': self.performance.__dict__,
            'monitoring': self.monitoring.__dict__
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def get_current_concurrency_level(self) -> int:
        """获取当前并发级别"""
        # 这里可以根据系统负载动态调整
        return self.concurrency.initial_max_requests
    
    def adjust_concurrency(self, success_rate: float, current_level: int) -> int:
        """根据成功率动态调整并发数"""
        if success_rate > 0.9 and current_level < self.concurrency.target_max_requests:
            return min(current_level + 20, self.concurrency.target_max_requests)
        elif success_rate < 0.7 and current_level > 50:
            return max(current_level - 20, 50)
        return current_level
    
    def get_ai_config(self):
        """获取当前AI提供商配置"""
        if self.ai_provider == "together":
            return self.together
        else:
            return self.openai
    
    def get_model_for_task(self, task_complexity: str = "balanced"):
        """根据任务复杂度获取合适的模型"""
        if self.ai_provider == "together":
            return self.together.models.get(task_complexity, self.together.models["balanced"])
        else:
            return self.openai.model

# 全局配置实例
config = DataBuilderConfig()

# 常用的域名白名单
TRUSTED_DOMAINS = [
    '.gov.', '.edu.', '.org.',
    'wikipedia.org', 'baidu.com', 'zhihu.com',
    'stackoverflow.com', 'github.com', 'medium.com',
    'arxiv.org', 'researchgate.net', 'scholar.google.com'
]

# 任务类型映射
TASK_TYPE_MAPPING = {
    'qa': 'question_answering',
    'classification': 'text_classification', 
    'generation': 'text_generation',
    'summarization': 'text_summarization',
    'translation': 'text_translation',
    'sentiment': 'sentiment_analysis'
}

# 语言代码映射
LANGUAGE_MAPPING = {
    'zh': 'chinese',
    'en': 'english',
    'zh-cn': 'chinese',
    'zh-tw': 'chinese_traditional',
    'ja': 'japanese',
    'ko': 'korean'
}