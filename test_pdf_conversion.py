#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转换专项测试
"""

import os
import sys
import traceback

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from converter.document_converter import DocumentConverter
from utils.config_manager import ConfigManager

def create_simple_pdf():
    """创建简单的PDF测试文件"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_file = 'test_simple.pdf'
        c = canvas.Canvas(pdf_file, pagesize=letter)
        
        # 添加简单的英文文本
        c.drawString(100, 750, "Test PDF Document")
        c.drawString(100, 720, "This is a test PDF file.")
        c.drawString(100, 690, "Chapter 1: Introduction")
        c.drawString(100, 660, "This chapter contains sample text.")
        c.drawString(100, 630, "We will test PDF to Markdown conversion.")
        
        c.save()
        print(f"✓ 创建简单PDF文件: {pdf_file}")
        return pdf_file
    except Exception as e:
        print(f"✗ 创建PDF文件失败: {e}")
        traceback.print_exc()
        return None

def test_pdf_conversion():
    """测试PDF转换"""
    print("=== PDF转Markdown专项测试 ===\n")
    
    try:
        # 初始化转换器
        print("1. 初始化转换器...")
        config = ConfigManager()
        converter = DocumentConverter(config)
        print("✓ 转换器初始化成功")
        
        # 创建PDF测试文件
        print("\n2. 创建PDF测试文件...")
        pdf_file = create_simple_pdf()
        
        if not pdf_file:
            print("✗ 无法创建PDF测试文件")
            return
        
        # 检查PDF文件
        if not os.path.exists(pdf_file):
            print(f"✗ PDF文件不存在: {pdf_file}")
            return
        
        file_size = os.path.getsize(pdf_file)
        print(f"✓ PDF文件创建成功: {pdf_file} (大小: {file_size} bytes)")
        
        # 检查转换支持
        print("\n3. 检查转换支持...")
        if converter.can_convert('.pdf', '.md'):
            print("✓ 支持PDF转Markdown")
        else:
            print("✗ 不支持PDF转Markdown")
            return
        
        # 执行转换
        print("\n4. 执行PDF转Markdown转换...")
        result = converter.convert_file(pdf_file, '.md')
        
        if result and os.path.exists(result):
            output_size = os.path.getsize(result)
            print(f"✓ 转换成功: {result} (大小: {output_size} bytes)")
            
            # 显示内容
            try:
                with open(result, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print("\n转换结果内容:")
                    print("-" * 50)
                    print(content)
                    print("-" * 50)
            except Exception as e:
                print(f"无法读取输出文件: {e}")
        else:
            print(f"✗ 转换失败: {result}")
        
        # 清理文件
        print("\n5. 清理测试文件...")
        for file_path in [pdf_file, result]:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"✓ 删除: {file_path}")
            except Exception as e:
                print(f"✗ 删除文件失败 {file_path}: {e}")
        
    except Exception as e:
        print(f"✗ 测试过程出错: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_conversion()