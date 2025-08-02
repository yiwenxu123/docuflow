#!/usr/bin/env python3
"""
测试实际文档格式转换（Word、Excel、PDF）
"""

import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from converter.document_converter import DocumentConverter
from utils.config_manager import ConfigManager

def create_word_document():
    """创建测试Word文档"""
    try:
        from docx import Document
        
        doc = Document()
        doc.add_heading('DocuFlow测试文档', 0)
        
        doc.add_heading('第一章：介绍', level=1)
        doc.add_paragraph('这是一个测试Word文档，用于验证DocuFlow的Word转Markdown功能。')
        
        doc.add_heading('第二章：功能列表', level=1)
        doc.add_paragraph('DocuFlow支持以下功能：')
        
        # 添加列表
        doc.add_paragraph('• PDF转Markdown', style='List Bullet')
        doc.add_paragraph('• Excel转Markdown', style='List Bullet')
        doc.add_paragraph('• Word转Markdown', style='List Bullet')
        
        word_file = "test_word_doc.docx"
        doc.save(word_file)
        return word_file
        
    except ImportError:
        print("   ⚠️  python-docx未安装，跳过Word文档创建")
        return None

def create_excel_document():
    """创建测试Excel文档"""
    try:
        import openpyxl
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "员工信息"
        
        # 添加测试数据
        headers = ["姓名", "年龄", "职位", "部门", "薪资"]
        data = [
            ["张三", 28, "软件工程师", "技术部", 15000],
            ["李四", 32, "产品经理", "产品部", 18000],
            ["王五", 25, "UI设计师", "设计部", 12000],
            ["赵六", 35, "技术总监", "技术部", 25000]
        ]
        
        # 写入表头
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # 写入数据
        for row, row_data in enumerate(data, 2):
            for col, value in enumerate(row_data, 1):
                ws.cell(row=row, column=col, value=value)
        
        excel_file = "test_excel_doc.xlsx"
        wb.save(excel_file)
        wb.close()
        return excel_file
        
    except ImportError:
        print("   ⚠️  openpyxl未安装，跳过Excel文档创建")
        return None

def test_document_conversion(converter, file_path, output_format, test_name):
    """测试文档转换"""
    if not file_path or not os.path.exists(file_path):
        print(f"   ⚠️  {test_name}: 测试文件不存在，跳过")
        return False
        
    try:
        print(f"   测试 {test_name}...")
        file_size = os.path.getsize(file_path)
        print(f"   输入文件: {file_path} (大小: {file_size} bytes)")
        
        output_path = converter.convert_file(file_path, output_format)
        
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"   ✓ 转换成功: {output_path} (大小: {output_size} bytes)")
            
            # 显示内容预览
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')[:10]  # 显示前10行
                print(f"   内容预览 (前10行):")
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        print(f"     {i}: {line[:80]}{'...' if len(line) > 80 else ''}")
            
            return True
        else:
            print(f"   ✗ 转换失败: 输出文件不存在")
            return False
            
    except Exception as e:
        print(f"   ✗ 转换失败: {str(e)}")
        return False

def main():
    print("=== DocuFlow 实际文档格式转换测试 ===\n")
    
    # 初始化转换器
    try:
        config_manager = ConfigManager()
        converter = DocumentConverter(config_manager)
        print("1. ✓ 转换器初始化成功")
    except Exception as e:
        print(f"1. ✗ 转换器初始化失败: {e}")
        return
    
    # 创建测试文档
    print("\n2. 创建测试文档...")
    word_file = create_word_document()
    excel_file = create_excel_document()
    
    if word_file:
        print(f"   ✓ Word文档创建成功: {word_file}")
    if excel_file:
        print(f"   ✓ Excel文档创建成功: {excel_file}")
    
    # 定义转换测试
    conversions = []
    
    if word_file:
        conversions.extend([
            (word_file, '.md', 'Word -> Markdown'),
            (word_file, '.html', 'Word -> HTML'),
            (word_file, '.txt', 'Word -> TXT'),
        ])
    
    if excel_file:
        conversions.extend([
            (excel_file, '.md', 'Excel -> Markdown'),
            (excel_file, '.html', 'Excel -> HTML'),
            (excel_file, '.txt', 'Excel -> TXT'),
        ])
    
    if not conversions:
        print("\n⚠️  没有可用的测试文档，请安装 python-docx 和 openpyxl")
        return
    
    print(f"\n3. 开始转换测试 (共{len(conversions)}项):")
    success_count = 0
    total_count = len(conversions)
    
    for file_path, output_format, test_name in conversions:
        if test_document_conversion(converter, file_path, output_format, test_name):
            success_count += 1
        print()  # 空行分隔
    
    # 显示测试结果
    print(f"=== 测试结果 ===")
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 所有实际文档转换测试通过！")
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个测试失败")
    
    # 清理测试文件
    print("\n4. 清理测试文件...")
    for file_path in [word_file, excel_file]:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"   ✓ 删除: {file_path}")
    
    # 清理输出文件
    for file_path, output_format, _ in conversions:
        if file_path:
            base_name = os.path.splitext(file_path)[0]
            output_file = base_name + output_format
            if os.path.exists(output_file):
                os.remove(output_file)
                print(f"   ✓ 删除: {output_file}")

if __name__ == "__main__":
    main()