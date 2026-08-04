#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MarkItDown集成的导入
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from converter.document_converter import DocumentConverter
    print("✓ 成功导入DocumentConverter")
    
    # 测试创建DocumentConverter实例
    converter = DocumentConverter()
    print("✓ 成功创建DocumentConverter实例")
    
    # 测试MarkItDown集成
    print(f"✓ MarkItDown可用: {converter.markitdown_integration.is_available()}")
    
    print("所有测试通过！")
    
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
