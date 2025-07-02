#!/bin/bash

# DocuFlow Tkinter GUI启动脚本
# 使用系统Python运行tkinter版本的GUI

echo "启动 DocuFlow 文档转换器 (Tkinter版)..."

# 使用系统Python而不是虚拟环境的Python
SYSTEM_PYTHON="/usr/bin/python3"

# 检查系统Python是否存在
if [ ! -f "$SYSTEM_PYTHON" ]; then
    echo "错误: 系统Python未找到: $SYSTEM_PYTHON"
    exit 1
fi

# 检查tkinter是否可用
$SYSTEM_PYTHON -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: 系统Python中未找到tkinter模块"
    echo "请安装tkinter: brew install python-tk@3.9"
    exit 1
fi

# 设置PYTHONPATH以确保能找到项目模块
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 抑制Tk弃用警告
export TK_SILENCE_DEPRECATION=1

# 运行tkinter版本的GUI
echo "正在启动Tkinter GUI界面..."
$SYSTEM_PYTHON main_tkinter.py

# 检查退出状态
if [ $? -ne 0 ]; then
    echo "GUI启动失败，请查看上方错误信息"
    exit 1
fi