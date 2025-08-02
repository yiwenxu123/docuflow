#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试转换问题的专用脚本
"""

import sys
import os
import traceback
from pathlib import Path
from converter.document_converter import DocumentConverter

def test_pdf_conversion():
    """测试PDF转换"""
    print("\n=== 测试PDF转换 ===")
    converter = DocumentConverter()
    
    # 查找项目中的PDF文件
    pdf_files = list(Path('.').glob('**/*.pdf'))
    if not pdf_files:
        print("❌ 未找到PDF文件进行测试")
        return False
    
    for pdf_file in pdf_files[:3]:  # 测试前3个PDF文件
        try:
            print(f"\n📄 测试文件: {pdf_file}")
            output_path = converter.convert_file(str(pdf_file), '.md')
            if output_path and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                print(f"✅ PDF转换成功: {output_path} ({file_size}字节)")
                
                # 显示转换内容的前几行
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:200]
                    print(f"📝 内容预览: {content}...")
            else:
                print(f"❌ PDF转换失败: 输出文件不存在")
                return False
        except Exception as e:
            print(f"❌ PDF转换异常: {e}")
            print(f"详细错误: {traceback.format_exc()}")
            return False
    
    return True

def test_excel_conversion():
    """测试Excel转换"""
    print("\n=== 测试Excel转换 ===")
    converter = DocumentConverter()
    
    # 查找项目中的Excel文件
    excel_files = list(Path('.').glob('**/*.xlsx')) + list(Path('.').glob('**/*.xls'))
    if not excel_files:
        print("❌ 未找到Excel文件进行测试")
        return False
    
    for excel_file in excel_files[:3]:  # 测试前3个Excel文件
        try:
            print(f"\n📊 测试文件: {excel_file}")
            output_path = converter.convert_file(str(excel_file), '.md')
            if output_path and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                print(f"✅ Excel转换成功: {output_path} ({file_size}字节)")
                
                # 显示转换内容的前几行
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:200]
                    print(f"📝 内容预览: {content}...")
            else:
                print(f"❌ Excel转换失败: 输出文件不存在")
                return False
        except Exception as e:
            print(f"❌ Excel转换异常: {e}")
            print(f"详细错误: {traceback.format_exc()}")
            return False
    
    return True

def check_dependencies():
    """检查依赖库"""
    print("\n=== 检查依赖库 ===")
    dependencies = {
        'PyPDF2': 'PyPDF2',
        'pdfplumber': 'pdfplumber', 
        'openpyxl': 'openpyxl',
        'pandas': 'pandas',
        'python-docx': 'docx'
    }
    
    # 特殊处理pandas导入
    pandas_aliases = {'pandas': ['pandas', 'pd']}
    
    missing = []
    for name, module in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name}: 已安装")
        except ImportError:
            print(f"❌ {name}: 未安装")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️ 缺失依赖: {', '.join(missing)}")
        print(f"安装命令: pip3 install {' '.join(missing)}")
        return False
    
    return True

def main():
    print("🔍 DocuFlow 转换问题调试工具")
    print("=" * 50)
    
    # 检查依赖
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n❌ 依赖检查失败，请先安装缺失的依赖")
        return
    
    # 测试转换功能
    pdf_ok = test_pdf_conversion()
    excel_ok = test_excel_conversion()
    
    print("\n" + "=" * 50)
    print("📊 调试结果汇总:")
    print(f"  PDF转换: {'✅ 正常' if pdf_ok else '❌ 失败'}")
    print(f"  Excel转换: {'✅ 正常' if excel_ok else '❌ 失败'}")
    
    if not pdf_ok or not excel_ok:
        print("\n💡 建议:")
        print("  1. 检查文件是否损坏或加密")
        print("  2. 尝试使用不同的文件进行测试")
        print("  3. 重新安装依赖: pip3 install --upgrade PyPDF2 pdfplumber openpyxl pandas")
        print("  4. 查看详细错误日志")

if __name__ == '__main__':
    main()