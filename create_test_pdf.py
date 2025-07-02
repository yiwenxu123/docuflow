#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试PDF文件
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def create_test_pdf():
    """创建一个简单的测试PDF文件"""
    filename = "test_document.pdf"
    
    # 创建PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # 添加标题
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "DocuFlow 测试文档")
    
    # 添加正文
    c.setFont("Helvetica", 12)
    y_position = height - 150
    
    content = [
        "这是一个用于测试DocuFlow PDF转Markdown功能的示例文档。",
        "",
        "主要特性：",
        "• 支持PDF转Markdown转换",
        "• 保持文档结构和格式",
        "• 支持批量转换",
        "• 提取表格内容",
        "",
        "技术实现：",
        "- 使用PyPDF2和pdfplumber库",
        "- 智能文本清理和格式化",
        "- Markdown格式输出",
        "",
        "这个PDF文件将被转换为Markdown格式，",
        "以验证转换功能的正确性。"
    ]
    
    for line in content:
        c.drawString(100, y_position, line)
        y_position -= 20
    
    # 添加第二页
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, "第二页内容")
    
    c.setFont("Helvetica", 12)
    y_position = height - 150
    
    page2_content = [
        "这是第二页的内容，用于测试多页PDF的转换。",
        "",
        "转换后应该能看到：",
        "1. 页面分隔标记",
        "2. 保持的文本结构",
        "3. 正确的中文编码",
        "",
        "如果您能看到这些内容，说明PDF转Markdown功能工作正常。"
    ]
    
    for line in page2_content:
        c.drawString(100, y_position, line)
        y_position -= 20
    
    # 保存PDF
    c.save()
    
    print(f"测试PDF文件已创建: {filename}")
    return filename

if __name__ == "__main__":
    try:
        create_test_pdf()
        print("✓ 测试PDF文件创建成功")
    except ImportError:
        print("⚠ 需要安装reportlab库来创建测试PDF")
        print("请运行: pip install reportlab")
    except Exception as e:
        print(f"✗ 创建测试PDF失败: {e}")