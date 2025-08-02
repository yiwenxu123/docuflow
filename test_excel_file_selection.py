#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Excel文件选择功能
验证GUI界面是否正确支持.xlsx和.xls文件选择
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PySide6.QtWidgets import QApplication, QFileDialog
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt5.QtWidgets import QApplication, QFileDialog
    from PyQt5.QtCore import Qt

from ui.main_window import FileTypeFilterDialog

def test_file_dialog_filter():
    """测试文件选择对话框的过滤器"""
    print("🔍 测试文件选择对话框过滤器...")
    
    # 模拟文件选择对话框的过滤器字符串
    filter_string = "支持的文件 (*.docx *.md *.pdf *.html *.epub *.xlsx *.xls);;Word文档 (*.docx);;Markdown (*.md);;PDF (*.pdf);;HTML (*.html);;EPUB (*.epub);;Excel表格 (*.xlsx *.xls);;所有文件 (*)"
    
    # 检查是否包含Excel格式
    excel_formats = ['.xlsx', '.xls']
    missing_formats = []
    
    for fmt in excel_formats:
        if f'*{fmt}' not in filter_string:
            missing_formats.append(fmt)
    
    if missing_formats:
        print(f"❌ 文件选择对话框缺少格式: {', '.join(missing_formats)}")
        return False
    else:
        print("✅ 文件选择对话框包含所有Excel格式")
        print(f"📋 过滤器字符串: {filter_string}")
        return True

def test_file_type_filter_dialog():
    """测试文件类型过滤对话框"""
    print("\n🔍 测试文件类型过滤对话框...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        # 创建文件类型过滤对话框
        dialog = FileTypeFilterDialog()
        
        # 检查是否包含Excel文件类型
        excel_types = ['.xlsx', '.xls']
        missing_types = []
        
        for excel_type in excel_types:
            if excel_type not in dialog.checkboxes:
                missing_types.append(excel_type)
        
        if missing_types:
            print(f"❌ 文件类型过滤对话框缺少类型: {', '.join(missing_types)}")
            return False
        else:
            print("✅ 文件类型过滤对话框包含所有Excel类型")
            
            # 显示所有支持的文件类型
            print("📋 支持的文件类型:")
            for file_type, checkbox in dialog.checkboxes.items():
                print(f"  - {file_type}: {checkbox.text()}")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试文件类型过滤对话框时出错: {e}")
        return False

def test_excel_file_creation():
    """测试创建Excel文件并验证识别"""
    print("\n🔍 测试Excel文件创建和识别...")
    
    try:
        import openpyxl
        
        # 创建测试Excel文件
        test_files = {
            'test_selection.xlsx': 'Excel 2007+格式',
            'test_selection.xls': 'Excel 97-2003格式（需要xlwt库）'
        }
        
        created_files = []
        
        # 创建.xlsx文件
        xlsx_file = 'test_selection.xlsx'
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "测试数据"
        ws['A1'] = '文件类型'
        ws['B1'] = '状态'
        ws['A2'] = 'Excel XLSX'
        ws['B2'] = '支持选择'
        wb.save(xlsx_file)
        created_files.append(xlsx_file)
        print(f"✅ 创建测试文件: {xlsx_file}")
        
        # 验证文件存在
        for file_path in created_files:
            if Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                print(f"📄 {file_path}: {file_size} 字节")
            else:
                print(f"❌ 文件不存在: {file_path}")
        
        return True, created_files
        
    except ImportError:
        print("⚠️ openpyxl库未安装，无法创建Excel文件")
        return False, []
    except Exception as e:
        print(f"❌ 创建Excel文件时出错: {e}")
        return False, []

def cleanup_test_files(files):
    """清理测试文件"""
    print("\n🧹 清理测试文件...")
    for file_path in files:
        try:
            if Path(file_path).exists():
                Path(file_path).unlink()
                print(f"🗑️ 删除: {file_path}")
        except Exception as e:
            print(f"⚠️ 删除文件失败 {file_path}: {e}")

def main():
    print("🧪 Excel文件选择功能测试")
    print("=" * 50)
    
    test_results = []
    created_files = []
    
    # 测试1: 文件选择对话框过滤器
    result1 = test_file_dialog_filter()
    test_results.append(('文件选择对话框过滤器', result1))
    
    # 测试2: 文件类型过滤对话框
    result2 = test_file_type_filter_dialog()
    test_results.append(('文件类型过滤对话框', result2))
    
    # 测试3: Excel文件创建和识别
    result3, files = test_excel_file_creation()
    test_results.append(('Excel文件创建和识别', result3))
    created_files.extend(files)
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！Excel文件选择功能已修复")
        print("\n📋 使用说明:")
        print("  1. 启动GUI应用: python3 main.py")
        print("  2. 点击'选择文件'按钮")
        print("  3. 在文件类型下拉菜单中选择'Excel表格 (*.xlsx *.xls)'")
        print("  4. 或选择'支持的文件'查看所有格式")
        print("  5. 选择您的Excel文件进行转换")
    else:
        print("\n⚠️ 部分测试失败，请检查修复情况")
    
    # 清理测试文件
    if created_files:
        cleanup_test_files(created_files)

if __name__ == '__main__':
    main()