"""
DataBuilder V3 - 质量驱动的数据收集系统
主要特性：
- 配置化任务映射，无需硬编码
- 智能质量验证，确保数据有效性
- 高并发处理，保持性能优势
- 实时监控告警，主动发现问题
"""

from .pipeline import DataBuilderPipeline
from .spec_mapper import SpecMapper
from .query_generator import QueryGenerator
from .page_scraper import PageScraper
from .sample_extractor import SampleExtractor
from .quality_validator import QualityValidator
from .storage_writer import StorageWriter
from .monitoring import EnhancedMonitoring

__version__ = "3.0.0"
__author__ = "Metra AI Team"

__all__ = [
    "DataBuilderPipeline",
    "SpecMapper",
    "QueryGenerator", 
    "PageScraper",
    "SampleExtractor",
    "QualityValidator",
    "StorageWriter",
    "EnhancedMonitoring"
]