"""
对话记忆自动保存模块
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import asdict
from .models import Conversation
from .config_loader import MemorySystemConfig, PathsConfig


class ConversationSaver:
    """对话保存器"""

    def __init__(self, config: MemorySystemConfig):
        """
        初始化对话保存器

        Args:
            config: 记忆系统配置
        """
        self.config = config
        self.conversations_dir = Path(config.paths.conversations)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

    def save_conversation(
        self,
        user_input: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        保存对话到文件

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            metadata: 额外元数据

        Returns:
            创建的 Conversation 对象
        """
        # 创建对话记录
        conversation = Conversation(
            timestamp=datetime.now(),
            user_input=user_input,
            assistant_response=assistant_response,
            metadata=metadata or {}
        )

        # 生成文件名（按日期）
        date_str = conversation.timestamp.strftime('%Y-%m-%d')
        filename = f"{date_str}.md"
        filepath = self.conversations_dir / filename

        # 读取或创建当天文件
        if filepath.exists():
            content = filepath.read_text(encoding='utf-8')
        else:
            content = f"# {date_str} 对话记录\n\n"

        # 追加新的对话
        content += conversation.to_markdown()

        # 保存文件
        filepath.write_text(content, encoding='utf-8')

        # 同时保存 JSON 格式供程序处理
        json_path = self.conversations_dir / f"{date_str}.json"
        self._save_json(conversation, json_path)

        return conversation

    def _save_json(self, conversation: Conversation, json_path: Path) -> None:
        """保存对话为 JSON 格式"""
        if json_path.exists():
            # 追加到现有 JSON 数组
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []

        data.append(asdict(conversation))

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def load_conversations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[Conversation]:
        """
        加载指定时间范围内的对话

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            对话列表
        """
        conversations = []

        for json_file in self.conversations_dir.glob("*.json"):
            # 这里简化处理，实际应该根据日期过滤
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                        conv = Conversation(**item)
                        conversations.append(conv)
            except Exception as e:
                print(f"加载对话文件 {json_file} 失败: {e}")

        # 按时间排序
        conversations.sort(key=lambda x: x.timestamp)

        return conversations

    def get_today_conversations(self) -> list[Conversation]:
        """获取今天的对话"""
        today = datetime.now().date()
        all_conversations = self.load_conversations()

        return [
            conv for conv in all_conversations
            if conv.timestamp.date() == today
        ]

    def cleanup_old_conversations(self, days: int = 30) -> int:
        """
        清理旧的对话文件

        Args:
            days: 保留天数

        Returns:
            清理的文件数量
        """
        cutoff_date = datetime.now().date().replace(day=datetime.now().day - days)
        cleaned = 0

        for md_file in self.conversations_dir.glob("*.md"):
            try:
                # 从文件名解析日期
                date_str = md_file.stem
                file_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                if file_date < cutoff_date:
                    md_file.unlink()
                    json_file = md_file.with_suffix('.json')
                    if json_file.exists():
                        json_file.unlink()
                    cleaned += 1
            except Exception as e:
                print(f"清理文件 {md_file} 失败: {e}")

        return cleaned
