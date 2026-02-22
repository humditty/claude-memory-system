# 🔄 集成到 Claude Code 工作流

本指南详细说明如何将记忆系统集成到你的 **Claude Code CLI** 日常工作中。

---

## 📋 目录

1. [集成方式总览](#集成方式总览)
2. [方式A：API 调用方式](#方式a-api-调用方式)
3. [方式B：Claude Code Skill](#方式b-claude-code-skill)
4. [方式C：Git Hook](#方式c-git-hook)
5. [方式D：Shell 别名](#方式d-shell-别名)
6. [最佳实践](#最佳实践)

---

## 🎯 集成方式总览

| 方式 | 优点 | 复杂度 | 适合场景 |
|------|------|--------|---------|
| API 调用 | 最灵活，可自定义 | 简单 | 所有 Python 项目 |
| Claude Skill | 最无缝，只需 `/memory` 命令 | 中等 | 与 Claude CLI 深度集成 |
| Git Hook | 自动触发，无需干预 | 中等 | 代码提交时记录 |
| Shell 别名 | 最简单快捷 | 简单 | 快速命令 |

---

## 方式A：API 调用方式

### 场景：在 Python 脚本中直接使用

#### 示例1：集成到数据分析流程

```python
# data_analysis_with_memory.py
from memory_client import MemoryClient
import pandas as pd

client = MemoryClient()

def analyze_sales_data(filepath: str):
    """分析销售数据并记录思考过程"""

    # 1. 记录思考开始
    query = "如何分析这份销售数据？"
    print(f"🤔 {query}")
    client.record(query, "开始分析...")

    # 2. 加载数据
    df = pd.read_csv(filepath)
    insights = f"数据包含 {len(df)} 行，销售额趋势..."

    # 3. 记录分析结果
    client.record(
        user_input=query,
        assistant_response=insights,
        metadata={"file": filepath, "rows": len(df)}
    )

    return insights

# 使用
result = analyze_sales_data("sales.csv")
print(result)
```

#### 示例2：代码审查助手

```python
# code_review_bot.py
from memory_client import MemoryClient
import os

client = MemoryClient()

def review_code_with_context(code_file: str):
    """根据用户历史偏好进行代码审查"""

    # 1. 获取相关记忆
    tech_prefs = client.search("技术偏好", category="技术偏好")
    work_style = client.search("工作习惯", category="工作习惯")

    # 2. 构建个性化审查提示
    prefs_summary = "\n".join([p['content'] for p in tech_prefs[:3]])

    review_prompt = f"""
用户偏好：
{prefs_summary}

请审查以下代码并基于用户偏好给出建议：
```
{open(code_file).read()}
```
    """

    # 3. 调用 Claude（实际代码）
    # response = claude.chat(review_prompt)

    # 4. 记录审查结果
    mock_response = "代码质量良好，建议添加类型注解..."
    client.record(
        user_input=f"审查 {code_file}",
        assistant_response=mock_response,
        metadata={"file": code_file, "type": "code_review"}
    )

    return mock_response
```

---

## 方式B：Claude Code Skill

Claude Code Skill 让你在 Claude CLI 中使用自定义命令。

### 步骤1：创建 Skill 文件

```bash
# 创建技能目录
mkdir -p ~/.claude/skills/memory_skill

# 创建技能定义
cat > ~/.claude/skills/memory_skill/skill.yaml << 'EOF'
name: memory
description: 记忆系统管理命令
version: 1.0.0
arguments:
  - name: command
    description: 要执行的命令
    required: true
    values:
      - search
      - identity
      - stats
      - record
EOF
```

### 步骤2：创建技能实现

```python
# ~/.claude/skills/memory_skill/skill.py
#!/usr/bin/env python3
from memory_client import MemoryClient
import sys
import json

client = MemoryClient()

def skill_search(query: str, category: str = None, top_k: int = 5):
    """搜索记忆"""
    results = client.search(query, category=category, top_k=top_k)

    print(f"🔍 搜索: {query}")
    print(f"找到 {len(results)} 条记忆:\n")

    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['category']}] {r['content']}")
        print(f"   相似度: {r['similarity']:.1%}\n")

def skill_identity():
    """显示身份"""
    print(client.get_identity_context())

def skill_soul():
    """显示灵魂"""
    print(client.get_soul_context())

def skill_stats():
    """显示统计"""
    stats = client.get_stats()
    for k, v in stats.items():
        print(f"{k}: {v}")

def skill_record(user_input: str, response: str):
    """手动记录对话"""
    client.record(user_input, response, block=True)
    print("✅ 已记录")

# 主入口
if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        category = sys.argv[3] if len(sys.argv) > 3 else None
        skill_search(query, category)
    elif command == "identity":
        skill_identity()
    elif command == "soul":
        skill_soul()
    elif command == "stats":
        skill_stats()
    elif command == "record":
        user_input = sys.argv[2] if len(sys.argv) > 2 else ""
        response = sys.argv[3] if len(sys.argv) > 3 else ""
        skill_record(user_input, response)
    else:
        print(f"未知命令: {command}")
```

```bash
chmod +x ~/.claude/skills/memory_skill/skill.py
```

### 步骤3：在 Claude Code 中使用

```bash
# 启动 Claude Code
claude

# 在对话中使用你的技能
/claude 输入：/memory search "Python"
/claude 输入：/memory identity
/claude 输入：/memory stats
```

**输出**：直接在 Claude Code 界面中显示。

---

## 方式C：Git Hook

在每次 `git commit` 时自动记录相关对话。

### 步骤1：创建 Git Hook

```bash
# 在项目根目录：.git/hooks/post-commit
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# Git post-commit hook：记录提交信息

# 获取最近一次提交信息（排除自动提交）
COMMIT_MSG=$(git log -1 --pretty=%B)

# 简单的关键词过滤，只记录包含 "memory" 或特定标签的提交
# 可以根据需要调整
if echo "$COMMIT_MSG" | grep -qiE "(memory|feat|chore)"; then
    python3 -c "
from memory_client import MemoryClient
client = MemoryClient()
client.record(
    user_input='Git提交',
    assistant_response='$COMMIT_MSG',
    metadata={'type': 'git_commit', 'repo': '$(basename $(pwd))'}
)
    " 2>/dev/null || true
fi
EOF

chmod +x .git/hooks/post-commit
```

### 步骤2：全局 Git Hook 模板

如果你希望所有项目都能使用：

```bash
# 创建全局模板
mkdir -p ~/.git-templates/hooks
cp your-post-commit-hook ~/.git-templates/hooks/post-commit

# 设置 Git 使用模板
git config --global init.templateDir ~/.git-templates
```

---

## 方式D：Shell 别名

最简单的集成方式：添加别名到你的 `~/.bashrc` 或 `~/.zshrc`。

```bash
# ~/.bashrc 或 ~/.zshrc

# 记忆系统别名
alias memory-search='python3 /path/to/project/main.py --search'
alias memory-identity='python3 /path/to/project/main.py --identity'
alias memory-stats='python3 /path/to/project/main.py --stats'
alias memory-process='python3 /path/to/project/main.py --process --days 1'
alias memory-cleanup='python3 /path/to/project/main.py --cleanup --days 30'
```

**使用**：

```bash
memory-search "React教程"
memory-identity
memory-stats
```

---

## 🏆 最佳实践

### ✅ 推荐的集成方式

**对于大多数用户**：使用 `MemoryClient()` 直接在代码中集成

```python
# my_assistant.py
from memory_client import MemoryClient

client = MemoryClient()

def handle_message(user_msg):
    # 获取上下文
    context = client.get_full_context()

    # 调用 Claude...
    response = claude.generate(user_msg, context=context)

    # 记录
    client.record(user_msg, response)

    return response
```

### ⚡ 性能优化

```python
# 使用异步模式避免阻塞
client = MemoryClient()

def chat_handler(user_msg):
    # 立即返回，不等待记录完成
    response = generate_response(user_msg)
    client.record(user_msg, response, block=False)

    return response  # 立即返回给用户
```

### 🔒 隐私保护

```python
# 1. 过滤敏感信息
SENSITIVE_PATTERNS = ["密码", "密钥", "token", "api_key"]

def should_record(text: str) -> bool:
    """检查是否应该记录"""
    return not any(pattern in text for pattern in SENSITIVE_PATTERNS)

client = MemoryClient()

def safe_record(user_input, response):
    if should_record(user_input) and should_record(response):
        client.record(user_input, response)
    else:
        print("⚠️ 检测到敏感信息，跳过记录")
```

### 📊 监控和调试

```bash
# 创建监控脚本
cat > ~/bin/memory-monitor.sh << 'EOF'
#!/bin/bash
cd /path/to/memory-system

# 每日报告
echo "📊 记忆系统状态 - $(date)"
python main.py --stats
echo ""
echo "最近新增记忆："
python main.py --search "最近" --top-k 5
EOF

chmod +x ~/bin/memory-monitor.sh

# 添加到 crontab
0 8 * * * ~/bin/memory-monitor.sh >> ~/memory.log 2>&1
```

---

## 🔧 高级配置

### 自定义客户端实例

```python
# 多个项目使用不同的记忆库
client_a = MemoryClient(config_path="./project_a/config.yaml")
client_b = MemoryClient(config_path="./project_b/config.yaml")

# 独立运作，互不影响
```

### 批量导入历史对话

```python
# import_old_chats.py
from memory_client import MemoryClient

client = MemoryClient()

# 从旧系统导入
old_chats = load_old_chats()  # 你的旧数据格式

for chat in old_chats:
    client.record(
        user_input=chat['user'],
        assistant_response=chat['assistant'],
        metadata={"source": "legacy_system", "date": chat['date']}
    )

print(f"✅ 导入了 {len(old_chats)} 条历史对话")
```

---

## 🎯 场景示例

### 场景1：技术博客写作助手

```python
from memory_client import MemoryClient
import re

client = MemoryClient()

def get_writing_style_tips() -> str:
    """获取用户的写作偏好"""
    prefs = client.search("写作偏好", category="写作偏好")
    tips = []

    for pref in prefs:
        if "简洁" in pref['content']:
            tips.append("用户喜欢简洁表达")
        if "代码" in pref['content']:
            tips.append("用户重视代码示例")

    return "\n".join(tips) if tips else "暂无偏好记录"

def write_blog_post(topic: str):
    """写博客"""
    style = get_writing_style_tips()

    prompt = f"""
主题：{topic}

写作风格参考：
{style}

请撰写博客...
    """

    # ... 生成并记录
```

### 场景2：项目管理助手

```python
from memory_client import MemoryClient
from datetime import datetime

client = MemoryClient()

def log_project_update(project: str, progress: str):
    """记录项目进展"""
    client.record(
        user_input=f"项目 {project} 更新",
        assistant_response=progress,
        metadata={
            "type": "project_update",
            "date": datetime.now().isoformat(),
            "project": project
        }
    )

    # 搜索相关技术偏好在后续任务中使用
    prefs = client.search(f"{project} 技术", category="技术偏好")
```

### 场景3：邮件助手

```python
from memory_client import MemoryClient

client = MemoryClient()

def check_email_rules(subject: str, sender: str) -> str:
    """检查邮件分类规则"""
    rules = client.search("邮件分类", category="邮件分类规则")

    for rule in rules:
        if "重要" in rule['content'] and "老板" in subject:
            return "重要邮件"
        # ... 更多规则

    return "普通邮件"
```

---

## 🎉 总结

**推荐方案**：

1. **开发环境**：使用 `MemoryClient()` 直接集成
2. **Claude Code**：配置为 Skill (`/memory search xxx`)
3. **生产环境**：添加 crontab 定期处理
4. **团队**：共享 config.yaml，独立向量库

**核心优势**：

- 🚀 **零侵入**：只需添加 `client.record()` 调用
- ⚡ **异步**：不影响主流程性能
- 🔍 **智能检索**：语义搜索而非关键词匹配
- 📈 **自动进化**：身份自动更新

---

## 📚 参考文档

- `README.md` - 完整文档
- `QUICKSTART.md` - 5分钟快速开始
- `example_claude_workflow.py` - 完整示例代码

---

**开始集成吧！** 🚀
