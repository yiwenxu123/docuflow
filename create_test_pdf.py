#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试PDF文件
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def create_test_pdf():
    """创建测试PDF文件"""
    filename = "test_document.pdf"
    
    # 创建PDF文档
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    
    # 获取样式
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # 添加标题
    story.append(Paragraph("DocuFlow PDF转换测试文档", title_style))
    story.append(Spacer(1, 12))
    
    # 添加介绍段落
    intro_text = """
    这是一个用于测试DocuFlow PDF转Markdown功能的示例文档。
    本文档包含多种元素，包括标题、段落、列表和表格。
    """
    story.append(Paragraph(intro_text, normal_style))
    story.append(Spacer(1, 12))
    
    # 添加章节标题
    story.append(Paragraph("第一章：功能特性", heading_style))
    story.append(Spacer(1, 12))
    
    # 添加功能列表
    features_text = """
    DocuFlow支持以下功能：<br/>
    • PDF转Markdown格式<br/>
    • Excel转Markdown格式<br/>
    • Word转Markdown格式<br/>
    • 批量文件转换<br/>
    • 智能文本清理<br/>
    • 表格格式保持
    """
    story.append(Paragraph(features_text, normal_style))
    story.append(Spacer(1, 12))
    
    # 添加第二章
    story.append(Paragraph("第二章：技术规格", heading_style))
    story.append(Spacer(1, 12))
    
    # 添加技术信息
    tech_text = """
    DocuFlow使用以下技术栈：<br/>
    - Python 3.9+<br/>
    - PySide6 (GUI框架)<br/>
    - PyPDF2 和 pdfplumber (PDF处理)<br/>
    - openpyxl (Excel处理)<br/>
    - python-docx (Word处理)<br/>
    - Pandoc (格式转换引擎)
    """
    story.append(Paragraph(tech_text, normal_style))
    story.append(Spacer(1, 12))
    
    # 添加表格
    story.append(Paragraph("第三章：性能数据", heading_style))
    story.append(Spacer(1, 12))
    
    # 创建表格数据
    table_data = [
        ['文件类型', '平均转换时间', '成功率', '支持特性'],
        ['PDF', '2-5秒', '95%', '文本、表格'],
        ['Excel', '1-3秒', '98%', '工作表、公式'],
        ['Word', '2-4秒', '96%', '格式、图片'],
        ['PowerPoint', '3-6秒', '92%', '幻灯片、动画']
    ]
    
    # 创建表格
    table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 12))
    
    # 添加结论
    story.append(Paragraph("结论", heading_style))
    story.append(Spacer(1, 12))
    
    conclusion_text = """
    DocuFlow是一个功能强大的文档转换工具，支持多种格式之间的转换。
    通过智能的文本处理和格式保持技术，确保转换质量和用户体验。
    本测试文档验证了PDF转Markdown功能的有效性。
    """
    story.append(Paragraph(conclusion_text, normal_style))
    
    # 构建PDF
    doc.build(story)
    print(f"✅ 测试PDF文件已创建: {filename}")
    return filename

if __name__ == "__main__":
    try:
        pdf_file = create_test_pdf()
        print(f"📄 PDF文件大小: {os.path.getsize(pdf_file)} 字节")
    except Exception as e:
        print(f"❌ 创建PDF失败: {e}")
        print("请确保已安装reportlab: pip install reportlab")