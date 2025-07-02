#!/bin/bash
echo "启动 DocuFlow 文档转换器..."
cd "$(dirname "$0")"
source venv/bin/activate

# 设置Qt环境变量以解决macOS上的Qt平台插件问题 (PySide6)
PYSIDE6_PATH="$(pwd)/venv/lib/python3.13/site-packages/PySide6"
PLUGIN_PATH="$PYSIDE6_PATH/Qt/plugins"
LIB_PATH="$PYSIDE6_PATH/Qt/lib"

# 导出环境变量
export QT_PLUGIN_PATH="$PLUGIN_PATH"
export DYLD_LIBRARY_PATH="$LIB_PATH:$DYLD_LIBRARY_PATH"
export QT_QPA_PLATFORM_PLUGIN_PATH="$PLUGIN_PATH/platforms"
export QT_QPA_PLATFORM="cocoa"
export QT_DEBUG_PLUGINS=1

echo "正在启动GUI界面..."
echo "Qt插件路径: $QT_PLUGIN_PATH"
echo "库路径: $DYLD_LIBRARY_PATH"
python main.py
