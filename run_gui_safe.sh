#!/bin/bash

# DocuFlow GUI 安全启动脚本
# 解决 macOS 上 Tkinter GUI 显示问题

echo "=== DocuFlow GUI 启动脚本 ==="
echo "检查运行环境..."

# 检查是否在图形环境中
if [ -z "$DISPLAY" ] && [ "$(uname)" = "Darwin" ]; then
    echo "检测到 macOS 环境，设置图形显示..."
    # 在 macOS 上，通常不需要设置 DISPLAY
    export DISPLAY=":0"
fi

# 检查 Python 和 Tkinter
echo "检查 Python 环境..."
/usr/bin/python3 -c "import tkinter; print('Tkinter 可用')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: Tkinter 不可用"
    echo "请确保使用支持 Tkinter 的 Python 版本"
    exit 1
fi

# 设置环境变量
export TK_SILENCE_DEPRECATION=1
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "启动 DocuFlow GUI..."
echo "如果窗口没有显示，请检查:"
echo "1. 是否在图形桌面环境中运行"
echo "2. 是否有权限访问显示器"
echo "3. 防火墙或安全软件是否阻止了应用"
echo ""

# 尝试启动 GUI
if [ -f "main_tkinter.py" ]; then
    echo "使用系统 Python 启动..."
    /usr/bin/python3 main_tkinter.py
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "GUI 正常退出"
    else
        echo "GUI 退出，退出码: $exit_code"
        echo "如果遇到问题，请尝试:"
        echo "1. 在终端中直接运行: /usr/bin/python3 main_tkinter.py"
        echo "2. 检查是否有错误信息"
        echo "3. 尝试重启终端或系统"
    fi
else
    echo "错误: 找不到 main_tkinter.py 文件"
    echo "请确保在正确的目录中运行此脚本"
    exit 1
fi

echo "=== 脚本执行完成 ==="