"""
配置加载和管理模块
"""
import yaml
from pathlib import Path
from typing import Dict, Any
import os
from dataclasses import dataclass, field, asdict


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    temperature: float = 0.3


@dataclass
class EmbeddingsConfig:
    """嵌入模型配置"""
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384


@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    type: str = "chromadb"
    persist_directory: str = "./vector_store"
    collection_name: str = "conversation_memories"


@dataclass
class MemoryExtractionConfig:
    """记忆提取配置"""
    auto_extract: bool = True
    min_conversation_length: int = 100
    categories: list = field(default_factory=lambda: [
        "写作偏好", "语气风格", "关注兴趣", "股票追踪",
        "邮件分类规则", "个人背景", "工作习惯", "技术偏好"
    ])
    max_memories_per_day: int = 20


@dataclass
class IdentityUpdateConfig:
    """身份更新配置"""
    frequency: str = "daily"  # daily, weekly, manual
    deduplicate: bool = True
    max_identity_items: int = 50
    max_soul_items: int = 30


@dataclass
class PathsConfig:
    """路径配置"""
    conversations: str = "./conversations"
    memories: str = "./memories"
    logs: str = "./logs"


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "./logs/memory_system.log"
    max_size_mb: int = 10
    backup_count: int = 5


@dataclass
class MemorySystemConfig:
    """完整的记忆系统配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = field(default_factory=EmbeddingsConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    memory_extraction: MemoryExtractionConfig = field(default_factory=MemoryExtractionConfig)
    identity_update: IdentityUpdateConfig = field(default_factory=IdentityUpdateConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, config_path: str = "./config.yaml") -> "MemorySystemConfig":
        """从 YAML 文件加载配置"""
        config_file = Path(config_path)

        if not config_file.exists():
            # 创建默认配置
            return cls()

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        config = cls()

        # 递归更新配置
        def update_dataclass(obj, data_dict):
            for key, value in data_dict.items():
                if hasattr(obj, key):
                    attr = getattr(obj, key)
                    if isinstance(attr, (LLMConfig, EmbeddingsConfig, VectorStoreConfig,
                                       MemoryExtractionConfig, IdentityUpdateConfig,
                                       PathsConfig, LoggingConfig)):
                        update_dataclass(attr, value)
                    else:
                        setattr(obj, key, value)

        update_dataclass(config, data)

        # 环境变量替换
        config.llm.api_key = os.path.expandvars(config.llm.api_key)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "llm": asdict(self.llm),
            "embeddings": asdict(self.embeddings),
            "vector_store": asdict(self.vector_store),
            "memory_extraction": asdict(self.memory_extraction),
            "identity_update": asdict(self.identity_update),
            "paths": asdict(self.paths),
            "logging": asdict(self.logging)
        }
