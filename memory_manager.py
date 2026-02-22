"""
记忆管理系统 - 核心管理器
整合所有模块，提供统一的工作流
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import sys

from .config_loader import MemorySystemConfig
from .conversation_saver import ConversationSaver
from .memory_extractor import MemoryExtractor
from .vector_store import VectorStore
from .identity_updater import IdentityUpdater, UpdateResult
from .models import Conversation, Memory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器 - 整个系统的入口点

    工作流程：
    1. 对话保存：每次对话后自动保存
    2. 记忆提取：定期（或触发式）从对话提取记忆
    3. 向量存储：将记忆向量化存储
    4. 身份更新：基于记忆更新身份和灵魂特征
    5. RAG 检索：支持语义搜索
    """

    def __init__(
        self,
        config_path: str = "./config.yaml",
        llm_client=None
    ):
        """
        初始化记忆管理器

        Args:
            config_path: 配置文件路径
            llm_client: 可选的 LLM 客户端（用于兼容现有代码）
        """
        logger.info("初始化记忆管理系统...")

        # 加载配置
        self.config = MemorySystemConfig.from_yaml(config_path)
        logger.info(f"配置加载完成，LLM提供商: {self.config.llm.provider}")

        # 初始化组件
        self.conversation_saver = ConversationSaver(self.config)
        self.vector_store = VectorStore(self.config)
        self.memory_extractor = MemoryExtractor(self.config, llm_client)
        self.identity_updater = IdentityUpdater(
            self.config,
            self.vector_store,
            self.memory_extractor,
            llm_client
        )

        logger.info("记忆管理系统初始化完成 ✅")

    def record_conversation(
        self,
        user_input: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        记录对话（这是工作流的第一步）

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            metadata: 额外元数据

        Returns:
            对话对象
        """
        logger.info("保存对话...")
        conversation = self.conversation_saver.save_conversation(
            user_input=user_input,
            assistant_response=assistant_response,
            metadata=metadata
        )
        logger.info(f"对话保存完成: {conversation.id}")
        return conversation

    def process_conversation_async(
        self,
        user_input: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        异步处理对话（后台运行，不阻塞主流程）

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            metadata: 额外元数据
        """
        import threading

        def _process():
            try:
                # 1. 保存对话
                conversation = self.record_conversation(user_input, assistant_response, metadata)

                # 2. 提取记忆
                if self.config.memory_extraction.auto_extract:
                    logger.info("提取记忆...")
                    memories = self.memory_extractor.extract_memories_from_conversation(conversation)

                    if memories:
                        # 3. 存储到向量库
                        self.vector_store.add_memories(memories)
                        logger.info(f"提取并存储了 {len(memories)} 条记忆")

                # 4. 检查是否需要更新身份
                if self.identity_updater.should_update():
                    logger.info("更新身份和灵魂特征...")
                    result = self.identity_updater.update_identity_and_soul(dry_run=False)
                    logger.info(f"身份更新结果: {result}")

            except Exception as e:
                logger.error(f"异步处理对话失败: {e}", exc_info=True)

        # 在后台线程运行
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()

    def extract_and_store_memories(
        self,
        days: int = 1,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """
        手动提取指定天数的对话记忆

        Args:
            days: 提取最近几天的对话
            limit: 限制处理的对话数量

        Returns:
            提取的记忆列表
        """
        logger.info(f"提取最近 {days} 天的对话记忆...")

        # 加载对话
        conversations = self.conversation_saver.load_conversations()
        if limit:
            conversations = conversations[-limit:]

        recent_conversations = []
        cutoff_date = datetime.now().date().replace(day=datetime.now().day - days)

        for conv in conversations:
            if conv.timestamp.date() >= cutoff_date:
                recent_conversations.append(conv)

        logger.info(f"找到 {len(recent_conversations)} 条对话")

        # 提取记忆
        memories = self.memory_extractor.extract_from_multiple_conversations(recent_conversations)
        logger.info(f"提取了 {len(memories)} 条记忆")

        if memories:
            # 存储到向量库
            self.vector_store.add_memories(memories)
            logger.info("记忆已存储到向量库")

        return memories

    def update_identity(self, dry_run: bool = False) -> UpdateResult:
        """
        手动更新身份和灵魂特征

        Args:
            dry_run: 演练模式，不实际保存

        Returns:
            更新结果
        """
        logger.info("手动更新身份和灵魂特征...")
        result = self.identity_updater.update_identity_and_soul(dry_run=dry_run)
        return result

    def search_memories(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆（RAG 检索）

        Args:
            query: 查询文本
            category: 可选的类别过滤（字符串，如 "写作偏好"）
            top_k: 返回的最大结果数
            min_confidence: 最小置信度

        Returns:
            记忆列表
        """
        # 转换类别
        from .models import MemoryCategory
        cat_enum = None
        if category:
            try:
                cat_enum = MemoryCategory(category)
            except ValueError:
                logger.warning(f"未知的记忆类别: {category}")

        return self.vector_store.search(
            query=query,
            category=cat_enum,
            top_k=top_k,
            min_confidence=min_confidence
        )

    def get_identity_context(self) -> str:
        """获取身份上下文（用于注入到 Claude 提示）"""
        return self.identity_updater.get_identity_context()

    def get_soul_context(self) -> str:
        """获取灵魂上下文"""
        return self.identity_updater.get_soul_context()

    def get_all_memories(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取所有记忆

        Args:
            category: 可选的类别过滤

        Returns:
            记忆列表
        """
        if category:
            from .models import MemoryCategory
            try:
                cat_enum = MemoryCategory(category)
                return self.vector_store.search_by_category(cat_enum, top_k=100)
            except ValueError:
                return []
        else:
            return self.vector_store.get_all_memories()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_memories": self.vector_store.count(),
            "conversations_count": len(self.conversation_saver.load_conversations()),
            "identity_last_updated": self.identity_updater.identity.last_updated,
            "soul_last_updated": self.identity_updater.soul.last_updated,
            "vector_store_path": str(Path(self.config.vector_store.persist_directory))
        }
        return stats

    def cleanup_old_files(self, days: int = 30) -> int:
        """
        清理旧的文件

        Args:
            days: 保留天数

        Returns:
            清理的文件数
        """
        cleaned = self.conversation_saver.cleanup_old_conversations(days)
        return cleaned
