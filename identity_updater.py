"""
身份更新机制模块
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
import json

from models import Memory, Identity, Soul, MemoryCategory
from config_loader import MemorySystemConfig, IdentityUpdateConfig
from vector_store import VectorStore
from memory_extractor import MemoryExtractor


@dataclass
class UpdateResult:
    """更新结果"""
    identity_updates: List[str] = field(default_factory=list)
    soul_updates: List[str] = field(default_factory=list)
    memories_added: int = 0
    memories_consolidated: int = 0


class IdentityUpdater:
    """身份更新器 - 基于记忆更新身份和灵魂特征"""

    def __init__(
        self,
        config: MemorySystemConfig,
        vector_store: VectorStore,
        memory_extractor: MemoryExtractor,
        llm_client=None
    ):
        """
        初始化身份更新器

        Args:
            config: 记忆系统配置
            vector_store: 向量存储实例
            memory_extractor: 记忆提取器
            llm_client: LLM 客户端
        """
        self.config = config
        self.vs_config = config.vector_store
        self.update_config = config.identity_update
        self.vector_store = vector_store
        self.memory_extractor = memory_extractor
        self.llm_client = llm_client or memory_extractor.llm_client

        # 确保记忆存储目录存在
        self.memories_dir = Path(config.paths.memories)
        self.memories_dir.mkdir(parents=True, exist_ok=True)

        # 加载现有身份和灵魂数据
        self.identity = self._load_identity()
        self.soul = self._load_soul()

    def _load_identity(self) -> Identity:
        """加载或创建默认身份对象"""
        identity_file = self.memories_dir / "identity.md"

        if identity_file.exists():
            # TODO: 从 markdown 解析 Identity（简化版，实际需要完整的解析器）
            return Identity()
        else:
            return Identity()

    def _load_soul(self) -> Soul:
        """加载或创建默认灵魂对象"""
        soul_file = self.memories_dir / "soul.md"

        if soul_file.exists():
            # TODO: 从 markdown 解析 Soul
            return Soul()
        else:
            return Soul()

    def should_update(self) -> bool:
        """
        检查是否应该更新身份

        Returns:
            是否应该更新
        """
        frequency = self.update_config.frequency

        if frequency == "manual":
            return False

        # 检查上次更新时间
        if self.identity.last_updated:
            now = datetime.now()
            last_update = self.identity.last_updated

            if frequency == "daily":
                # 每日更新：检查是否是新的一天
                return now.date() > last_update.date()
            elif frequency == "weekly":
                # 每周更新：检查是否是新的一周
                week_diff = (now - last_update).days // 7
                return week_diff >= 1

        return True

    def gather_recent_memories(
        self,
        days: int = 7,
        min_confidence: float = 0.7
    ) -> List[Memory]:
        """
        收集最近的记忆

        Args:
            days: 收集最近 N 天的记忆
            min_confidence: 最小置信度

        Returns:
            记忆列表
        """
        all_memories = self.vector_store.get_all_memories()

        # 过滤时间和置信度
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_memories = []

        for mem_data in all_memories:
            # 检查置信度
            if mem_data['confidence'] < min_confidence:
                continue

            # 检查日期
            try:
                created_at = datetime.fromisoformat(mem_data['created_at'])
                if created_at >= cutoff_date:
                    recent_memories.append(Memory(
                        id=mem_data['id'],
                        category=MemoryCategory(mem_data['category']),
                        content=mem_data['content'],
                        source_conversation_id=mem_data['source_conversation_id'],
                        confidence=mem_data['confidence'],
                        tags=mem_data['tags']
                    ))
            except Exception:
                continue

        return recent_memories

    def analyze_memories_with_llm(
        self,
        memories: List[Memory]
    ) -> Dict[str, Any]:
        """
        使用 LLM 分析记忆并生成身份/灵魂更新

        Args:
            memories: 记忆列表

        Returns:
            分析结果字典
        """
        if not memories:
            return {}

        # 按类别分组记忆
        memories_by_category = {}
        for mem in memories:
            cat = mem.category.value
            if cat not in memories_by_category:
                memories_by_category[cat] = []
            memories_by_category[cat].append(mem.content)

        # 构建分析提示词
        prompt = self._build_analysis_prompt(memories_by_category, len(memories))

        try:
            # 调用 LLM
            response = self.llm_client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的用户画像分析助手，擅长从零散信息中提炼用户特征。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content

            # 解析 JSON
            if '```json' in result_text:
                json_str = result_text.split('```json')[1].split('```')[0].strip()
            else:
                json_str = result_text.strip()

            return json.loads(json_str)

        except Exception as e:
            print(f"LLM 分析失败: {e}")
            return {}

    def _build_analysis_prompt(
        self,
        memories_by_category: Dict[str, List[str]],
        total_memories: int
    ) -> str:
        """构建分析提示词"""
        prompt = f"""基于以下 {total_memories} 条用户记忆，分析和更新用户的身份和灵魂特征。

