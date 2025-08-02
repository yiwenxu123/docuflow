#!/bin/bash
# DocuFlow 项目清理脚本
# 用于清理冗余文件和优化项目结构

echo "🧹 开始清理DocuFlow项目..."

# 删除意外创建的版本文件
echo "📦 删除意外创建的版本文件..."
rm -f =0.7.0 =0.8.11 =3.0.0 =4.11.0 =4.9.0 2>/dev/null

# 删除冗余文档
echo "📄 删除冗余文档..."
rm -f README_Enhanced.md 2>/dev/null
rm -f GUI问题解决方案.md 2>/dev/null
rm -f Tkinter_GUI使用说明.md 2>/dev/null
rm -f 文件转换问题解决方案.md 2>/dev/null
rm -f 输出位置问题完整解决方案.md 2>/dev/null

# 删除冗余启动脚本
echo "🚀 删除冗余启动脚本..."
rm -f run_docuflow.sh 2>/dev/null
rm -f start.sh 2>/dev/null

# 清理临时目录
echo "🗂️ 清理临时目录..."
rm -rf temp/ 2>/dev/null
if [ -d "input" ] && [ -z "$(ls -A input 2>/dev/null)" ]; then
    rm -rf input/ 2>/dev/null
fi

# 清理Python缓存
echo "🐍 清理Python缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

# 清理macOS系统文件
echo "🍎 清理macOS系统文件..."
find . -name ".DS_Store" -delete 2>/dev/null

# 清理日志文件
echo "📝 清理旧日志文件..."
find . -name "*.log" -mtime +7 -delete 2>/dev/null

echo "✅ 项目清理完成！"
echo ""
echo "📊 清理统计："
echo "   - 删除了冗余文档和启动脚本"
echo "   - 清理了Python缓存文件"
echo "   - 清理了系统临时文件"
echo ""
echo "🚀 建议运行以下命令验证功能："
echo "   ./docuflow gui      # 启动GUI版本"
echo "   ./docuflow web      # 启动Web版本"
echo "   ./docuflow status   # 查看系统状态"
echo "   ./docuflow test     # 运行功能测试"
echo ""
echo "📚 查看使用指南："
echo "   cat 新手使用指南.md"
echo "   cat README.md"