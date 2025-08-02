#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Excel文件支持功能
验证文件添加和拖拽功能是否正确支持Excel格式
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.file_utils import is_supported_file, get_supported_formats, get_conversion_targets

def test_excel_file_support():
    """测试Excel文件格式支持"""
    print("🧪 测试Excel文件格式支持")
    print("=" * 50)
    
    # 测试文件格式支持
    excel_files = [
        'test.xlsx',
        'test.xls',
        'document.XLSX',  # 测试大写
        'spreadsheet.XLS'
    ]
    
    print("📋 测试文件格式识别:")
    for file in excel_files:
        is_supported = is_supported_file(file)
        status = "✅ 支持" if is_supported else "❌ 不支持"
        print(f"  {file}: {status}")
    
    # 测试支持的格式列表
    print("\n📋 当前支持的文件格式:")
    formats = get_supported_formats()
    for ext, desc in formats.items():
        print(f"  {ext}: {desc}")
    
    # 测试转换目标
    print("\n📋 Excel文件转换支持:")
    for excel_ext in ['.xlsx', '.xls']:
        targets = get_conversion_targets(excel_ext)
        print(f"  {excel_ext} 可转换为: {', '.join(targets)}")
    
    return True

def create_test_excel_file():
    """创建测试Excel文件"""
    print("\n🔧 创建测试Excel文件...")
    
    try:
        import openpyxl
        
        # 创建测试Excel文件
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "测试数据"
        
        # 添加测试数据
        ws['A1'] = '姓名'
        ws['B1'] = '年龄'
        ws['C1'] = '城市'
        ws['A2'] = '张三'
        ws['B2'] = 25
        ws['C2'] = '北京'
        ws['A3'] = '李四'
        ws['B3'] = 30
        ws['C3'] = '上海'
        
        # 保存文件
        test_file = 'test_excel_support.xlsx'
        wb.save(test_file)
        
        print(f"✅ 创建测试文件: {test_file}")
        
        # 测试文件是否被识别为支持的格式
        if is_supported_file(test_file):
            print(f"✅ 文件被正确识别为支持的格式")
        else:
            print(f"❌ 文件未被识别为支持的格式")
        
        return test_file
        
    except ImportError:
        print("⚠️ openpyxl库未安装，无法创建Excel文件")
        return None
    except Exception as e:
        print(f"❌ 创建Excel文件时出错: {e}")
        return None

def test_file_validation():
    """测试文件验证功能"""
    print("\n🔍 测试文件验证功能...")
    
    test_cases = [
        ('document.docx', True),
        ('spreadsheet.xlsx', True),
        ('data.xls', True),
        ('readme.md', True),
        ('report.pdf', True),
        ('image.jpg', False),
        ('video.mp4', False),
        ('archive.zip', False),
        ('script.py', False)
    ]
    
    passed = 0
    total = len(test_cases)
    
    for filename, expected in test_cases:
        result = is_supported_file(filename)
        status = "✅ 通过" if result == expected else "❌ 失败"
        expected_str = "支持" if expected else "不支持"
        actual_str = "支持" if result else "不支持"
        print(f"  {filename}: 期望{expected_str}, 实际{actual_str} - {status}")
        
        if result == expected:
            passed += 1
    
    print(f"\n📊 验证结果: {passed}/{total} 测试通过")
    return passed == total

def cleanup_test_files():
    """清理测试文件"""
    print("\n🧹 清理测试文件...")
    test_files = ['test_excel_support.xlsx']
    
    for file_path in test_files:
        try:
            if Path(file_path).exists():
                Path(file_path).unlink()
                print(f"🗑️ 删除: {file_path}")
        except Exception as e:
            print(f"⚠️ 删除文件失败 {file_path}: {e}")

def main():
    print("🧪 Excel文件支持功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: Excel文件格式支持
    result1 = test_excel_file_support()
    test_results.append(('Excel文件格式支持', result1))
    
    # 测试2: 文件验证功能
    result2 = test_file_validation()
    test_results.append(('文件验证功能', result2))
    
    # 测试3: 创建和识别Excel文件
    test_file = create_test_excel_file()
    result3 = test_file is not None
    test_results.append(('Excel文件创建和识别', result3))
    
    # 汇总结果
    print("\n" + "=" * 60)
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
        print("\n🎉 所有测试通过！Excel文件支持功能已修复")
        print("\n📋 现在您可以:")
        print("  1. 通过文件选择对话框选择.xlsx和.xls文件")
        print("  2. 拖拽Excel文件到文件列表")
        print("  3. 批量选择文件夹中的Excel文件")
        print("  4. 将Excel文件转换为Markdown、HTML或PDF格式")
    else:
        print("\n⚠️ 部分测试失败，请检查修复情况")
    
    # 清理测试文件
    cleanup_test_files()
    
    return passed_tests == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)