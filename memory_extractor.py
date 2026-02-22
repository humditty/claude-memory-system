"""
偏好提炼和记忆提取模块
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .models import Memory, MemoryCategory, Conversation
from .config_loader import MemorySystemConfig, MemoryExtractionConfig


@dataclass
class ExtractedMemory:
    """从 LLM 提取的原始记忆"""
    category: str
    content: str
    confidence: float = 0.8
    tags: List[str] = field(default_factory=list)


class MemoryExtractor:
    """记忆提取器 - 使用 LLM 从对话中提取记忆"""

    def __init__(self, config: MemorySystemConfig, llm_client=None):
        """
        初始化记忆提取器

        Args:
            config: 记忆系统配置
            llm_client: LLM 客户端（如果为 None 则根据配置自动创建）
        """
        self.config = config
        self.extraction_config = config.memory_extraction
        self.llm_client = llm_client or self._create_llm_client()

    def _create_llm_client(self):
        """根据配置创建 LLM 客户端"""
        provider = self.config.llm.provider

        if provider == "openai":
            from openai import OpenAI
            return OpenAI(
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url
            )
        elif provider == "anthropic":
            import anthropic
            return anthropic.Anthropic(api_key=self.config.llm.api_key)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")

    def extract_memories_from_conversation(
        self,
        conversation: Conversation
    ) -> List[Memory]:
        """
        从对话中提取记忆

        Args:
            conversation: 对话对象

        Returns:
            提取的记忆列表
        """
        # 检查对话长度
        total_length = len(conversation.user_input) + len(conversation.assistant_response)
        if total_length < self.extraction_config.min_conversation_length:
            return []

        # 构建 LLM 提示词
        prompt = self._build_extraction_prompt(conversation)

        try:
            # 调用 LLM 提取记忆
            extracted_data = self._call_llm(prompt)

            # 转换为 Memory 对象
            memories = []
            for item in extracted_data:
                try:
                    category = MemoryCategory(item['category'])
                except ValueError:
                    # 如果类别不匹配，使用 OTHER
                    category = MemoryCategory.INTERESTS

                memory = Memory(
                    category=category,
                    content=item['content'].strip(),
                    source_conversation_id=conversation.id,
                    confidence=item.get('confidence', 0.8),
                    tags=item.get('tags', [])
                )
                memories.append(memory)

            return memories

        except Exception as e:
            print(f"提取记忆失败: {e}")
            return []

    def _build_extraction_prompt(self, conversation: Conversation) -> str:
        """构建提取记忆的提示词"""
        categories_str = "\n".join([
            f"- {cat}: {self._get_category_description(cat)}"
            for cat in self.extraction_config.categories
        ])

        prompt = f"""你是一个专业的用户记忆提取助手。请从以下对话中提取关于用户的有价值信息。

# 可提取的记忆类别：
{categories_str}

# 对话内容：
## 用户输入：
{conversation.user_input}

## Claude 回复：
{conversation.assistant_response}

# 提取要求：
1. 只提取**明确**的用户相关信息（从用户输入或回复内容推断）
2. 如果用户提到偏好、习惯、背景等信息，请提取到对应的类别
3. 每条记忆应该简洁（1-2句话），但包含完整信息
4. 为每条记忆分配置信度（0.0-1.0）：
   - 0.9+: 用户明确陈述
   - 0.7-0.9: 从上下文合理推断
   - 0.5-0.7: 可能正确的推断
5. 添加相关标签（如技术栈、领域关键词等）

# 输出格式（JSON 数组）：
[
  {{
    "category": "写作偏好",
    "content": "用户喜欢简洁明了的文档风格，讨厌冗长的描述",
    "confidence": 0.9,
    "tags": ["写作", "文档风格"]
  }},
  {{
    "category": "技术偏好",
    "content": "用户主要使用 Python 进行开发",
    "confidence": 0.95,
    "tags": ["Python", "编程"]
  }}
]

请仅输出 JSON 数组，不要包含其他文字。"""

        return prompt

    def _get_category_description(self, category: str) -> str:
        """获取类别的描述"""
        descriptions = {
            "写作偏好": "用户的写作习惯、文档风格偏好",
            "语气风格": "用户喜欢的沟通语气（正式、随意、友好等）",
            "关注兴趣": "用户感兴趣的主题、领域",
            "股票追踪": "用户关注的股票、投资组合",
            "邮件分类规则": "用户使用的邮件过滤和处理规则",
            "个人背景": "用户的职业、教育背景、地理位置等",
            "工作习惯": "用户的工作时间、工具使用、协作方式",
            "技术偏好": "用户偏好的编程语言、框架、工具"
        }
        return descriptions.get(category, "用户的相关信息")

    def _call_llm(self, prompt: str) -> List[Dict]:
        """调用 LLM API"""
        provider = self.config.llm.provider

        if provider == "openai":
            response = self.llm_client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的记忆提取助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens
            )
            content = response.choices[0].message.content

        elif provider == "anthropic":
            response = self.llm_client.messages.create(
                model=self.config.llm.model,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.content[0].text

        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")

        # 解析 JSON
        content = content.strip()
        # 尝试提取 JSON 部分（如果 LLM 返回了额外的文字）
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        return json.loads(content)

    def extract_from_multiple_conversations(
        self,
        conversations: List[Conversation]
    ) -> List[Memory]:
        """
        从多个对话中批量提取记忆

        Args:
            conversations: 对话列表

        Returns:
            所有提取的记忆
        """
        all_memories = []

        for conversation in conversations:
            memories = self.extract_memories_from_conversation(conversation)
            all_memories.extend(memories)

            # 限制每日提取数量
            if len(all_memories) >= self.extraction_config.max_memories_per_day:
                break

        return all_memories
