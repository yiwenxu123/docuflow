#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 简单测试脚本
用于验证应用的基本功能
"""

import os
import sys
import tempfile
import subprocess
from utils.file_utils import is_supported_file, get_supported_formats, can_convert_to
from converter.document_converter import DocumentConverter

def test_dependencies():
    """测试依赖是否正确安装"""
    print("🔍 测试依赖...")
    
    # 测试Pandoc
    try:
        result = subprocess.run(["pandoc", "--version"], 
                               capture_output=True, text=True, check=False)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Pandoc: {version}")
        else:
            print("❌ Pandoc: 未安装或无法运行")
            return False
    except FileNotFoundError:
        print("❌ Pandoc: 未找到")
        return False
    
    # 测试PyQt5
    try:
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5: 已安装")
    except ImportError:
        print("❌ PyQt5: 未安装")
        return False
    
    return True

def test_file_utils():
    """测试文件工具函数"""
    print("\n🔍 测试文件工具...")
    
    # 测试支持的格式
    formats = get_supported_formats()
    print(f"✅ 支持的格式: {list(formats.keys())}")
    
    # 测试文件格式检查
    test_files = [
        "test.docx",
        "test.md", 
        "test.pdf",
        "test.txt",  # 不支持的格式
        "test.html"
    ]
    
    for file in test_files:
        supported = is_supported_file(file) if os.path.exists(file) else "文件不存在，仅测试扩展名检查"
        ext = os.path.splitext(file)[1]
        format_supported = ext.lower() in formats
        print(f"  {file}: 格式支持={format_supported}")
    
    # 测试转换支持
    print("\n转换支持测试:")
    test_conversions = [
        (".docx", ".pdf"),
        (".md", ".docx"),
        (".pdf", ".md"),
        (".txt", ".pdf")  # 不支持的转换
    ]
    
    for src, dst in test_conversions:
        can_convert = can_convert_to(src, dst)
        print(f"  {src} → {dst}: {can_convert}")
    
    return True

def test_converter():
    """测试转换器"""
    print("\n🔍 测试转换器...")
    
    try:
        converter = DocumentConverter()
        print("✅ 转换器初始化成功")
        
        # 测试转换支持检查
        can_convert = converter.can_convert(".md", ".pdf")
        print(f"✅ 转换支持检查: .md → .pdf = {can_convert}")
        
        return True
        
    except Exception as e:
        print(f"❌ 转换器测试失败: {e}")
        return False

def create_test_markdown():
    """创建测试用的Markdown文件"""
    test_content = """# 测试文档

这是一个测试用的Markdown文档。

## 功能特性

- 支持多种格式转换
- 简单易用的界面
- 批量处理功能

## 代码示例

```python
print("Hello, DocuFlow!")
```

**粗体文本** 和 *斜体文本*

> 这是一个引用块

1. 有序列表项1
2. 有序列表项2
3. 有序列表项3
"""
    
    test_file = os.path.join(os.getcwd(), "test_document.md")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    return test_file

def test_actual_conversion():
    """测试实际的文件转换"""
    print("\n🔍 测试实际转换...")
    
    # 创建测试文件
    test_file = create_test_markdown()
    print(f"✅ 创建测试文件: {test_file}")
    
    try:
        converter = DocumentConverter()
        
        # 测试转换为HTML
        output_file = converter.convert_file(test_file, ".html")
        if output_file and os.path.exists(output_file):
            print(f"✅ 转换成功: {output_file}")
            
            # 清理测试文件
            os.remove(test_file)
            os.remove(output_file)
            print("✅ 清理测试文件")
            
            return True
        else:
            print("❌ 转换失败")
            return False
            
    except Exception as e:
        print(f"❌ 转换测试失败: {e}")
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

def main():
    """主测试函数"""
    print("🚀 DocuFlow 功能测试")
    print("=" * 30)
    
    tests = [
        ("依赖检查", test_dependencies),
        ("文件工具", test_file_utils),
        ("转换器", test_converter),
        ("实际转换", test_actual_conversion)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 30)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用已准备就绪。")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)