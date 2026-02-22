# Claude 记忆管理系统

一个智能的用户记忆管理系统，用于自动保存对话、提取偏好、更新身份，并提供语义检索功能。

## 📋 目录

1. [系统架构](#系统架构)
2. [快速开始](#快速开始)
3. [核心功能](#核心功能)
4. [集成到工作流](#集成到工作流)
5. [配置文件说明](#配置文件说明)
6. [API 参考](#api-参考)
7. [最佳实践](#最佳实践)

---

## 🏗️ 系统架构

```
memory_workspace/
├── conversations/           # 原始对话存储（按日期）
│   ├── 2025-02-22.md
│   ├── 2025-02-21.md
│   └── 2025-02-21.json
├── memories/              # 提炼后的结构化记忆
│   ├── preferences.md     # 写作偏好、语气风格
│   ├── identity.md        # 动态身份信息
│   ├── soul.md           # 性格特征、价值观
│   ├── stocks.md         # 股票追踪
│   └── email_rules.md    # 邮件分类规则
├── vector_store/         # 向量数据库（ChromaDB）
│   ├── chroma.sqlite3
│   └── embeddings/
├── config.yaml          # 配置文件
├── logs/
│   └── memory_system.log
```

### 四大核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 对话保存 | `conversation_saver.py` | 自动保存对话为 markdown 和 JSON |
| 记忆提取 | `memory_extractor.py` | 使用 LLM 从对话提取结构化记忆 |
| 身份更新 | `identity_updater.py` | 基于记忆更新 identity.md 和 soul.md |
| 向量检索 | `vector_store.py` | 使用 ChromaDB 实现 RAG 搜索 |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆或创建项目目录
cd /path/to/your/project

# 安装依赖
pip install -r requirements.txt

# 配置 LLM API（支持 OpenAI 或 Anthropic）
export OPENAI_API_KEY="your-api-key"
# 或编辑 config.yaml 中的 api_key
```

### 2. 配置系统

复制并编辑配置文件：

```yaml
# config.yaml
llm:
  provider: "openai"          # openai 或 anthropic
  api_key: "${OPENAI_API_KEY}"  # 环境变量或直接填写
  model: "gpt-4o-mini"       # 使用的模型
  temperature: 0.3

embeddings:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384

memory_extraction:
  auto_extract: true         # 对话后自动提取
  min_conversation_length: 100

identity_update:
  frequency: "daily"         # daily, weekly, manual
  deduplicate: true
```

### 3. 初始化

```bash
# 查看系统状态
python main.py --init
```

### 4. 首次处理

```bash
# 处理所有历史对话
python main.py --process --days 30

# 查看提取的记忆
python main.py --search "Python"
```

---

## ⚙️ 核心功能

### 功能1：对话记忆自动保存

**自动化流程**：每次对话结束后，自动保存到 `conversations/YYYY-MM-DD.md`

#### 使用示例

```python
from memory_manager import MemoryManager

# 初始化
manager = MemoryManager()

# 记录对话
conversation = manager.record_conversation(
    user_input="我想学习 React",
    assistant_response="React 是一个流行的前端框架...",
    metadata={"topic": "前端开发"}
)
```

**保存的文件格式**：

```markdown
# 对话记录

时间: 2025-02-22 14:30:00
对话ID: abc-123-def

## 用户输入
我想学习 React

## Claude 回复
React 是一个流行的前端框架...
```

### 功能2：偏好提炼

**自动提取**：使用 LLM 从对话中提取 8 类记忆

| 类别 | 描述 | 示例 |
|------|------|------|
| 写作偏好 | 文档风格、格式喜好 | "喜欢代码块高亮" |
| 语气风格 | 沟通语气偏好 | "喜欢简洁直接的表达" |
| 关注兴趣 | 兴趣领域 | "关注 AI 和自动化" |
| 股票追踪 | 股票和投资 | "持有 AAPL 和 TSLA" |
| 邮件分类规则 | 邮件过滤规则 | "重要邮件标红" |
| 个人背景 | 职业、教育 | "5年Python开发经验" |
| 工作习惯 | 工作时间、工具 | "夜猫子，喜欢VSCode" |
| 技术偏好 | 技术栈偏好 | "主要用FastAPI做后端" |

#### 提取流程

```python
# 自动提取（对话保存时触发）
memories = manager.extract_and_store_memories(days=1)

# 查看结果
for memory in memories:
    print(f"[{memory['category']}] {memory['content']}")
    print(f"置信度: {memory['confidence']:.1%}")
```

### 功能3：身份更新

**自动更新**：每天首次使用时，分析最近 7 天的记忆，更新身份和灵魂特征

#### 身份结构（identity.md）

```markdown
# 身份信息

## 基本资料
- 名称: 用户
- 专业领域: Python, Django, React
- 偏好语言: 中文
- 沟通风格: 简洁直接

## 关键事实
- 有 5 年全栈开发经验
- 目前在一个创业公司担任 Tech Lead
- 喜欢阅读技术博客
```

#### 灵魂特征（soul.md）

```markdown
# 灵魂特征

## 核心价值观
- 追求代码优雅和简洁
- 相信自动化能解放生产力

## 性格特征
理性, 逻辑思维强, 追求完美

## 工作方式
喜欢深夜编程，使用 VSCode，重度依赖 CLI 工具

## 内在动机
- 希望构建改变世界的产品
- 享受解决复杂技术挑战的过程
```

### 功能4：向量化检索（RAG）

**语义搜索**：基于 ChromaDB 和 sentence-transformers

```python
# 简单搜索
results = manager.search_memories("如何优化代码", top_k=5)

for r in results:
    print(f"相似度: {r['similarity']:.1%}")
    print(f"类别: {r['category']}")
    print(f"内容: {r['content']}\n")

# 按类别搜索
python_memories = manager.search_memories(
    query="Python性能优化",
    category="技术偏好",
    top_k=10
)
```

---

## 🔌 集成到工作流

### 方式1：使用 MemoryClient（推荐）

`MemoryClient` 提供了最简单的集成方式，适用于任何 Python 项目：

```python
from memory_client import MemoryClient

# 获取单例（自动初始化）
client = MemoryClient()

# 在对话处理完成后记录
def handle_chat(user_msg: str, assistant_msg: str):
    # 你的处理逻辑...
    response = generate_response(user_msg)

    # 记录到记忆系统（异步，不阻塞）
    client.record(user_msg, response)

    return response
```

#### 注入记忆上下文到 Claude 提示

```python
from memory_client import MemoryClient
import anthropic

client = MemoryClient()
claude = anthropic.Anthropic()

def chat_with_memory(user_input: str):
    # 获取记忆上下文
    identity_ctx = client.get_identity_context()
    soul_ctx = client.get_soul_context()

    # 构建系统提示
    system_prompt = f"""
{identity_ctx}
{soul_ctx}

请根据上述用户特征，用合适的语气和风格回复。
"""

    # 调用 Claude
    response = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}]
    )

    # 记录这次对话
    client.record(user_input, response.content[0].text)

    return response.content[0].text
```

### 方式2：命令行集成

在 shell 脚本或自动化流程中使用 CLI：

```bash
#!/bin/bash
# daily_memory_update.sh

# 每天早上运行
python main.py --process --days 1

# 导出备份
python main.py --export "./backup/memories_$(date +%Y%m%d).json"

# 清理30天前的文件
python main.py --cleanup --days 30
```

#### crontab 示例

```bash
# 每天凌晨 2 点自动处理
0 2 * * * cd /path/to/project && python main.py --process --days 1 >> /var/log/memory.log 2>&1

# 每周一凌晨 3 点强制更新身份
0 3 * * 1 cd /path/to/project && python main.py --process --days 7
```

### 方式3：Jupyter Notebook 集成

```python
# notebook_extension.py
from memory_client import MemoryClient
from IPython.core.getipython import get_ipython

client = MemoryClient()

# 注册 pre-run 钩子
ip = get_ipython()

def record_cell(cell):
    # 这里可以记录代码执行等
    pass

# 每次执行 cell 后记录
ip.events.register('post_run_cell', record_cell)
```

---

## ⚙️ 配置文件说明

### 完整配置示例

```yaml
# config.yaml

# LLM 配置（用于记忆提取）
llm:
  provider: "openai"              # openai, anthropic, local
  api_key: "${OPENAI_API_KEY}"    # 从环境变量读取
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o-mini"           # 推荐：gpt-4o-mini（性价比高）
  max_tokens: 4096
  temperature: 0.3                # 低温度确保一致性

# 嵌入模型配置
embeddings:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384

# 向量存储配置
vector_store:
  type: "chromadb"
  persist_directory: "./vector_store"
  collection_name: "conversation_memories"

# 记忆提取配置
memory_extraction:
  auto_extract: true              # 对话后自动提取
  min_conversation_length: 100    # 最少字符数才提取
  categories:                     # 自定义类别
    - "写作偏好"
    - "语气风格"
    - "关注兴趣"
    - "股票追踪"
    - "邮件分类规则"
    - "个人背景"
    - "工作习惯"
    - "技术偏好"
  max_memories_per_day: 20        # 每日最多提取数

# 身份更新配置
identity_update:
  frequency: "daily"              # daily, weekly, manual
  deduplicate: true               # 去重
  max_identity_items: 50          # 最多保留的记忆条数
  max_soul_items: 30

# 路径配置
paths:
  conversations: "./conversations"
  memories: "./memories"
  logs: "./logs"

# 日志配置
logging:
  level: "INFO"
  file: "./logs/memory_system.log"
  max_size_mb: 10
  backup_count: 5
```

### 使用环境变量

```bash
# .env 文件
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
```

config.yaml 中使用 `${VAR_NAME}` 语法引用。

---

## 📚 API 参考

### MemoryManager 类

#### `__init__(config_path="./config.yaml", llm_client=None)`
初始化记忆管理器

#### `record_conversation(user_input, assistant_response, metadata=None)`
同步保存对话，返回 Conversation 对象

#### `process_conversation_async(user_input, assistant_response, metadata=None)`
异步处理对话（推荐：不阻塞主流程）

#### `extract_and_store_memories(days=1, limit=None)`
手动提取记忆

#### `update_identity(dry_run=False)`
手动更新身份

#### `search_memories(query, category=None, top_k=5, min_confidence=0.0)`
搜索记忆

#### `get_identity_context()`
获取身份上下文字符串

#### `get_soul_context()`
获取灵魂上下文字符串

#### `get_stats()`
获取统计信息字典

---

### MemoryClient 类（单例）

#### `record(user_input, assistant_response, metadata=None, block=False)`
记录对话（推荐使用）

#### `search(query, category=None, top_k=5)`
搜索记忆

#### `get_identity_context()`
获取身份上下文

#### `get_soul_context()`
获取灵魂上下文

#### `get_full_context()`
获取完整上下文（身份+灵魂）

---

## 🎯 最佳实践

### 1. LLM 选择建议

| 使用场景 | 推荐模型 | 备注 |
|---------|---------|------|
| 记忆提取 | gpt-4o-mini | 性价比高，速度快 |
| 身份更新 | gpt-4o 或 claude-3-5-sonnet | 需要更好的分析能力 |
| 本地部署 | 本地 Ollama 模型 | 需要配置 provider="local" |

### 2. 性能优化

```python
# 批量处理历史对话（避免频繁API调用）
manager.extract_and_store_memories(days=30, limit=100)

# 使用异步模式避免阻塞
client.record(user_msg, response, block=False)

# 定期清理（通过crontab）
0 3 * * 0 python main.py --cleanup --days 90
```

### 3. 记忆质量提升

```yaml
# 调整提取参数
memory_extraction:
  min_conversation_length: 200      # 避免太短的对话
  max_memories_per_day: 50          # 提高上限捕获更多信息

# 降低温度提高一致性
llm:
  temperature: 0.1                  # 更确定性
```

### 4. 隐私考虑

```bash
# 敏感信息过滤 - 在 config.yaml 中添加
memory_extraction:
  exclude_patterns:
    - "密码"
    - "密钥"
    - "token"

# 或定期清理敏感对话
# conversations/ 目录可以单独加密备份
```

### 5. 监控和维护

```bash
# 创建监控脚本
#!/bin/bash
# check_memory_system.sh
python main.py --stats
python main.py --search "最近新增" | head -20

# 添加到 crontab（每天检查）
0 6 * * * /path/to/check_memory_system.sh >> /var/log/memory_health.log
```

---

## 🛠️ 故障排除

### 问题1：API 调用失败

**症状**：`MemoryExtractor` 报错

**解决**：
1. 检查 API 密钥是否正确
2. 检查网络连接
3. 确认账户余额/限额

### 问题2：向量库无法加载

**症状**：`ChromaDB` 报错

**解决**：
```bash
# 重建向量库
rm -rf vector_store/
python main.py --process --days 30
```

### 问题3：提取的记忆质量差

**原因**：提示词不够优化或模型能力不足

**解决**：
1. 调整 `memory_extractor.py` 中的提示词
2. 切换到更强的模型（如 gpt-4o）
3. 增加 `min_conversation_length` 阈值

---

## 📈 扩展建议

### 可能的扩展功能

1. **多模态记忆**：支持图片、文件附件
2. **情感分析**：记录用户情绪变化
3. **知识图谱**：将记忆关联成图谱
4. **时间感知**：记忆的时间衰减权重
5. **Web UI**：记忆管理界面
6. **多用户支持**：每个用户独立记忆库

---

## 📄 文件清单

| 文件 | 用途 |
|------|------|
| `models.py` | 数据模型（Conversation, Memory, Identity, Soul） |
| `config_loader.py` | 配置文件加载和管理 |
| `conversation_saver.py` | 对话保存 |
| `memory_extractor.py` | LLM 记忆提取 |
| `vector_store.py` | ChromaDB 向量存储 |
| `identity_updater.py` | 身份更新逻辑 |
| `memory_manager.py` | 核心管理器 |
| `memory_client.py` | 便捷客户端（推荐） |
| `main.py` | CLI 命令行工具 |
| `config.yaml` | 配置文件模板 |
| `requirements.txt` | Python 依赖 |

---

## 🎉 开始使用

现在你可以：

1. **配置 LLM**：编辑 `config.yaml` 或设置环境变量
2. **初始化系统**：运行 `python main.py --init`
3. **处理历史对话**：运行 `python main.py --process --days 30`
4. **查看结果**：运行 `python main.py --identity` 和 `--stats`

**恭喜！你的 Claude 现在拥有记忆能力了 🧠**

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License

---

**最后更新**: 2025-02-22 | **版本**: 1.0.0
