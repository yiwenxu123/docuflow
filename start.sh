#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 虚拟环境目录
VENV_DIR="venv"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "创建虚拟环境失败，请确保已安装 python3 和 venv。" >&2
        exit 1
    fi
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 强制重新安装 PySide6 以解决潜在的插件问题
echo -e "${YELLOW}正在重新安装 PySide6 以确保插件完整...${NC}"
pip uninstall -y PySide6
pip install PySide6

# 检查并安装其他依赖
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}正在检查并安装依赖...${NC}"
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依赖安装失败。" >&2
        deactivate
        exit 1
    fi
else
    echo -e "${YELLOW}未找到 requirements.txt 文件，跳过依赖安装。${NC}"
fi

# 设置 Qt 相关环境变量
echo -e "${YELLOW}设置Qt环境变量...${NC}"
export QT_QPA_PLATFORM_PLUGIN_PATH=$(python -c "import PySide6; import os; print(os.path.join(PySide6.__path__[0], 'Qt', 'plugins'))" 2>/dev/null || echo "")
export QT_PLUGIN_PATH=$QT_QPA_PLATFORM_PLUGIN_PATH
export QT_QPA_PLATFORM=cocoa

# 检查Qt插件是否存在
if [ -n "$QT_PLUGIN_PATH" ] && [ -d "$QT_PLUGIN_PATH" ]; then
    echo -e "${GREEN}Qt插件路径: $QT_PLUGIN_PATH${NC}"
else
    echo -e "${YELLOW}警告: Qt插件路径未找到，可能会影响GUI显示${NC}"
fi

# 启动主程序
MAIN_SCRIPT="main_pyside.py"
if [ -f "$MAIN_SCRIPT" ]; then
    echo -e "${GREEN}正在启动 DocuFlow...${NC}"
    python "$MAIN_SCRIPT"
else
    echo "主程序脚本 $MAIN_SCRIPT 未找到。" >&2
fi

# 停用虚拟环境
deactivate