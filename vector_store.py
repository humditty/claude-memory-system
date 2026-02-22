"""
向量化存储和检索模块
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

from .models import Memory, Conversation
from .config_loader import MemorySystemConfig, VectorStoreConfig


class VectorStore:
    """向量存储管理器 - 使用 ChromaDB"""

    def __init__(self, config: MemorySystemConfig):
        """
        初始化向量存储

        Args:
            config: 记忆系统配置
        """
        self.config = config
        self.vs_config = config.vector_store

        # 确保存储目录存在
        self.persist_dir = Path(self.vs_config.persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.vs_config.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # 初始化嵌入模型
        print(f"加载嵌入模型: {config.embeddings.model}")
        self.embedding_model = SentenceTransformer(config.embeddings.model)

    def add_memory(self, memory: Memory) -> str:
        """
        添加记忆到向量存储

        Args:
            memory: 记忆对象

        Returns:
            记忆ID
        """
        # 生成嵌入向量
        text = f"{memory.category.value}: {memory.content}"
        embedding = self.embedding_model.encode(text).tolist()

        # 存储到 ChromaDB
        self.collection.add(
            ids=[memory.id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "category": memory.category.value,
                "confidence": memory.confidence,
                "source_conversation_id": memory.source_conversation_id,
                "created_at": memory.created_at.isoformat(),
                "tags": ", ".join(memory.tags) if memory.tags else "",
                "content": memory.content
            }]
        )

        return memory.id

    def add_memories(self, memories: List[Memory]) -> List[str]:
        """
        批量添加记忆

        Args:
            memories: 记忆列表

        Returns:
            记忆ID列表
        """
        if not memories:
            return []

        # 生成嵌入向量
        texts = [f"{m.category.value}: {m.content}" for m in memories]
        embeddings = self.embedding_model.encode(texts).tolist()

        # 批量存储
        ids = [m.id for m in memories]
        metadatas = [{
            "category": m.category.value,
            "confidence": m.confidence,
            "source_conversation_id": m.source_conversation_id,
            "created_at": m.created_at.isoformat(),
            "tags": ", ".join(m.tags) if m.tags else "",
            "content": m.content
        } for m in memories]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        return ids

    def search(
        self,
        query: str,
        category: Optional[MemoryCategory] = None,
        top_k: int = 5,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆

        Args:
            query: 查询文本
            category: 可选的类别过滤
            top_k: 返回的最大结果数
            min_confidence: 最小置信度

        Returns:
            记忆列表（包含距离和元数据）
        """
        # 生成查询嵌入
        query_embedding = self.embedding_model.encode(query).tolist()

        # 构建过滤条件
        where = {}
        if category:
            where["category"] = category.value

        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # 获取更多结果以便过滤
            where=where if where else None,
            include=["documents", "metadatas", "distances"]
        )

        # 处理结果
        formatted_results = []
        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            # ChromaDB 使用余弦距离（0-2，越小越相似），转换为相似度
            similarity = 1 - dist / 2

            # 过滤置信度
            confidence = meta.get('confidence', 0.8)
            if confidence < min_confidence:
                continue

            formatted_results.append({
                "id": results['ids'][0][i],
                "content": meta.get('content', doc),
                "category": meta.get('category'),
                "confidence": confidence,
                "similarity": similarity,
                "source_conversation_id": meta.get('source_conversation_id'),
                "created_at": meta.get('created_at'),
                "tags": meta.get('tags', '').split(', ') if meta.get('tags') else [],
                "distance": dist
            })

            if len(formatted_results) >= top_k:
                break

        return formatted_results

    def search_by_category(
        self,
        category: MemoryCategory,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        按类别搜索记忆

        Args:
            category: 记忆类别
            top_k: 返回的最大结果数

        Returns:
            记忆列表
        """
        results = self.collection.get(
            where={"category": category.value},
            limit=top_k,
            include=["documents", "metadatas"]
        )

        memories = []
        for i, (doc_id, meta) in enumerate(zip(results['ids'], results['metadatas'])):
            memories.append({
                "id": doc_id,
                "content": meta.get('content', results['documents'][i]),
                "category": meta.get('category'),
                "confidence": meta.get('confidence', 0.8),
                "source_conversation_id": meta.get('source_conversation_id'),
                "created_at": meta.get('created_at'),
                "tags": meta.get('tags', '').split(', ') if meta.get('tags') else []
            })

        return memories

    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆

        Args:
            memory_id: 记忆ID

        Returns:
            是否成功
        """
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"删除记忆 {memory_id} 失败: {e}")
            return False

    def clear_all(self) -> None:
        """清空所有记忆"""
        self.client.delete_collection(self.vs_config.collection_name)
        self.collection = self.client.create_collection(
            name=self.vs_config.collection_name
        )

    def count(self) -> int:
        """获取记忆总数"""
        return self.collection.count()

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """获取所有记忆（慎用）"""
        results = self.collection.get(include=["documents", "metadatas"])

        memories = []
        for i, (doc_id, meta) in enumerate(zip(results['ids'], results['metadatas'])):
            memories.append({
                "id": doc_id,
                "content": meta.get('content', results['documents'][i]),
                "category": meta.get('category'),
                "confidence": meta.get('confidence', 0.8),
                "source_conversation_id": meta.get('source_conversation_id'),
                "created_at": meta.get('created_at'),
                "tags": meta.get('tags', '').split(', ') if meta.get('tags') else []
            })

        return memories
