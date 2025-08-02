#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用现有PDF文件测试转换功能
"""

import os
import sys
import traceback

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from converter.document_converter import DocumentConverter
from utils.config_manager import ConfigManager

def create_text_pdf():
    """使用fpdf创建简单PDF"""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(40, 10, 'Test PDF Document')
        pdf.ln(20)
        pdf.set_font('Arial', '', 12)
        pdf.cell(40, 10, 'This is a test PDF file for conversion.')
        pdf.ln(10)
        pdf.cell(40, 10, 'Chapter 1: Introduction')
        pdf.ln(10)
        pdf.cell(40, 10, 'This chapter contains sample text content.')
        pdf.ln(10)
        pdf.cell(40, 10, 'We will test the PDF to Markdown conversion.')
        
        pdf_file = 'test_fpdf.pdf'
        pdf.output(pdf_file)
        print(f"✓ 创建PDF文件: {pdf_file}")
        return pdf_file
    except Exception as e:
        print(f"✗ 使用fpdf创建PDF失败: {e}")
        return None

def test_existing_pdf():
    """测试现有PDF文件"""
    # 查找现有的PDF文件
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    if pdf_files:
        return pdf_files[0]
    return None

def test_pdf_reading():
    """测试PDF读取功能"""
    print("=== PDF读取和转换测试 ===\n")
    
    try:
        # 初始化转换器
        print("1. 初始化转换器...")
        config = ConfigManager()
        converter = DocumentConverter(config)
        print("✓ 转换器初始化成功")
        
        # 尝试创建PDF文件
        print("\n2. 准备PDF测试文件...")
        pdf_file = create_text_pdf()
        
        if not pdf_file:
            # 尝试使用现有PDF文件
            pdf_file = test_existing_pdf()
            if pdf_file:
                print(f"✓ 使用现有PDF文件: {pdf_file}")
            else:
                print("✗ 无法找到或创建PDF测试文件")
                return
        
        # 检查文件
        if not os.path.exists(pdf_file):
            print(f"✗ PDF文件不存在: {pdf_file}")
            return
        
        file_size = os.path.getsize(pdf_file)
        print(f"✓ PDF文件准备就绪: {pdf_file} (大小: {file_size} bytes)")
        
        # 测试PDF读取功能
        print("\n3. 测试PDF文本提取...")
        try:
            # 直接测试PDF文本提取方法
            text = converter._extract_text_from_pdf(pdf_file)
            if text and text.strip():
                print(f"✓ PDF文本提取成功 (长度: {len(text)} 字符)")
                print("提取的文本预览:")
                print("-" * 40)
                print(text[:200] + "..." if len(text) > 200 else text)
                print("-" * 40)
            else:
                print("✗ PDF文本提取失败或内容为空")
        except Exception as e:
            print(f"✗ PDF文本提取出错: {e}")
            traceback.print_exc()
        
        # 检查转换支持
        print("\n4. 检查转换支持...")
        if converter.can_convert('.pdf', '.md'):
            print("✓ 支持PDF转Markdown")
        else:
            print("✗ 不支持PDF转Markdown")
            return
        
        # 执行完整转换
        print("\n5. 执行PDF转Markdown转换...")
        try:
            result = converter.convert_file(pdf_file, '.md')
            
            if result and os.path.exists(result):
                output_size = os.path.getsize(result)
                print(f"✓ 转换成功: {result} (大小: {output_size} bytes)")
                
                # 显示转换结果
                try:
                    with open(result, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print("\n转换结果:")
                        print("-" * 50)
                        print(content)
                        print("-" * 50)
                except Exception as e:
                    print(f"无法读取输出文件: {e}")
            else:
                print(f"✗ 转换失败: {result}")
        except Exception as e:
            print(f"✗ 转换过程出错: {e}")
            traceback.print_exc()
        
        # 清理文件
        print("\n6. 清理测试文件...")
        cleanup_files = []
        if pdf_file == 'test_fpdf.pdf':  # 只清理我们创建的文件
            cleanup_files.append(pdf_file)
        if 'result' in locals() and result:
            cleanup_files.append(result)
        
        for file_path in cleanup_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"✓ 删除: {file_path}")
            except Exception as e:
                print(f"✗ 删除文件失败 {file_path}: {e}")
        
    except Exception as e:
        print(f"✗ 测试过程出错: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_reading()