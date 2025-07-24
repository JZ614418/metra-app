"""
SpecMapper - 任务描述到内部规范映射器
将用户的任务描述转换为标准化的内部规范，支持配置化处理
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from openai import AsyncOpenAI
from app.core.config import settings
from app.services.data_builder_v3.config import InternalSpec, TASK_TYPE_MAPPING, LANGUAGE_MAPPING, TRUSTED_DOMAINS, config
from app.services.data_builder_v3.together_client import TogetherClient

logger = logging.getLogger(__name__)

class SpecMapper:
    """任务规范映射器"""
    
    def __init__(self):
        # 根据配置选择AI客户端
        if config.ai_provider == "together":
            self.ai_client = TogetherClient(
                api_key=config.together.api_key,
                base_url=config.together.base_url
            )
            self.use_together = True
        else:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.use_together = False
        
    async def map_task_to_spec(self, task_definition: Dict[str, Any]) -> InternalSpec:
        """
        将用户任务描述映射为内部规范
        
        Args:
            task_definition: 用户任务定义
            {
                "task": "中医药知识问答",
                "type": "qa", 
                "language": "chinese",
                "description": "收集中医药相关问答数据",
                "domain": "tcm",
                "labels": ["中医", "药材", "病症", "方剂"],
                "data_volume": 2000
            }
            
        Returns:
            InternalSpec: 标准化内部规范
        """
        try:
            # 预处理任务信息
            processed_task = self._preprocess_task(task_definition)
            
            # 使用GPT生成内部规范
            spec_dict = await self._generate_spec_with_gpt(processed_task)
            
            # 验证和完善规范
            validated_spec = self._validate_and_enhance_spec(spec_dict, processed_task)
            
            # 创建InternalSpec对象
            internal_spec = InternalSpec(
                domain=validated_spec["domain"],
                task_type=validated_spec["task_type"],
                language=validated_spec["language"],
                quality_rules=validated_spec["quality_rules"],
                search_strategy=validated_spec["search_strategy"],
                extraction_template=validated_spec["extraction_template"],
                validation_rules=validated_spec["validation_rules"],
                expected_output_format=validated_spec["expected_output_format"]
            )
            
            logger.info(f"✅ 任务映射成功: {task_definition.get('task', 'Unknown')} -> {internal_spec.domain}/{internal_spec.task_type}")
            return internal_spec
            
        except Exception as e:
            logger.error(f"❌ 任务映射失败: {str(e)}")
            # 返回默认规范
            return self._create_default_spec(task_definition)
    
    def _preprocess_task(self, task_definition: Dict[str, Any]) -> Dict[str, Any]:
        """预处理任务定义"""
        processed = task_definition.copy()
        
        # 标准化任务类型
        task_type = processed.get("type", "qa").lower()
        processed["task_type"] = TASK_TYPE_MAPPING.get(task_type, task_type)
        
        # 标准化语言
        language = processed.get("language", "chinese").lower()
        processed["language"] = LANGUAGE_MAPPING.get(language, language)
        
        # 提取关键信息
        processed["keywords"] = processed.get("labels", [])
        processed["target_volume"] = processed.get("data_volume", 1000)
        
        return processed
    
    async def _generate_spec_with_gpt(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI生成内部规范"""
        
        prompt = f"""
你是一个数据收集专家，需要将用户的任务描述转换为标准化的内部规范。

用户任务信息：
- 任务名称: {task_info.get('task', 'Unknown')}
- 任务类型: {task_info.get('task_type', 'qa')}
- 语言: {task_info.get('language', 'chinese')}
- 领域: {task_info.get('domain', 'general')}
- 描述: {task_info.get('description', '')}
- 关键词: {task_info.get('keywords', [])}
- 目标数据量: {task_info.get('target_volume', 1000)}

请生成一个JSON格式的内部规范，包含以下字段：

1. domain: 领域标识 (如: tcm, finance, legal, education, general)
2. task_type: 任务类型 (question_answering, text_classification, text_generation, text_summarization)
3. language: 语言 (chinese, english, japanese, korean)
4. quality_rules: 质量规则
   - min_content_length: 最小内容长度
   - min_answer_length: 最小答案长度(QA任务)
   - required_keywords: 必需关键词
   - forbidden_keywords: 禁止关键词
5. search_strategy: 搜索策略
   - base_keywords: 基础关键词
   - site_whitelist: 站点白名单
   - negative_keywords: 负面关键词
   - search_depth: 搜索深度
6. extraction_template: 提取模板(用于GPT提取)
7. validation_rules: 验证规则列表
8. expected_output_format: 期望输出格式

请确保规范实用且可执行。只返回JSON，无需其他说明。

示例输出格式：
{{
  "domain": "tcm",
  "task_type": "question_answering",
  "language": "chinese",
  "quality_rules": {{
    "min_content_length": 60,
    "min_answer_length": 100,
    "required_keywords": ["中医", "药材"],
    "forbidden_keywords": ["广告", "淘宝", "购买"]
  }},
  "search_strategy": {{
    "base_keywords": ["中医药", "中药", "方剂"],
    "site_whitelist": ["baidu.com", "zhihu.com"],
    "negative_keywords": ["广告", "商品", "价格"],
    "search_depth": 3
  }},
  "extraction_template": "从以下文本中提取中医药相关的问答对...",
  "validation_rules": ["检查问题是否以？结尾", "检查答案是否包含中医术语"],
  "expected_output_format": "{{\\\"input\\\": \\\"问题\\\", \\\"output\\\": \\\"答案\\\"}}"
}}
"""
        
        try:
            if self.use_together:
                # 使用TogetherAI (高质量模型，因为这是关键任务)
                model = config.get_model_for_task("high_quality")
                ai_response = await self.ai_client.generate_chat(
                    prompt=prompt,
                    model=model,
                    max_tokens=1500,
                    temperature=0.3
                )
            else:
                # 使用OpenAI
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1500
                )
                ai_response = response.choices[0].message.content
            
            # 解析JSON
            if '```json' in ai_response:
                json_start = ai_response.find('```json') + 7
                json_end = ai_response.rfind('```')
                ai_response = ai_response[json_start:json_end]
            elif '{' in ai_response:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                ai_response = ai_response[json_start:json_end]
            
            spec_dict = json.loads(ai_response)
            provider = "TogetherAI" if self.use_together else "OpenAI"
            logger.info(f"✅ {provider}生成规范成功: {spec_dict.get('domain', 'unknown')}")
            return spec_dict
            
        except Exception as e:
            logger.error(f"❌ AI生成规范失败: {str(e)}")
            raise
    
    def _validate_and_enhance_spec(self, spec_dict: Dict[str, Any], task_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证和完善规范"""
        
        # 确保必需字段存在
        spec_dict.setdefault("domain", task_info.get("domain", "general"))
        spec_dict.setdefault("task_type", task_info.get("task_type", "question_answering"))
        spec_dict.setdefault("language", task_info.get("language", "chinese"))
        
        # 验证和完善质量规则
        quality_rules = spec_dict.get("quality_rules", {})
        quality_rules.setdefault("min_content_length", 60)
        quality_rules.setdefault("min_answer_length", 100)
        quality_rules.setdefault("required_keywords", task_info.get("keywords", []))
        quality_rules.setdefault("forbidden_keywords", ["广告", "淘宝", "购买", "价格", "商品"])
        spec_dict["quality_rules"] = quality_rules
        
        # 验证和完善搜索策略
        search_strategy = spec_dict.get("search_strategy", {})
        search_strategy.setdefault("base_keywords", task_info.get("keywords", []))
        search_strategy.setdefault("site_whitelist", TRUSTED_DOMAINS)
        search_strategy.setdefault("negative_keywords", ["-广告", "-淘宝", "-购买", "-价格"])
        search_strategy.setdefault("search_depth", 3)
        spec_dict["search_strategy"] = search_strategy
        
        # 验证提取模板
        if not spec_dict.get("extraction_template"):
            spec_dict["extraction_template"] = self._generate_default_extraction_template(
                spec_dict["task_type"], 
                spec_dict["domain"]
            )
        
        # 验证规则
        spec_dict.setdefault("validation_rules", [
            "检查内容长度是否满足要求",
            "检查是否包含必需关键词",
            "检查是否包含禁止关键词"
        ])
        
        # 输出格式
        spec_dict.setdefault("expected_output_format", 
            '{"input": "问题", "output": "答案"}' if spec_dict["task_type"] == "question_answering" 
            else '{"text": "文本", "label": "标签"}'
        )
        
        return spec_dict
    
    def _generate_default_extraction_template(self, task_type: str, domain: str) -> str:
        """生成默认提取模板"""
        
        templates = {
            "question_answering": f"""
你是一名{domain}专家。请从以下文本中提取1-3组高质量的【问题】【答案】对：

文章内容：
<<<{{page_text}}>>>

要求：
1. 问题必须是完整的疑问句，以"？"结尾
2. 答案必须详细准确，≥100字
3. 问答内容必须与{domain}相关
4. 返回JSON数组格式：[{{"input": "问题", "output": "答案"}}]

如果文本中没有合适的问答内容，返回空数组[]。
            """,
            
            "text_classification": f"""
你是一名{domain}专家。请从以下文本中提取可用于分类训练的文本片段：

文章内容：
<<<{{page_text}}>>>

要求：
1. 提取的文本片段≥60字
2. 为每个片段分配准确的类别标签
3. 内容必须与{domain}相关
4. 返回JSON数组格式：[{{"text": "文本内容", "label": "类别标签"}}]

如果文本中没有合适的分类内容，返回空数组[]。
            """,
            
            "text_generation": f"""
你是一名{domain}专家。请从以下文本中提取可用于生成训练的示例：

文章内容：
<<<{{page_text}}>>>

要求：
1. 提取有价值的文本段落作为输入
2. 生成对应的输出或续写内容
3. 内容必须与{domain}相关
4. 返回JSON数组格式：[{{"input": "输入", "output": "输出"}}]

如果文本中没有合适的生成内容，返回空数组[]。
            """
        }
        
        return templates.get(task_type, templates["question_answering"])
    
    def _create_default_spec(self, task_definition: Dict[str, Any]) -> InternalSpec:
        """创建默认规范"""
        logger.warning("使用默认规范替代")
        
        return InternalSpec(
            domain=task_definition.get("domain", "general"),
            task_type=TASK_TYPE_MAPPING.get(task_definition.get("type", "qa"), "question_answering"),
            language=LANGUAGE_MAPPING.get(task_definition.get("language", "chinese"), "chinese"),
            quality_rules={
                "min_content_length": 60,
                "min_answer_length": 100,
                "required_keywords": task_definition.get("labels", []),
                "forbidden_keywords": ["广告", "淘宝", "购买"]
            },
            search_strategy={
                "base_keywords": task_definition.get("labels", []),
                "site_whitelist": TRUSTED_DOMAINS,
                "negative_keywords": ["-广告", "-淘宝", "-购买"],
                "search_depth": 3
            },
            extraction_template=self._generate_default_extraction_template(
                "question_answering", 
                task_definition.get("domain", "general")
            ),
            validation_rules=["检查基础格式", "检查内容长度"],
            expected_output_format='{"input": "问题", "output": "答案"}'
        )

# 创建全局实例
spec_mapper = SpecMapper()