# 记忆分类汇总：

"""

        for category, items in memories_by_category.items():
            prompt += f"## {category}\n"
            for i, item in enumerate(items[:10], 1):  # 最多展示 10 条
                prompt += f"{i}. {item}\n"
            if len(items) > 10:
                prompt += f"... 还有 {len(items) - 10} 条\n"
            prompt += "\n"

        prompt += """# 任务
请基于上述记忆，生成以下 JSON 格式的分析结果：

{
  "identity": {
    "expertise": ["新增专业领域列表"],
    "preferred_language": "偏好语言",
    "communication_style": "沟通风格描述",
    "key_facts": ["新的关键事实"]
  },
  "soul": {
    "core_values": ["新增核心价值观"],
    "personality_traits": ["新增性格特征"],
    "working_style": "更新后的工作方式",
    "motivations": ["新增动机"],
    "concerns": ["新增关注点"]
  },
  "summary": "整体分析摘要（1-2句话）"
}

要求：
1. 只添加新的信息，避免重复现有内容
2. 专业领域、关键事实等应该具体且有用
3. 所有列表项都应简洁（10-20字以内）
4. 如果某些字段没有新增信息，请使用空数组或""
5. 返回纯 JSON 格式，不要包含其他文字

"""

        return prompt

    def update_identity_and_soul(self, dry_run: bool = False) -> UpdateResult:
        """
        更新身份和灵魂

        Args:
            dry_run: 是否为演练模式（不实际保存）

        Returns:
            更新结果
        """
        result = UpdateResult()

        # 1. 收集近期记忆
        recent_memories = self.gather_recent_memories(days=7, min_confidence=0.7)
        result.memories_added = len(recent_memories)

        if not recent_memories:
            print("近期没有足够的记忆可供分析")
            return result

        # 2. 使用 LLM 分析记忆
        print(f"分析 {len(recent_memories)} 条近期记忆...")
        analysis = self.analyze_memories_with_llm(recent_memories)

        if not analysis:
            print("LLM 分析未返回有效结果")
            return result

        # 3. 更新 Identity
        identity_changes = self._apply_identity_updates(analysis.get('identity', {}))
        result.identity_updates = identity_changes

        # 4. 更新 Soul
        soul_changes = self._apply_soul_updates(analysis.get('soul', {}))
        result.soul_updates = soul_changes

        # 5. 去重和优化
        if self.update_config.deduplicate:
            consolidated = self._deduplicate_memories()
            result.memories_consolidated = consolidated

        # 6. 保存到文件
        if not dry_run:
            self._save_identity()
            self._save_soul()
            print(f"✅ 身份更新：{len(identity_changes)} 项")
            print(f"✅ 灵魂更新：{len(soul_changes)} 项")
            print(f"✅ 记忆合并：{consolidated} 项")

        return result

    def _apply_identity_updates(self, updates: Dict[str, Any]) -> List[str]:
        """应用身份更新"""
        changes = []

        if 'expertise' in updates:
            new_expertise = set(updates['expertise'])
            old_expertise = set(self.identity.expertise)
            added = new_expertise - old_expertise

            if added:
                self.identity.expertise.extend(list(added))
                changes.append(f"专业领域: {', '.join(added)}")

        if 'preferred_language' in updates and updates['preferred_language']:
            if self.identity.preferred_language != updates['preferred_language']:
                changes.append(f"偏好语言: {self.identity.preferred_language} → {updates['preferred_language']}")
                self.identity.preferred_language = updates['preferred_language']

        if 'communication_style' in updates and updates['communication_style']:
            if self.identity.communication_style != updates['communication_style']:
                changes.append(f"沟通风格: 更新为 {updates['communication_style']}")
                self.identity.communication_style = updates['communication_style']

        if 'key_facts' in updates:
            new_facts = set(updates['key_facts'])
            old_facts = set(self.identity.key_facts)
            added = new_facts - old_facts

            if added:
                self.identity.key_facts.extend(list(added))
                changes.append(f"关键事实: 添加 {len(added)} 项")

        self.identity.last_updated = datetime.now()
        return changes

    def _apply_soul_updates(self, updates: Dict[str, Any]) -> List[str]:
        """应用灵魂更新"""
        changes = []

        if 'core_values' in updates:
            new_values = set(updates['core_values'])
            old_values = set(self.soul.core_values)
            added = new_values - old_values

            if added:
                self.soul.core_values.extend(list(added))
                changes.append(f"核心价值观: {', '.join(added)}")

        if 'personality_traits' in updates:
            new_traits = set(updates['personality_traits'])
            old_traits = set(self.soul.personality_traits)
            added = new_traits - old_traits

            if added:
                self.soul.personality_traits.extend(list(added))
                changes.append(f"性格特征: {', '.join(added)}")

        if 'working_style' in updates and updates['working_style']:
            if self.soul.working_style != updates['working_style']:
                changes.append(f"工作方式: 更新为 {updates['working_style']}")
                self.soul.working_style = updates['working_style']

        if 'motivations' in updates:
            new_motivations = set(updates['motivations'])
            old_motivations = set(self.soul.motivations)
            added = new_motivations - old_motivations

            if added:
                self.soul.motivations.extend(list(added))
                changes.append(f"内在动机: 添加 {len(added)} 项")

        if 'concerns' in updates:
            new_concerns = set(updates['concerns'])
            old_concerns = set(self.soul.concerns)
            added = new_concerns - old_concerns

            if added:
                self.soul.concerns.extend(list(added))
                changes.append(f"关注点: 添加 {len(added)} 项")

        self.soul.last_updated = datetime.now()
        return changes

    def _deduplicate_memories(self) -> int:
        """
        去重记忆（基于语义相似度）
        注意：这需要调用向量存储，避免循环依赖
        TODO: 实现记忆去重逻辑
        """
        # 这里可以添加基于向量相似度的去重逻辑
        # 暂时返回 0
        return 0

    def _save_identity(self) -> None:
        """保存身份到文件"""
        identity_file = self.memories_dir / "identity.md"
        identity_file.write_text(self.identity.to_markdown(), encoding='utf-8')

    def _save_soul(self) -> None:
        """保存灵魂到文件"""
        soul_file = self.memories_dir / "soul.md"
        soul_file.write_text(self.soul.to_markdown(), encoding='utf-8')

    def get_current_identity(self) -> Identity:
        """获取当前身份"""
        return self.identity

    def get_current_soul(self) -> Soul:
        """获取当前灵魂"""
        return self.soul

    def get_identity_context(self) -> str:
        """
        获取用于 Claude 提示的身份上下文

        Returns:
            格式化的身份信息字符串
        """
        expertise = ', '.join(self.identity.expertise) if self.identity.expertise else '暂无专业领域信息'
        facts = '\n- '.join(self.identity.key_facts) if self.identity.key_facts else '暂无关键事实'

        context = f"""# 用户身份信息（动态记忆）

## 基本资料
- 专业领域: {expertise}
- 偏好语言: {self.identity.preferred_language}
- 沟通风格: {self.identity.communication_style or '未记录'}

## 关键事实
- {facts}

**最后更新**: {self.identity.last_updated.strftime('%Y-%m-%d %H:%M')}
"""
        return context

    def get_soul_context(self) -> str:
        """
        获取用于 Claude 提示的灵魂上下文

        Returns:
            格式化的灵魂特征字符串
        """
        values = '\n- '.join(self.soul.core_values) if self.soul.core_values else '未记录'
        traits = ', '.join(self.soul.personality_traits) if self.soul.personality_traits else '未记录'
        motivations = '\n- '.join(self.soul.motivations) if self.soul.motivations else '未记录'
        concerns = '\n- '.join(self.soul.concerns) if self.soul.concerns else '未记录'

        context = f"""# 用户灵魂特征（动态记忆）

## 核心价值观
- {values}

## 性格特征
{traits}

## 工作方式
{self.soul.working_style or '未记录'}

## 内在动机
- {motivations}

## 关注点
- {concerns}

**最后更新**: {self.soul.last_updated.strftime('%Y-%m-%d %H:%M')}
"""
        return context
