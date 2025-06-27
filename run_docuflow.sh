#!/bin/bash
echo "启动 DocuFlow 文档转换器..."
cd "$(dirname "$0")"
source venv/bin/activate

# 设置Qt插件路径以解决macOS上的Qt平台插件问题
export QT_PLUGIN_PATH="$VIRTUAL_ENV/lib/python3.13/site-packages/PyQt5/Qt5/plugins"

echo "正在启动GUI界面..."
python main.py
