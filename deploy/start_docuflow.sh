#!/bin/bash
# DocuFlow 快速启动脚本

cd "$(dirname "$0")"

echo "🚀 启动 DocuFlow..."

# 检查Python环境
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 检查依赖
echo "🔍 检查依赖..."
$PYTHON -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || {
    echo "❌ Python版本过低，需要3.8+"
    exit 1
}

# 安装依赖（如果需要）
if [ ! -f ".deps_installed" ]; then
    echo "📦 首次运行，安装依赖..."
    $PYTHON -m pip install -r requirements.txt --user --quiet
    touch .deps_installed
    echo "✅ 依赖安装完成"
fi

# 启动应用
case "${1:-web}" in
    "gui")
        echo "🖥️  启动GUI版本..."
        $PYTHON main_pyside.py
        ;;
    "web")
        echo "🌐 启动Web版本..."
        echo "📱 访问地址: http://localhost:5003"
        $PYTHON main_web.py
        ;;
    "cli")
        echo "💻 启动命令行版本..."
        shift
        $PYTHON main_cli.py "$@"
        ;;
    *)
        echo "用法: $0 [gui|web|cli] [参数...]"
        echo "  gui - 图形界面"
        echo "  web - 网页界面"
        echo "  cli - 命令行"
        ;;
esac
