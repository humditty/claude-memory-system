#!/usr/bin/env python3
"""
记忆系统主程序 - 命令行接口

使用方式：
1. 作为独立服务运行：python main.py --serve
2. 手动触发处理：python main.py --process
3. 搜索记忆：python main.py --search "查询内容"
4. 查看统计：python main.py --stats
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

from memory_manager import MemoryManager
from config_loader import MemorySystemConfig


def print_colored(text: str, color: str = "green") -> None:
    """打印彩色文本（简化版，实际可以使用 rich 库）"""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")


def cmd_init(manager: MemoryManager) -> int:
    """初始化命令"""
    print_colored("初始化记忆系统...", "blue")
    stats = manager.get_stats()
    print(f"📊 系统统计:")
    print(f"   向量库路径: {stats['vector_store_path']}")
    print(f"   对话数量: {stats['conversations_count']}")
    print(f"   记忆总数: {stats['total_memories']}")
    print(f"   身份更新: {stats['identity_last_updated'].strftime('%Y-%m-%d %H:%M') if stats['identity_last_updated'] else '从未'}")
    print(f"   灵魂更新: {stats['soul_last_updated'].strftime('%Y-%m-%d %H:%M') if stats['soul_last_updated'] else '从未'}")
    print_colored("✅ 初始化完成", "green")
    return 0


def cmd_process(manager: MemoryManager, days: int = 1) -> int:
    """处理命令：提取记忆并更新身份"""
    print_colored(f"开始处理最近 {days} 天的对话...", "blue")

    # 步骤1：提取并存储记忆
    memories = manager.extract_and_store_memories(days=days)
    print(f"📝 提取了 {len(memories)} 条记忆")

    if memories:
        # 显示类别分布
        from collections import Counter
        categories = [m['category'] for m in memories]
        cat_counts = Counter(categories)
        print("   类别分布:")
        for cat, count in cat_counts.most_common():
            print(f"     {cat}: {count}")

    # 步骤2：更新身份
    result = manager.update_identity(dry_run=False)
    print(f"\n🔄 身份更新结果:")
    print(f"   记忆分析: {len(memories)} 条")
    print(f"   身份更新项: {len(result.identity_updates)}")
    if result.identity_updates:
        for update in result.identity_updates[:5]:  # 只显示前5项
            print(f"     • {update}")
        if len(result.identity_updates) > 5:
            print(f"     ... 还有 {len(result.identity_updates)-5} 项")

    print(f"   灵魂更新项: {len(result.soul_updates)}")
    if result.soul_updates:
        for update in result.soul_updates[:5]:
            print(f"     • {update}")
        if len(result.soul_updates) > 5:
            print(f"     ... 还有 {len(result.soul_updates)-5} 项")

    print(f"   记忆合并: {result.memories_consolidated}")

    print_colored("\n✅ 处理完成", "green")
    return 0


def cmd_search(manager: MemoryManager, query: str, category: str = None, top_k: int = 5) -> int:
    """搜索命令"""
    print_colored(f"搜索: {query}", "blue")
    if category:
        print(f"   类别: {category}")

    results = manager.search_memories(query, category=category, top_k=top_k)

    if not results:
        print_colored("未找到相关记忆", "yellow")
        return 0

    print(f"\n找到 {len(results)} 条相关记忆:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. [{result['category']}] 置信度: {result['confidence']:.1%} 相似度: {result['similarity']:.1%}")
        print(f"   {result['content']}")
        if result['tags']:
            print(f"   标签: {', '.join(result['tags'][:3])}")
        print()

    return 0


def cmd_identity(manager: MemoryManager) -> int:
    """显示身份信息"""
    identity_ctx = manager.get_identity_context()
    soul_ctx = manager.get_soul_context()

    print(identity_ctx)
    print("\n" + "="*50 + "\n")
    print(soul_ctx)
    return 0


def cmd_stats(manager: MemoryManager) -> int:
    """显示统计信息"""
    stats = manager.get_stats()

    print("📊 记忆系统统计:\n")
    print(f"向量库路径: {stats['vector_store_path']}")
    print(f"记忆总数: {stats['total_memories']}")
    print(f"对话总数: {stats['conversations_count']}")
    print(f"身份最后更新: {stats['identity_last_updated'].strftime('%Y-%m-%d %H:%M') if stats['identity_last_updated'] else '从未'}")
    print(f"灵魂最后更新: {stats['soul_last_updated'].strftime('%Y-%m-%d %H:%M') if stats['soul_last_updated'] else '从未'}")

    # 显示类别统计
    all_memories = manager.get_all_memories()
    if all_memories:
        from collections import Counter
        categories = [m['category'] for m in all_memories]
        cat_counts = Counter(categories)

        print("\n记忆类别分布:")
        for cat, count in cat_counts.most_common():
            print(f"  {cat}: {count}")

    return 0


def cmd_cleanup(manager: MemoryManager, days: int = 30) -> int:
    """清理旧文件"""
    print_colored(f"清理 {days} 天前的旧文件...", "yellow")
    cleaned = manager.cleanup_old_files(days)
    print(f"✅ 清理了 {cleaned} 个文件")
    return 0


def cmd_export(manager: MemoryManager, output_path: str = None) -> int:
    """导出记忆为 JSON"""
    memories = manager.get_all_memories()

    if not memories:
        print("没有记忆可导出")
        return 0

    export_data = {
        "exported_at": datetime.now().isoformat(),
        "total_memories": len(memories),
        "memories": memories,
        "identity": manager.identity_updater.get_identity_context(),
        "soul": manager.identity_updater.get_soul_context()
    }

    output_file = output_path or f"./memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

    print(f"✅ 已导出 {len(memories)} 条记忆到: {output_file}")
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Claude 记忆管理系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --process           # 处理最近1天的对话
  %(prog)s --process --days 7  # 处理最近7天的对话
  %(prog)s --search "Python编程"  # 搜索记忆
  %(prog)s --identity          # 显示身份信息
  %(prog)s --stats             # 显示统计信息
  %(prog)s --export            # 导出记忆
  %(prog)s --cleanup --days 30 # 清理30天前的文件
        """
    )

    parser.add_argument("--config", default="./config.yaml",
                       help="配置文件路径（默认: ./config.yaml）")
    parser.add_argument("--process", action="store_true",
                       help="处理对话并更新记忆")
    parser.add_argument("--days", type=int, default=1,
                       help="处理最近N天的对话（默认: 1）")
    parser.add_argument("--search", metavar="QUERY",
                       help="搜索记忆")
    parser.add_argument("--category",
                       help="搜索的类别（与--search一起使用）")
    parser.add_argument("--top-k", type=int, default=5,
                       help="搜索结果数量（默认: 5）")
    parser.add_argument("--identity", action="store_true",
                       help="显示身份信息")
    parser.add_argument("--soul", action="store_true",
                       help="显示灵魂特征")
    parser.add_argument("--stats", action="store_true",
                       help="显示统计信息")
    parser.add_argument("--init", action="store_true",
                       help="初始化并查看状态")
    parser.add_argument("--cleanup", action="store_true",
                       help="清理旧文件")
    parser.add_argument("--export", metavar="OUTPUT", nargs="?",
                       help="导出记忆为JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 检查配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        print_colored(f"配置文件不存在: {config_path}", "red")
        print("请复制 config.yaml.example 并配置你的 LLM API 密钥")
        return 1

    try:
        # 初始化管理器
        manager = MemoryManager(config_path=str(config_path))

        # 执行命令
        if args.init:
            return cmd_init(manager)
        elif args.process:
            return cmd_process(manager, days=args.days)
        elif args.search:
            return cmd_search(manager, args.search, args.category, args.top_k)
        elif args.identity:
            return cmd_identity(manager)
        elif args.soul:
            print(manager.get_soul_context())
            return 0
        elif args.stats:
            return cmd_stats(manager)
        elif args.cleanup:
            return cmd_cleanup(manager, args.days)
        elif args.export is not None:
            output_path = args.export if isinstance(args.export, str) else None
            return cmd_export(manager, output_path)
        else:
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        print_colored("\n❌ 用户中断", "yellow")
        return 130
    except Exception as e:
        print_colored(f"\n❌ 错误: {e}", "red")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
