#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.document_converter import DocumentConverter
from utils.config_manager import ConfigManager

def test_can_convert():
    """测试can_convert方法"""
    print("=== 测试can_convert方法 ===")
    
    # 初始化转换器
    config_manager = ConfigManager()
    converter = DocumentConverter(config_manager)
    
    # 测试PDF转换支持
    test_cases = [
        ('.pdf', '.md'),
        ('.pdf', '.html'),
        ('.pdf', '.txt'),
        ('.docx', '.md'),
        ('.xlsx', '.md'),
    ]
    
    print("转换支持测试:")
    for source, target in test_cases:
        result = converter.can_convert(source, target)
        print(f"  {source} -> {target}: {result}")
    
    # 查看支持的转换映射
    print(f"\n支持的转换映射:")
    conversion_map = converter.conversion_map
    for source, targets in conversion_map.items():
        print(f"  {source}: {targets}")
    
    # 测试配置
    print(f"\n配置信息:")
    print(f"  SUPPORTED_CONVERSIONS: {config_manager.SUPPORTED_CONVERSIONS}")

if __name__ == "__main__":
    test_can_convert()