#!/bin/bash

# DocuFlow 安装脚本
# 适用于 macOS

echo "🚀 DocuFlow 文档转换器安装脚本"
echo "================================="

# 检查Python版本
echo "📋 检查Python版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ -z "$python_version" ]]; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.7或更高版本"
    exit 1
fi
echo "✅ Python版本: $python_version"

# 检查pip
echo "📋 检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到pip3"
    exit 1
fi
echo "✅ pip3 已安装"

# 创建虚拟环境
echo "📋 创建Python虚拟环境..."
if [ -d "venv" ]; then
    echo "⚠️  虚拟环境已存在，将重新创建"
    rm -rf venv
fi

python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ 创建虚拟环境失败"
    exit 1
fi
echo "✅ 虚拟环境创建成功"

# 检查Homebrew
echo "📋 检查Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "⚠️  警告: 未找到Homebrew，将尝试安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew 已安装"
fi

# 安装Pandoc
echo "📋 检查Pandoc..."
if ! command -v pandoc &> /dev/null; then
    echo "📦 安装Pandoc..."
    brew install pandoc
else
    echo "✅ Pandoc 已安装"
fi

# 激活虚拟环境并安装Python依赖
echo "📦 安装Python依赖包..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖包安装成功"
else
    echo "❌ 依赖包安装失败"
    exit 1
fi

# 创建启动脚本
echo "📝 创建启动脚本..."
cat > run_docuflow.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF

chmod +x run_docuflow.sh

# 运行测试
echo "📋 运行功能测试..."
source venv/bin/activate
python test_app.py

if [ $? -eq 0 ]; then
    echo "✅ 功能测试通过"
else
    echo "⚠️  功能测试失败，但安装已完成"
fi

echo ""
echo "🎉 安装完成！"
echo "================================="
echo "运行方式:"
echo "1. 双击启动脚本: ./run_docuflow.sh"
echo "2. 命令行方式: source venv/bin/activate && python main.py"
echo ""
echo "如果遇到问题，请查看 README.md 获取更多帮助"