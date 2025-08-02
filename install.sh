#!/bin/bash

# DocuFlow 安装脚本
# 适用于 macOS

echo "🚀 DocuFlow 文档转换器安装脚本"
echo "================================="

# 检查Python版本
echo "📋 检查Python版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ -z "$python_version" ]]; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.7或更高版本"
    exit 1
fi
echo "✅ Python版本: $python_version"

# 检查pip
echo "📋 检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到pip3"
    exit 1
fi
echo "✅ pip3 已安装"

# 检查Homebrew
echo "📋 检查Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "⚠️  警告: 未找到Homebrew，将尝试安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew 已安装"
fi

# 安装Pandoc
echo "📋 检查Pandoc..."
if ! command -v pandoc &> /dev/null; then
    echo "📦 安装Pandoc..."
    brew install pandoc
else
    echo "✅ Pandoc 已安装"
fi

# 安装Python依赖（全局安装）
echo "📦 安装Python依赖包..."
pip3 install --user PyPDF2 pdfplumber python-docx openpyxl pandas PySide6 PyYAML pydantic

if [ $? -eq 0 ]; then
    echo "✅ 依赖包安装成功"
else
    echo "❌ 依赖包安装失败"
    exit 1
fi

# 运行功能测试
echo "📋 运行功能测试..."
python3 test_all_conversions.py

if [ $? -eq 0 ]; then
    echo "✅ 功能测试通过"
else
    echo "⚠️  功能测试失败，但安装已完成"
fi

# 重新打包应用
echo "📦 重新打包应用..."
if [ -f "build_app.py" ]; then
    echo "🔨 清理旧版本..."
    rm -rf dist build
    
    echo "🔨 重新打包应用..."
    python3 build_app.py
    
    if [ -d "dist/DocuFlow.app" ]; then
        echo "🔧 修复应用权限和签名..."
        # 清理扩展属性
        xattr -cr dist/DocuFlow.app
        
        # 修复权限
        chmod -R 755 dist/DocuFlow.app
        
        # 复制到用户应用目录
        echo "📱 安装应用到启动台..."
        cp -R dist/DocuFlow.app ~/Applications/
        
        # 重置启动台
        defaults write com.apple.dock ResetLaunchPad -bool true
        
        echo "✅ 应用打包和安装完成"
    else
        echo "⚠️  应用打包失败，但核心功能可用"
    fi
else
    echo "⚠️  未找到build_app.py，跳过应用打包"
fi

echo ""
echo "🎉 安装完成！"
echo "================================="
echo "使用方法:"
echo "1. 启动台应用: 在启动台中找到DocuFlow图标"
echo "2. 命令行GUI: python3 main.py"
echo "3. 命令行转换: python3 -c \"from converter.document_converter import DocumentConverter; dc = DocumentConverter(); dc.convert_file('input.pdf', '.md')\""
echo "4. 测试功能: python3 test_all_conversions.py"
echo ""
echo "支持的转换:"
echo "• PDF → Markdown ✅"
echo "• Excel → Markdown ✅"
echo "• Word → Markdown ✅"
echo ""
echo "如果遇到问题，请查看 问题解决方案.md 获取更多帮助"