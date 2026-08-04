#!/bin/bash

# DocuFlow 极速启动器 v4.0
# 快速启动 + 智能缓存 + 美观界面

# 设置终端标题
echo -ne "\033]0;DocuFlow 启动中...\007"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 快速检查缓存文件
CACHE_FILE="$HOME/.docuflow_cache"
INSTALL_COMPLETE_FILE="$SCRIPT_DIR/.install_complete"

# 快速启动函数
fast_start() {
    clear
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "║                    ${GREEN}DocuFlow 文档转换器${NC}                    ║"
    echo -e "║                     ${PURPLE}极速启动 v4.0${NC}                         ║"
    echo -e "║${YELLOW}    拖拽文件直接转换 · 批量处理 · 多格式支持${NC}                ║"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查安装状态
check_installation() {
    if [ -f "$INSTALL_COMPLETE_FILE" ] && [ -d "venv" ]; then
        # 快速验证关键依赖
        if source venv/bin/activate && python3 -c "import PySide6" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# 快速安装检查
quick_install_check() {
    # 检查Homebrew
    if ! command -v brew >/dev/null 2>&1; then
        echo -e "${YELLOW}[安装]${NC} 正在安装Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" >/dev/null 2>&1
        
        if [ -f /opt/homebrew/bin/brew ]; then
            export PATH="/opt/homebrew/bin:$PATH"
        elif [ -f /usr/local/bin/brew ]; then
            export PATH="/usr/local/bin:$PATH"
        fi
    fi
    
    # 检查pandoc
    if ! command -v pandoc >/dev/null 2>&1; then
        echo -e "${YELLOW}[安装]${NC} 正在安装pandoc..."
        brew install pandoc >/dev/null 2>&1
    fi
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}[安装]${NC} 正在配置Python环境..."
        python3 -m venv venv >/dev/null 2>&1
    fi
    
    # 检查依赖
    source venv/bin/activate
    if ! python3 -c "import PySide6" 2>/dev/null; then
        echo -e "${YELLOW}[安装]${NC} 正在安装Python依赖..."
        pip install -r requirements.txt >/dev/null 2>&1 || pip install PySide6 python-docx reportlab PyPDF2 openpyxl >/dev/null 2>&1
    fi
    
    # 标记安装完成
    touch "$INSTALL_COMPLETE_FILE"
    echo -e "${GREEN}[完成]${NC} 环境配置完成！"
}

# 主启动逻辑
main() {
    fast_start
    
    # 检查是否需要安装
    if check_installation; then
        echo -e "${GREEN}[启动]${NC} 正在启动DocuFlow..."
    else
        echo -e "${YELLOW}[首次]${NC} 检测到首次使用，正在配置环境..."
        quick_install_check
    fi
    
    # 启动应用
    source venv/bin/activate
    
    # 显示启动动画
    echo -ne "${CYAN}[启动]${NC} 加载中"
    for i in {1..3}; do
        echo -ne "."
        sleep 0.5
    done
    echo ""
    
    # 启动主应用
    python3 main_pyside.py
    
    echo -e "${GREEN}[完成]${NC} DocuFlow已关闭"
    echo ""
    echo -e "${CYAN}💡 提示：${NC}下次启动将更快！"
    sleep 2
}

# 执行主程序
main "$@"