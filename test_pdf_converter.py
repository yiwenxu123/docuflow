#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PDF转Markdown功能
"""

import os
import sys
from converter.document_converter import DocumentConverter

def test_pdf_to_markdown():
    """测试PDF转Markdown转换功能"""
    print("测试PDF转Markdown转换功能...")
    
    # 创建转换器实例
    try:
        converter = DocumentConverter()
        print("✓ 文档转换器初始化成功")
    except Exception as e:
        print(f"✗ 文档转换器初始化失败: {e}")
        return False
    
    # 检查是否支持PDF转换
    if converter.can_convert(".pdf", ".md"):
        print("✓ 支持PDF转Markdown转换")
    else:
        print("✗ 不支持PDF转Markdown转换")
        return False
    
    # 查找测试PDF文件
    test_files = []
    for file in os.listdir("."):
        if file.lower().endswith(".pdf"):
            test_files.append(file)
    
    if not test_files:
        print("⚠ 当前目录下没有找到PDF文件用于测试")
        print("请将PDF文件放在项目根目录下再运行测试")
        return False
    
    print(f"找到 {len(test_files)} 个PDF文件:")
    for i, file in enumerate(test_files, 1):
        print(f"  {i}. {file}")
    
    # 测试转换第一个PDF文件
    test_file = test_files[0]
    output_file = f"{os.path.splitext(test_file)[0]}_converted.md"
    
    try:
        print(f"\n正在转换 {test_file} -> {output_file}...")
        result = converter.convert_file(test_file, ".md")
        
        if result and os.path.exists(result):
            print(f"✓ 转换成功: {result}")
            
            # 显示转换结果的前几行
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')[:10]
                print("\n转换结果预览:")
                print("-" * 50)
                for line in lines:
                    print(line)
                if len(content.split('\n')) > 10:
                    print("...")
                print("-" * 50)
            
            return True
        else:
            print("✗ 转换失败: 未生成输出文件")
            return False
            
    except Exception as e:
        print(f"✗ 转换过程中出错: {e}")
        return False

def test_batch_conversion():
    """测试批量转换功能"""
    print("\n测试批量PDF转Markdown转换功能...")
    
    # 创建转换器实例
    converter = DocumentConverter()
    
    # 查找所有PDF文件
    pdf_files = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]
    
    if len(pdf_files) < 2:
        print("⚠ 需要至少2个PDF文件来测试批量转换功能")
        return False
    
    try:
        print(f"正在批量转换 {len(pdf_files)} 个PDF文件...")
        results = converter.batch_convert(pdf_files, ".md")
        
        print(f"✓ 批量转换完成，成功转换 {len(results)} 个文件:")
        for result in results:
            print(f"  - {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ 批量转换失败: {e}")
        return False

if __name__ == "__main__":
    print("DocuFlow PDF转Markdown功能测试")
    print("=" * 50)
    
    # 测试单个文件转换
    success1 = test_pdf_to_markdown()
    
    # 测试批量转换
    success2 = test_batch_conversion()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ 所有测试通过！PDF转Markdown功能正常工作")
    else:
        print("✗ 部分测试失败，请检查错误信息")