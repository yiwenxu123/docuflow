#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的 Excel 转 Markdown 测试
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_excel_support():
    """测试 Excel 转换支持"""
    try:
        from converter.document_converter import DocumentConverter
        from config import config
        
        print("🎯 测试 Excel 转 Markdown 支持")
        print("=" * 40)
        
        # 初始化转换器
        converter = DocumentConverter()
        
        # 测试格式支持
        xlsx_support = converter.can_convert('.xlsx', '.md')
        xls_support = converter.can_convert('.xls', '.md')
        
        print(f"📊 .xlsx -> .md 支持: {'✅ 是' if xlsx_support else '❌ 否'}")
        print(f"📊 .xls -> .md 支持: {'✅ 是' if xls_support else '❌ 否'}")
        
        # 检查 Excel 处理库
        try:
            from converter.document_converter import EXCEL_SUPPORT
            print(f"📚 Excel 处理库状态: {'✅ 可用' if EXCEL_SUPPORT else '❌ 不可用'}")
        except ImportError:
            print("📚 Excel 处理库状态: ❌ 导入失败")
        
        # 检查配置
        try:
            from config import FileSettings
            settings = FileSettings()
            xlsx_formats = settings.conversion_matrix.get('.xlsx', [])
            xls_formats = settings.conversion_matrix.get('.xls', [])
            
            print(f"⚙️  .xlsx 支持的输出格式: {xlsx_formats}")
            print(f"⚙️  .xls 支持的输出格式: {xls_formats}")
            
            md_in_xlsx = '.md' in xlsx_formats
            md_in_xls = '.md' in xls_formats
            
            print(f"✨ 配置检查: .xlsx -> .md {'✅ 已配置' if md_in_xlsx else '❌ 未配置'}")
            print(f"✨ 配置检查: .xls -> .md {'✅ 已配置' if md_in_xls else '❌ 未配置'}")
            
        except Exception as e:
            print(f"⚠️  配置检查失败: {e}")
        
        print("\n" + "=" * 40)
        
        if xlsx_support and xls_support:
            print("🎉 Excel 转 Markdown 功能已成功集成！")
            print("\n💡 使用方法:")
            print("   1. GUI: 选择 Excel 文件，输出格式选择 Markdown")
            print("   2. 命令行: ./docuflow convert file.xlsx --format md")
            print("   3. 快速启动: ./quick_start.sh gui")
            return True
        else:
            print("❌ Excel 转 Markdown 功能配置有问题")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_excel_support()
    sys.exit(0 if success else 1)