#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 转 Markdown 功能演示脚本

此脚本展示 DocuFlow 新增的 Excel 转 Markdown 功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_excel_to_markdown():
    """演示 Excel 转 Markdown 功能"""
    print("🎯 DocuFlow Excel 转 Markdown 功能演示")
    print("=" * 60)
    
    # 检查演示文件是否存在
    demo_file = project_root / "demo_data.xlsx"
    if not demo_file.exists():
        print("📁 演示文件不存在，正在创建...")
        try:
            from create_demo_excel import create_demo_excel
            create_demo_excel()
        except Exception as e:
            print(f"❌ 创建演示文件失败: {e}")
            return False
    
    print(f"📊 使用演示文件: {demo_file}")
    
    try:
        # 导入转换器
        from converter.document_converter import DocumentConverter
        
        # 初始化转换器
        converter = DocumentConverter()
        
        # 检查支持情况
        xlsx_support = converter.can_convert('.xlsx', '.md')
        print(f"✅ Excel 转 Markdown 支持: {'是' if xlsx_support else '否'}")
        
        if not xlsx_support:
            print("❌ 不支持 Excel 转 Markdown")
            return False
        
        # 执行转换
        print("\n🔄 正在转换 Excel 文件...")
        output_file = converter.convert_file(
            file_path=str(demo_file),
            output_format=".md"
        )
        
        print(f"✅ 转换完成！输出文件: {output_file}")
        
        # 读取并展示结果
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📄 转换结果预览:")
        print("=" * 50)
        
        # 显示前 20 行
        lines = content.split('\n')
        preview_lines = lines[:20]
        for i, line in enumerate(preview_lines, 1):
            print(f"{i:2d}: {line}")
        
        if len(lines) > 20:
            print(f"... (还有 {len(lines) - 20} 行，完整内容请查看输出文件)")
        
        print("=" * 50)
        
        # 统计信息
        print(f"\n📈 转换统计:")
        print(f"   - 总行数: {len(lines)}")
        print(f"   - 字符数: {len(content)}")
        print(f"   - 工作表数: {content.count('## 工作表')}")
        print(f"   - 表格行数: {content.count('|')}")
        
        # 文件信息
        output_path = Path(output_file)
        file_size = output_path.stat().st_size
        print(f"   - 文件大小: {file_size} 字节")
        
        return True
        
    except Exception as e:
        print(f"❌ 转换失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def show_usage_examples():
    """显示使用示例"""
    print("\n💡 使用方法示例:")
    print("-" * 40)
    
    print("\n1️⃣ GUI 界面:")
    print("   ./quick_start.sh gui")
    print("   选择 Excel 文件 → 选择 Markdown 格式 → 开始转换")
    
    print("\n2️⃣ 命令行:")
    print("   ./docuflow convert demo_data.xlsx --format md")
    print("   ./docuflow convert *.xlsx --format md --output ./output/")
    
    print("\n3️⃣ Web 界面:")
    print("   ./quick_start.sh web")
    print("   浏览器打开 http://localhost:5000")
    
    print("\n4️⃣ Python 代码:")
    print("   from converter.document_converter import DocumentConverter")
    print("   converter = DocumentConverter()")
    print("   result = converter.convert_file('file.xlsx', '.md')")

def show_supported_features():
    """显示支持的功能特性"""
    print("\n🌟 功能特性:")
    print("-" * 40)
    
    features = [
        "✅ 支持 .xlsx 和 .xls 格式",
        "✅ 多工作表自动处理",
        "✅ 标准 Markdown 表格格式",
        "✅ 智能空数据过滤",
        "✅ 数据统计信息",
        "✅ 双引擎处理保障",
        "✅ 完整的错误处理",
        "✅ 支持大文件处理",
        "✅ 保持原始表格结构",
        "✅ 自动字符转义"
    ]
    
    for feature in features:
        print(f"   {feature}")

def main():
    """主函数"""
    # 演示转换功能
    success = demo_excel_to_markdown()
    
    # 显示使用示例
    show_usage_examples()
    
    # 显示功能特性
    show_supported_features()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Excel 转 Markdown 功能演示完成！")
        print("\n📚 更多信息请查看:")
        print("   - 《新手使用指南.md》")
        print("   - 《Excel转Markdown功能说明.md》")
        print("\n🚀 立即开始使用:")
        print("   ./quick_start.sh gui")
    else:
        print("❌ 演示过程中出现问题，请检查错误信息。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)