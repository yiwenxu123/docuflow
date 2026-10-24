#!/bin/bash
# DocuFlow 启动器（不做静默安装）
cd "$(dirname "$0")" || exit 1

pause_and_exit() {
    echo ""
    read -n 1 -s -r -p "按任意键退出..."
    echo ""
    exit 1
}

if ! command -v pandoc >/dev/null 2>&1; then
    echo "未找到 pandoc。请先安装："
    echo "  brew install pandoc"
    pause_and_exit
fi

if [ ! -d "venv" ]; then
    echo "未找到 venv。请先在项目目录执行："
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    pause_and_exit
fi

source venv/bin/activate
python3 main_pyside.py
