# 🚀 快速开始指南

5 分钟快速上手记忆系统。

---

## 📦 步骤1：安装（30秒）

```bash
# 克隆或进入项目目录
cd /your/project

# 运行安装脚本
bash setup.sh

# 或手动安装
pip install -r requirements.txt
```

---

## 🔑 步骤2：配置 API（1分钟）

### 编辑 `.env` 文件：

```bash
# 选择你的 LLM 提供商

# 选项A：使用 OpenAI（推荐）
OPENAI_API_KEY=sk-your-openai-api-key-here

# 选项B：使用 Anthropic
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### 或者直接编辑 `config.yaml`：

```yaml
llm:
  provider: "openai"
  api_key: "sk-your-api-key-here"
  model: "gpt-4o-mini"
```

---

## 🎯 步骤3：初始化（10秒）

```bash
# 查看系统状态
python main.py --init

# 输出应该类似：
# 📊 系统统计:
#   向量库路径: ./vector_store
#   对话数量: 0
#   记忆总数: 0
#   身份更新: 从未
```

---

## 📝 步骤4：记录第一次对话（立即生效）

### 方法A：使用 Python API

```python
# test_memory.py
from memory_client import MemoryClient

client = MemoryClient()

# 记录对话
client.record(
    user_input="你好，我叫张三，是一名Python工程师",
    assistant_response="你好张三！很高兴认识你。作为Python工程师，..."
)

print("✅ 对话已记录！")
```

运行：
```bash
python test_memory.py
```

### 方法B：使用 CLI 命令

```bash
# 手动添加一条测试对话
python main.py --process --days 1
```

---

## 🔍 步骤5：查看记忆（实时）

```bash
# 搜索记忆
python main.py --search "Python工程师"

# 输出：
# 1. [个人背景] 用户是一名Python工程师，有5年开发经验...
#    置信度: 85% 相似度: 78%
```

---

## 🧠 步骤6：身份更新（自动或手动）

```bash
# 手动触发身份更新
python main.py --process --days 7

# 查看身份信息
python main.py --identity
```

输出示例：
```markdown
# 用户身份信息（动态记忆）

## 基本资料
- 专业领域: Python, Django, React
- 偏好语言: 中文
- 沟通风格: 简洁直接

## 关键事实
- 有 5 年全栈开发经验
```

---

## 🎉 完成！你已设置成功

你现在拥有的能力：

✅ 自动保存所有对话
✅ 自动提取用户偏好
✅ 自动更新身份档案
✅ 语义搜索历史记忆
✅ 在 Claude 提示中注入上下文

---

## 🔄 日常使用流程

### 场景1：集成到你的聊天机器人

```python
from memory_client import MemoryClient, get_context
import claude

client = MemoryClient()

def chat_loop():
    while True:
        user_msg = input("用户: ")

        # 1. 检索相关记忆
        memories = client.search(user_msg, top_k=3)

        # 2. 构建系统提示
        system_prompt = f"""
{get_context()}

相关记忆：
{format_memories(memories)}

请根据上下文回复。
        """

        # 3. 调用 Claude
        response = claude.chat(user_msg, system=system_prompt)

        # 4. 记录对话
        client.record(user_msg, response)

        print(f"助手: {response}")

chat_loop()
```

### 场景2：代码审查助手

```python
from memory_client import MemoryClient

client = MemoryClient()

def review_code(user_code: str, user_query: str):
    # 获取用户的技术偏好
    tech_prefs = client.search("技术偏好", category="技术偏好", top_k=5)

    # 根据偏好调整审查重点
    review_focus = "性能和安全性" if "性能" in str(tech_prefs) else "代码可读性"

    prompt = f"""
用户关注：{review_focus}
历史偏好：{tech_prefs}

请审查以下代码：
{user_code}
    """

    # 调用 Claude 并记录...
    client.record(user_query, review_result)
```

### 场景3：自动化脚本（crontab）

```bash
# crontab -e

# 每天凌晨 2:00 处理当天对话并更新身份
0 2 * * * cd /path/to/project && /path/to/project/.venv/bin/python main.py --process --days 1

# 每周一凌晨 3:00 清理旧文件（保留60天）
0 3 * * 1 cd /path/to/project && /path/to/project/.venv/bin/python main.py --cleanup --days 60
```

---

## 🐛 常见问题

### Q1: 提取的记忆质量不高？
**A**: 更换更强的模型（gpt-4o）或调整提示词。

### Q2: 身份更新不频繁？
**A**: 检查 `identity_update.frequency` 配置。

### Q3: 想停止自动提取？
**A**: 设置 `memory_extraction.auto_extract: false`。

### Q4: 如何导出数据？
**A**: `python main.py --export backup.json`

### Q5: 向量库占用太大？
**A**: `python main.py --cleanup --days 90`

---

## 📖 更多资源

- 📚 **完整文档**: 查看 `README.md`
- 🔧 **API 文档**: 查看 `memory_client.py` 中的注释
- 💡 **示例**: 运行 `python example_claude_workflow.py`
- 🐛 **问题反馈**: 创建 GitHub Issue

---

**准备好了吗？开始记录你的记忆吧！** 🚀
