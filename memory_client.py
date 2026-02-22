#!/usr/bin/env python3
"""
Memory Client - 集成到现有工作流的便捷接口

这是一个简单的 wrapper，可以轻松集成到任何使用 Claude 的工作流中。

使用示例：
```python
from memory_client import MemoryClient

# 初始化（单例模式）
client = MemoryClient()

# 在对话结束时调用
client.record(
    user_input="我想学习 Python",
    assistant_response="好的，我推荐从基础语法开始..."
)

# 在生成回复前注入记忆上下文
identity_ctx = client.get_identity_context()
soul_ctx = client.get_soul_context()

# 搜索相关记忆
memories = client.search("Python教程", top_k=3)
```
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# 确保可以导入本地模块
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from memory_manager import MemoryManager
from config_loader import MemorySystemConfig


class MemoryClient:
    """
    记忆系统客户端 - 单例模式

    这个类封装了 MemoryManager，提供更简单的接口用于日常工作流集成。
    """

    _instance: Optional['MemoryClient'] = None
    _manager: Optional[MemoryManager] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        config_path: str = "./config.yaml",
        auto_process: bool = True
    ):
        """
        初始化记忆客户端

        注意：由于是单例模式，多次初始化只会生效一次。

        Args:
            config_path: 配置文件路径
            auto_process: 是否自动处理对话（提取记忆、更新身份）
        """
        if self._initialized:
            return

        self.config_path = config_path
        self.auto_process = auto_process
        self._manager = None
        self._initialized = True

        # 延迟初始化，只在第一次使用时创建管理器
        self._ensure_manager()

    def _ensure_manager(self) -> None:
        """确保管理器已初始化"""
        if self._manager is None:
            try:
                self._manager = MemoryManager(config_path=self.config_path)
            except Exception as e:
                print(f"⚠️ 记忆系统初始化失败: {e}")
                self._manager = None

    def record(
        self,
        user_input: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None,
        block: bool = False
    ) -> None:
        """
        记录对话到记忆系统

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            metadata: 额外元数据
            block: 是否阻塞执行（如果为 False，则在后台线程执行）
        """
        if not self._manager:
            return

        if block:
            # 阻塞模式：直接记录并处理
            conversation = self._manager.record_conversation(
                user_input, assistant_response, metadata
            )

            if self.auto_process:
                self._manager.memory_extractor.extract_memories_from_conversation(conversation)
        else:
            # 异步模式：后台处理
            self._manager.process_conversation_async(
                user_input, assistant_response, metadata
            )

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆

        Args:
            query: 查询文本
            category: 可选类别
            top_k: 最大结果数

        Returns:
            记忆列表
        """
        if not self._manager:
            return []

        return self._manager.search_memories(query, category, top_k)

    def get_identity_context(self) -> str:
        """
        获取身份上下文

        可以直接插入到 Claude 的系统提示中
        """
        if not self._manager:
            return "# 用户身份信息\n\n（记忆系统未初始化）"

        return self._manager.get_identity_context()

    def get_soul_context(self) -> str:
        """
        获取灵魂上下文

        可以直接插入到 Claude 的系统提示中
        """
        if not self._manager:
            return "# 用户灵魂特征\n\n（记忆系统未初始化）"

        return self._manager.get_soul_context()

    def get_full_context(self) -> str:
        """
        获取完整的记忆上下文（身份+灵魂）

        返回可以直接插入到系统提示的内容
        """
        identity = self.get_identity_context()
        soul = self.get_soul_context()

        return f"{identity}\n\n{soul}"

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._manager:
            return {}

        return self._manager.get_stats()

    def force_update(self, dry_run: bool = False) -> bool:
        """
        强制触发身份更新

        Args:
            dry_run: 演练模式

        Returns:
            是否成功
        """
        if not self._manager:
            return False

        try:
            result = self._manager.update_identity(dry_run=dry_run)
            return True
        except Exception as e:
            print(f"身份更新失败: {e}")
            return False

    def is_enabled(self) -> bool:
        """检查记忆系统是否已启用"""
        return self._manager is not None


# 全局客户端实例（方便快速使用）
default_client = MemoryClient()


def get_client() -> MemoryClient:
    """获取默认客户端实例"""
    return default_client


def record(
    user_input: str,
    assistant_response: str,
    metadata: Optional[Dict[str, Any]] = None,
    block: bool = False
) -> None:
    """
    便捷函数：记录对话（使用默认客户端）

    示例：
    ```python
    from memory_client import record

    # 在对话处理完后调用
    record(user_input=user_msg, assistant_response=assistant_msg)
    ```
    """
    default_client.record(user_input, assistant_response, metadata, block)


def search(query: str, category: Optional[str] = None, top_k: int = 5) -> List[Dict]:
    """便捷函数：搜索记忆"""
    return default_client.search(query, category, top_k)


def get_context() -> str:
    """便捷函数：获取完整上下文"""
    return default_client.get_full_context()
