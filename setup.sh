#!/bin/bash
#
# 记忆系统快速安装脚本
# 使用方法：bash setup.sh
#

set -e  # 遇到错误退出

echo "========================================"
echo "🧠 Claude 记忆系统 - 快速安装"
echo "========================================"
echo ""

# 1. 检查 Python 版本
echo "1️⃣  检查 Python 版本..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version (>= $required_version)"
else
    echo "⚠️  Python 版本较低，推荐 >= 3.9"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. 创建虚拟环境（可选）
echo ""
read -p "是否创建虚拟环境？(推荐，Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv

    # 激活虚拟环境
    source .venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
else
    echo "使用系统 Python..."
fi

# 3. 安装依赖
echo ""
echo "2️⃣  安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 依赖安装完成"

# 4. 检查环境变量
echo ""
echo "3️⃣  检查配置..."

if [ -f ".env" ]; then
    echo "✅ 找到 .env 文件"
else
    echo "⚠️  未找到 .env 文件"
    cp .env.example .env
    echo "   已创建 .env 文件，请编辑并填入 API 密钥"
fi

# 5. 创建必要的目录
echo ""
echo "4️⃣  创建目录..."
mkdir -p conversations memories vector_store logs
echo "✅ 目录创建完成"

# 6. 验证配置
echo ""
echo "5️⃣  验证配置..."

if grep -q "your-openai-api-key-here" .env 2>/dev/null; then
    echo "⚠️  请在 .env 文件中设置 API 密钥"
else
    echo "✅ 环境变量配置"
fi

# 7. 测试初始化
echo ""
echo "6️⃣  测试初始化..."
python3 -c "
from memory_manager import MemoryManager
print('✅ 模块导入成功')
" || {
    echo "❌ 模块导入失败，请检查依赖"
    exit 1
}

# 总结
echo ""
echo "========================================"
echo "🎉 安装完成！"
echo "========================================"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，填入你的 API 密钥"
echo "2. 编辑 config.yaml（可选，调整配置）"
echo "3. 运行 python main.py --init 查看系统状态"
echo "4. 运行 python main.py --process --days 30 处理历史对话"
echo "5. 查看 README.md 了解详细用法"
echo ""
echo "💡 快速开始示例："
echo "   python example_claude_workflow.py"
echo ""
echo "祝使用愉快！🚀"
