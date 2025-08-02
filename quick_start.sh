#!/bin/bash

# DocuFlow 快速启动脚本
# 解决每次启动都需要重新安装依赖的问题

echo "🚀 DocuFlow 快速启动器 v1.0"
echo "================================"

# 检查启动方式参数
START_MODE="${1:-gui}"

case $START_MODE in
    "app")
        echo "📱 启动打包应用版本..."
        if [ -f "dist/DocuFlow/DocuFlow" ]; then
            echo "✅ 找到应用包，直接启动！"
            ./dist/DocuFlow/DocuFlow
        else
            echo "❌ 应用包不存在，请先运行: python3 build_app.py"
            echo "💡 或者使用其他启动方式: ./quick_start.sh gui"
        fi
        ;;
    "gui")
        echo "🖥️  启动GUI版本..."
        # 检查虚拟环境
        if [ ! -d "venv" ]; then
            echo "📦 首次运行，创建虚拟环境..."
            python3 -m venv venv
            source venv/bin/activate
            echo "📥 安装依赖（使用清华镜像源）..."
            pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
            echo "✅ 环境创建完成！"
        else
            echo "✅ 虚拟环境已存在，直接启动！"
            source venv/bin/activate
        fi
        python main_pyside.py
        ;;
    "web")
        echo "🌐 启动Web版本..."
        if [ ! -d "venv" ]; then
            echo "📦 首次运行，创建虚拟环境..."
            python3 -m venv venv
            source venv/bin/activate
            pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
        else
            source venv/bin/activate
        fi
        echo "🌐 Web服务启动中..."
        echo "📍 访问地址: http://127.0.0.1:5000"
        python main_web.py
        ;;

    "help")
        echo "📖 使用方法:"
        echo "  ./quick_start.sh app     - 启动打包应用（最快，3-5秒）"
        echo "  ./quick_start.sh gui     - 启动GUI版本（默认）"
        echo "  ./quick_start.sh web     - 启动Web版本"
        echo "  ./quick_start.sh help    - 显示帮助"
        echo ""
        echo "🎯 推荐启动顺序:"
        echo "  1. 打包应用版本（app）- 最快启动"
        echo "  2. GUI版本（gui）- 本地图形界面"
        echo "  3. Web版本（web）- 浏览器访问"
        ;;
    *)
        echo "❌ 未知启动方式: $START_MODE"
        echo "💡 使用 ./quick_start.sh help 查看帮助"
        exit 1
        ;;
esac

echo ""
echo "🎉 感谢使用 DocuFlow！"