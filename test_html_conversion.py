#!/usr/bin/env python3
"""
HTML转换测试脚本
"""

import sys
import os
import traceback
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from converter.document_converter import DocumentConverter

def test_html_conversions():
    """测试HTML转换功能"""
    converter = DocumentConverter()
    
    # 确保测试文件存在
    test_files = {
        'test_diagnostic.xlsx': 'Excel文件',
        'test_diagnostic.md': 'Markdown文件',
        'test_diagnostic.docx': 'Word文件'
    }
    
    for file_name, file_type in test_files.items():
        if not Path(file_name).exists():
            print(f"❌ {file_type} {file_name} 不存在")
            continue
        print(f"✅ {file_type} {file_name} 存在")
    
    print("\n" + "="*60)
    print("开始HTML转换测试")
    print("="*60)
    
    # 测试Excel到HTML转换
    print("\n1. 测试Excel到HTML转换...")
    try:
        output_path = str(Path.cwd() / "test_excel_to_html.html")
        print(f"   输入文件: test_diagnostic.xlsx")
        print(f"   输出路径: {output_path}")
        
        result = converter.convert_file('test_diagnostic.xlsx', output_path)
        print(f"   转换结果: {result}")
        
        if result and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"   ✅ Excel到HTML转换成功 ({file_size} bytes)")
        else:
            print(f"   ❌ Excel到HTML转换失败 - 输出文件不存在")
            
    except Exception as e:
        print(f"   ❌ Excel到HTML转换异常: {e}")
        print(f"   异常类型: {type(e).__name__}")
        traceback.print_exc()
    
    # 测试Markdown到HTML转换
    print("\n2. 测试Markdown到HTML转换...")
    try:
        output_path = str(Path.cwd() / "test_md_to_html.html")
        print(f"   输入文件: test_diagnostic.md")
        print(f"   输出路径: {output_path}")
        
        result = converter.convert_file('test_diagnostic.md', output_path)
        print(f"   转换结果: {result}")
        
        if result and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"   ✅ Markdown到HTML转换成功 ({file_size} bytes)")
        else:
            print(f"   ❌ Markdown到HTML转换失败 - 输出文件不存在")
            
    except Exception as e:
        print(f"   ❌ Markdown到HTML转换异常: {e}")
        print(f"   异常类型: {type(e).__name__}")
        traceback.print_exc()
    
    # 测试Word到HTML转换
    print("\n3. 测试Word到HTML转换...")
    try:
        output_path = str(Path.cwd() / "test_word_to_html.html")
        print(f"   输入文件: test_diagnostic.docx")
        print(f"   输出路径: {output_path}")
        
        result = converter.convert_file('test_diagnostic.docx', output_path)
        print(f"   转换结果: {result}")
        
        if result and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"   ✅ Word到HTML转换成功 ({file_size} bytes)")
        else:
            print(f"   ❌ Word到HTML转换失败 - 输出文件不存在")
            
    except Exception as e:
        print(f"   ❌ Word到HTML转换异常: {e}")
        print(f"   异常类型: {type(e).__name__}")
        traceback.print_exc()

if __name__ == "__main__":
    test_html_conversions()