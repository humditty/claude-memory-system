#!/usr/bin/env python3
"""
记忆系统集成示例：展示如何在 Claude Code 工作流中使用记忆系统

这个示例模拟了真实的使用场景，展示如何将记忆系统集成到
你的日常对话、代码审查、架构设计等工作中。
"""

from memory_client import MemoryClient, get_context
import time
from typing import Dict


# ============================================================================
# 示例1：基础集成 - 每次对话后自动记录
# ============================================================================

def example_1_basic_integration():
    """
    示例1：基础集成方式
    每次对话处理完后调用 record() 函数
    """
    print("="*60)
    print("示例1：基础集成")
    print("="*60)

    client = MemoryClient()

    # 模拟对话
    user_input = "我想用 Python 写一个 REST API，有什么推荐吗？"
    assistant_response = "我推荐使用 FastAPI，它速度快、自动生成文档，并且有很好的类型支持。你也可以考虑 Flask（更轻量）或 Django REST Framework（功能全面）。"

    # 记录对话（异步，不阻塞）
    client.record(user_input, assistant_response)

    print(f"✅ 已记录对话")
    print(f"用户：{user_input[:50]}...")
    print(f"助手：{assistant_response[:50]}...")

    # 等待异步处理完成
    time.sleep(2)

    # 查看当前记忆
    stats = client.get_stats()
    print(f"\n📊 当前记忆总数: {stats.get('total_memories', 0)}")


# ============================================================================
# 示例2：注入记忆上下文
# ============================================================================

def example_2_context_injection():
    """
    示例2：在调用 Claude 前注入记忆上下文
    """
    print("\n" + "="*60)
    print("示例2：注入记忆上下文到 Claude")
    print("="*60)

    client = MemoryClient()

    # 获取完整的记忆上下文
    full_context = client.get_full_context()

    print("📋 注入的记忆上下文：")
    print("-" * 40)
    print(full_context[:500] + "...\n" if len(full_context) > 500 else full_context)

    # 模拟调用 Claude 的 API
    """
    import anthropic

    claude = anthropic.Anthropic()

    response = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        system=f"""
{full_context}

请根据上述用户特征，用合适的语气回复。
        """,
        messages=[{"role": "user", "content": "帮我写个 Python 脚本"}],
        max_tokens=1000
    )
    """

    print("\n✅ 上下文已注入到 Claude 系统提示中")


# ============================================================================
# 示例3：智能搜索记忆
# ============================================================================

def example_3_search():
    """
    示例3：使用语义搜索查找相关记忆
    """
    print("\n" + "="*60)
    print("示例3：语义搜索记忆")
    print("="*60)

    client = MemoryClient()

    queries = [
        "Python 相关",
        "工作习惯",
        "技术栈",
        "沟通偏好"
    ]

    for query in queries:
        print(f"\n🔍 搜索: {query}")
        results = client.search(query, top_k=3)

        if results:
            for i, r in enumerate(results, 1):
                print(f"  {i}. [{r['category']}] {r['content'][:60]}...")
                print(f"     相似度: {r['similarity']:.1%}")
        else:
            print("  未找到相关记忆")


# ============================================================================
# 示例4：工作流装饰器模式
# ============================================================================

def example_4_decorator_workflow():
    """
    示例4：使用装饰器自动记录对话
    """
    print("\n" + "="*60)
    print("示例4：装饰器模式 - 自动记录")
    print("="*60)

    client = MemoryClient()

    def auto_record(func):
        """装饰器：自动记录函数调用（模拟对话）"""
        def wrapper(user_input: str, *args, **kwargs):
            # 执行原函数
            assistant_response = func(user_input, *args, **kwargs)

            # 自动记录
            client.record(
                user_input=user_input,
                assistant_response=assistant_response,
                metadata={"function": func.__name__}
            )

            return assistant_response
        return wrapper

    # 使用装饰器装饰你的处理函数
    @auto_record
    def process_query(query: str) -> str:
        """模拟 Claude 回复"""
        responses = {
            "React": "React 是一个用于构建用户界面的 JavaScript 库。",
            "Python": "Python 是一种广泛使用的高级编程语言...",
            "Docker": "Docker 是一个容器化平台..."
        }

        for key, value in responses.items():
            if key.lower() in query.lower():
                return value

        return "我不确定，你能详细说明一下吗？"

    # 测试对话
    queries = [
        "我想学习 React，有什么建议？",
        "如何使用 Docker 部署？",
        "Python有什么新特性？"
    ]

    for q in queries:
        print(f"\n用户：{q}")
        response = process_query(q)
        print(f"助手：{response}")
        print("(已自动记录到记忆系统)")

    time.sleep(2)  # 等待异步处理


# ============================================================================
# 示例5：Claude Code Extension 集成
# ============================================================================

def example_5_claude_code_extension():
    """
    示例5：集成到 Claude Code Skill
    如果你使用 Claude Code CLI，可以在自定义 skill 中使用记忆系统
    """
    print("\n" + "="*60)
    print("示例5：Claude Code Skill 集成")
    print("="*60)

    print("""
在你的 skill 文件中：

```python
#!/usr/bin/env python3
from memory_client import MemoryClient

def my_custom_skill(user_input: str):
    client = MemoryClient()

    # 1. 检索相关记忆
    memories = client.search(user_input, top_k=3)
    if memories:
        print("找到相关记忆：")
        for m in memories:
            print(f"- {m['content']}")

    # 2. 你的技能逻辑...

    # 3. 记录本次执行
    result = "技能执行结果"
    client.record(user_input, result, metadata={"skill": "my_custom_skill"})

    return result
```

然后在 .claude/skills/ 目录下创建配置文件即可。
    """)


# ============================================================================
# 示例6：长期记忆管理
# ============================================================================

def example_6_long_term_management():
    """
    示例6：定期维护和统计
    """
    print("\n" + "="*60)
    print("示例6：记忆系统管理")
    print("="*60)

    client = MemoryClient()

    print("📊 系统统计：")
    stats = client.get_stats()

    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 强制更新身份（如果很久没更新了）
    print("\n🔄 强制更新身份...")
    success = client.force_update(dry_run=True)  # dry_run=True 只预览

    if success:
        print("✅ 身份更新流程正常（dry-run模式）")
    else:
        print("⚠️ 身份更新失败，请检查配置")


# ============================================================================
# 主函数：运行所有示例
# ============================================================================

def main():
    """运行所有示例"""
    print("\n" + "🧠"*30)
    print(" Claude 记忆系统集成示例")
    print(" 🧠"*30)

    examples = [
        example_1_basic_integration,
        example_2_context_injection,
        example_3_search,
        example_4_decorator_workflow,
        example_5_claude_code_extension,
        example_6_long_term_management
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ 示例执行失败: {e}")

    print("\n" + "="*60)
    print("✅ 所有示例执行完成！")
    print("="*60)

    print("""
📚 下一步：
1. 查看 README.md 了解详细文档
2. 配置你的 config.yaml（设置 API 密钥）
3. 运行 python main.py --process 处理历史对话
4. 开始在你的项目中使用 MemoryClient

💡 提示：
- 首次使用建议先运行 --init 查看状态
- 使用 --search 命令测试记忆检索
- 查看 --identity 查看自动更新的身份信息
    """)


if __name__ == "__main__":
    main()
