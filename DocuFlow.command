#!/bin/bash

# DocuFlow 桌面快捷启动脚本
# 双击即可启动，无需终端操作

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 启动应用包版本（最快）
if [ -f "dist/DocuFlow/DocuFlow" ]; then
    echo "🚀 启动 DocuFlow 应用包版本..."
    ./dist/DocuFlow/DocuFlow
else
    # 如果应用包不存在，使用快速启动脚本
    echo "📱 应用包不存在，使用GUI版本启动..."
    ./quick_start.sh gui
fi

# 保持窗口打开，显示结果
echo ""
echo "按任意键关闭窗口..."
read -n 1