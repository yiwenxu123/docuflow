#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强的过滤功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from converter.document_converter import DocumentConverter

def test_html_to_markdown():
    """测试HTML到Markdown转换，验证GitHub Gist页面结构去除"""
    print("测试HTML到Markdown转换...")
    
    # 确保测试目录存在
    test_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    os.makedirs(test_dir, exist_ok=True)
    
    # 测试文件路径
    input_file = "/Users/yiwenxu123/Downloads/llm-wiki (2026_4_7 14：47：37).html"
    output_file = os.path.join(test_dir, "test_output.md")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件不存在: {input_file}")
        return False
    
    try:
        # 创建转换器实例
        converter = DocumentConverter()
        
        # 执行转换，启用过滤功能
        result = converter.convert_file(
            file_path=input_file,
            output_format=".md",
            output_dir=test_dir,
            keep_original_name=False,
            filter_images=True,
            clean_content=True
        )
        
        print(f"转换成功: {result}")
        
        # 读取转换结果
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查结果
        print(f"转换后文件大小: {len(content)} 字符")
        
        # 验证文件路径引用是否被去除
        file_path_references = "/Users/yiwenxu123/trae/文档转换/llm-wiki_filtered.md#L1-224"
        if file_path_references in content:
            print("错误：文件路径引用未被去除")
        else:
            print("✓ 文件路径引用已被去除")
        
        # 验证GitHub Gist页面结构是否被去除
        # 检查是否包含典型的GitHub Gist页面结构元素
        gist_elements = [
            "gist.github.com",
            "Created by",
            "Star",
            "Fork",
            "Share"
        ]
        
        for element in gist_elements:
            if element in content:
                print(f"错误：GitHub Gist页面结构元素 '{element}' 未被去除")
            else:
                print(f"✓ GitHub Gist页面结构元素 '{element}' 已被去除")
        
        # 验证内容是否保留
        if len(content.strip()) > 0:
            print("✓ 内容已保留")
        else:
            print("错误：内容未保留")
        
        # 打印前1000字符作为预览
        print("\n转换结果预览：")
        print(content[:1000] + "..." if len(content) > 1000 else content)
        
        return True
        
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def test_markdown_cleanup():
    """测试Markdown文件清理，验证文件路径引用去除"""
    print("\n测试Markdown文件清理...")
    
    # 确保测试目录存在
    test_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建一个包含文件路径引用的测试Markdown文件
    test_content = """
# 测试文档

这是一个测试文档，包含文件路径引用：/Users/yiwenxu123/trae/文档转换/llm-wiki_filtered.md#L1-224

还有另一个引用：/path/to/another/file.md#L10-20

## 章节

这是章节内容。
"""
    
    try:
        # 创建转换器实例
        converter = DocumentConverter()
        
        # 直接使用_clean_content方法测试
        cleaned_content = converter._clean_content(
            content=test_content,
            content_type='markdown',
            filter_images=True,
            clean_content=True
        )
        
        print("清理成功")
        
        # 检查文件路径引用是否被去除
        if "/Users/yiwenxu123/trae/文档转换/llm-wiki_filtered.md#L1-224" in cleaned_content:
            print("错误：文件路径引用未被去除")
        else:
            print("✓ 文件路径引用已被去除")
        
        if "/path/to/another/file.md#L10-20" in cleaned_content:
            print("错误：文件路径引用未被去除")
        else:
            print("✓ 文件路径引用已被去除")
        
        # 验证内容是否保留
        if "测试文档" in cleaned_content and "章节内容" in cleaned_content:
            print("✓ 内容已保留")
        else:
            print("错误：内容未保留")
        
        print("\n清理结果：")
        print(cleaned_content)
        
        return True
        
    except Exception as e:
        print(f"清理失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试增强的过滤功能...\n")
    
    # 运行测试
    html_test_result = test_html_to_markdown()
    markdown_test_result = test_markdown_cleanup()
    
    print("\n测试完成！")
    print(f"HTML转换测试: {'通过' if html_test_result else '失败'}")
    print(f"Markdown清理测试: {'通过' if markdown_test_result else '失败'}")
