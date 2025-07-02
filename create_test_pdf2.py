#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def create_test_pdf2():
    """创建第二个测试PDF文件"""
    filename = "test_document2.pdf"
    
    # 创建PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # 第一页
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "DocuFlow Test Document 2")
    
    c.setFont("Helvetica", 12)
    y_position = height - 150
    
    content = [
        "This is the second test document for DocuFlow.",
        "It contains multiple paragraphs and formatting.",
        "",
        "Features tested:",
        "• Document conversion",
        "• Text extraction",
        "• Markdown generation",
        "• Batch processing",
        "",
        "This document helps test the batch conversion functionality."
    ]
    
    for line in content:
        if line:
            c.drawString(100, y_position, line)
        y_position -= 20
    
    # 第二页
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, "Page 2 - Additional Content")
    
    c.setFont("Helvetica", 12)
    y_position = height - 150
    
    page2_content = [
        "This is the second page of the test document.",
        "",
        "Technical specifications:",
        "1. PDF format support",
        "2. Multi-page documents",
        "3. Text formatting preservation",
        "4. Unicode character support",
        "",
        "End of test document 2."
    ]
    
    for line in page2_content:
        if line:
            c.drawString(100, y_position, line)
        y_position -= 20
    
    c.save()
    print(f"✓ 创建测试PDF文件: {filename}")
    return filename

if __name__ == "__main__":
    create_test_pdf2()