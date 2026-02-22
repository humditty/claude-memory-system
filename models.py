"""
记忆系统的核心数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
import uuid


class MemoryCategory(Enum):
    """记忆类别枚举"""
    WRITING_PREFERENCE = "写作偏好"
    TONE_STYLE = "语气风格"
    INTERESTS = "关注兴趣"
    STOCK_TRACKING = "股票追踪"
    EMAIL_RULES = "邮件分类规则"
    BACKGROUND = "个人背景"
    WORK_HABITS = "工作习惯"
    TECH_PREFERENCE = "技术偏好"


@dataclass
class Conversation:
    """对话记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""
    user_input: str = ""
    assistant_response: str = ""
    metadata: Dict[str, any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """转换为 markdown 格式"""
        md = f"""# 对话记录

时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
对话ID: {self.id}

## 用户输入
{self.user_input}

## Claude 回复
{self.assistant_response}

## 元数据
```json
{self.metadata}
```

---
"""
        return md


@dataclass
class Memory:
    """提炼后的记忆"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: MemoryCategory = MemoryCategory.INTERESTS
    content: str = ""
    source_conversation_id: str = ""
    confidence: float = 0.8  # 置信度 0-1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """转换为 markdown 格式"""
        md = f"""## {self.category.value}

**ID**: {self.id}
**置信度**: {self.confidence:.2%}
**来源**: {self.source_conversation_id}
**时间**: {self.created_at.strftime('%Y-%m-%d %H:%M')}
**标签**: {', '.join(self.tags) if self.tags else '无'}

{self.content}

---
"""
        return md

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "category": self.category.value,
            "content": self.content,
            "source_conversation_id": self.source_conversation_id,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags
        }


@dataclass
class Identity:
    """动态身份信息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "用户"
    expertise: List[str] = field(default_factory=list)  # 专业领域
    preferred_language: str = "中文"  # 偏好语言
    communication_style: str = ""  # 沟通风格
    key_facts: List[str] = field(default_factory=list)  # 关键事实
    last_updated: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为 markdown 格式"""
        expertise_str = ', '.join(self.expertise) if self.expertise else '待确定'
        facts_str = '\n- '.join(self.key_facts) if self.key_facts else '无'

        md = f"""# 身份信息

## 基本资料
- 名称: {self.name}
- 专业领域: {expertise_str}
- 偏好语言: {self.preferred_language}
- 沟通风格: {self.communication_style or '待确定'}

## 关键事实
- {facts_str}

**最后更新**: {self.last_updated.strftime('%Y-%m-%d %H:%M')}
**ID**: {self.id}

---
"""
        return md


@dataclass
class Soul:
    """性格特征和价值观"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    core_values: List[str] = field(default_factory=list)  # 核心价值观
    personality_traits: List[str] = field(default_factory=list)  # 性格特征
    working_style: str = ""  # 工作方式
    motivations: List[str] = field(default_factory=list)  # 动机
    concerns: List[str] = field(default_factory=list)  # 关注点
    last_updated: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为 markdown 格式"""
        values_str = '\n- '.join(self.core_values) if self.core_values else '待确定'
        traits_str = ', '.join(self.personality_traits) if self.personality_traits else '待确定'
        motivations_str = '\n- '.join(self.motivations) if self.motivations else '待确定'
        concerns_str = '\n- '.join(self.concerns) if self.concerns else '待确定'

        md = f"""# 灵魂特征

## 核心价值观
- {values_str}

## 性格特征
{traits_str}

## 工作方式
{self.working_style or '待确定'}

## 内在动机
- {motivations_str}

## 关注点
- {concerns_str}

**最后更新**: {self.last_updated.strftime('%Y-%m-%d %H:%M')}
**ID**: {self.id}

---
"""
        return md
