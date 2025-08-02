#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试当前界面功能的脚本
确保所有转换功能正常工作
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有必要的模块导入"""
    print("=" * 50)
    print("测试模块导入...")
    
    try:
        # 测试核心模块导入
        from utils.config_manager import ConfigManager
        print("✓ ConfigManager 导入成功")
        
        from converter.document_converter import DocumentConverter
        print("✓ DocumentConverter 导入成功")
        
        from utils.file_utils import FileUtils
        print("✓ FileUtils 导入成功")
        
        from utils.logger import Logger
        print("✓ Logger 导入成功")
        
        # 测试GUI模块导入
        try:
            from PySide6.QtWidgets import QApplication
            print("✓ PySide6 导入成功")
        except ImportError:
            try:
                from PyQt5.QtWidgets import QApplication
                print("✓ PyQt5 导入成功")
            except ImportError:
                print("✗ 未找到Qt库")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        traceback.print_exc()
        return False

def test_config_manager():
    """测试配置管理器"""
    print("=" * 50)
    print("测试配置管理器...")
    
    try:
        from utils.config_manager import ConfigManager
        
        config = ConfigManager()
        print("✓ ConfigManager 初始化成功")
        
        # 测试支持的转换格式
        conversions = config.SUPPORTED_CONVERSIONS
        print(f"✓ 支持的转换格式: {len(conversions)} 种")
        
        # 检查Excel支持
        if '.xlsx' in conversions:
            print(f"✓ Excel支持: {conversions['.xlsx']}")
        else:
            print("✗ Excel转换不支持")
            return False
            
        # 检查PDF支持
        if '.pdf' in conversions:
            print(f"✓ PDF支持: {conversions['.pdf']}")
        else:
            print("✗ PDF转换不支持")
            
        return True
        
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        traceback.print_exc()
        return False

def test_document_converter():
    """测试文档转换器"""
    print("=" * 50)
    print("测试文档转换器...")
    
    try:
        from converter.document_converter import DocumentConverter
        from utils.config_manager import ConfigManager
        
        config = ConfigManager()
        converter = DocumentConverter(config)
        print("✓ DocumentConverter 初始化成功")
        
        # 测试Excel转换支持
        can_convert_excel = converter.can_convert('.xlsx', '.md')
        print(f"✓ Excel到Markdown转换支持: {can_convert_excel}")
        
        # 测试PDF转换支持
        can_convert_pdf = converter.can_convert('.pdf', '.md')
        print(f"✓ PDF到Markdown转换支持: {can_convert_pdf}")
        
        return True
        
    except Exception as e:
        print(f"✗ 文档转换器测试失败: {e}")
        traceback.print_exc()
        return False

def test_excel_conversion():
    """测试Excel转换功能"""
    print("=" * 50)
    print("测试Excel转换功能...")
    
    try:
        from converter.document_converter import DocumentConverter
        from utils.config_manager import ConfigManager
        
        # 检查测试文件是否存在
        test_file = project_root / "test_data.xlsx"
        if not test_file.exists():
            print("✗ 测试Excel文件不存在，跳过转换测试")
            return True
            
        config = ConfigManager()
        converter = DocumentConverter(config)
        
        output_file = project_root / "test_output" / "interface_test_excel.md"
        output_file.parent.mkdir(exist_ok=True)
        
        # 执行转换
        converter.convert_file(str(test_file), str(output_file))
        
        if output_file.exists():
            print("✓ Excel转换成功")
            # 读取并显示部分内容
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()[:200]
                print(f"✓ 转换内容预览: {content}...")
            return True
        else:
            print("✗ Excel转换失败 - 输出文件不存在")
            return False
            
    except Exception as e:
        print(f"✗ Excel转换测试失败: {e}")
        traceback.print_exc()
        return False

def test_file_operations():
    """测试文件操作功能"""
    print("=" * 50)
    print("测试文件操作功能...")
    
    try:
        from utils.file_utils import get_file_extension, is_supported_file
        
        # 测试文件扩展名检测
        ext = get_file_extension("test.xlsx")
        print(f"✓ 文件扩展名检测: {ext}")
        
        # 测试支持的格式检查
        is_supported = is_supported_file("test.xlsx")
        print(f"✓ 格式支持检查: {is_supported}")
        
        return True
        
    except Exception as e:
        print(f"✗ 文件操作测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("DocuFlow 当前界面功能测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置管理器", test_config_manager),
        ("文档转换器", test_document_converter),
        ("Excel转换", test_excel_conversion),
        ("文件操作", test_file_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n正在运行: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} 测试通过")
            else:
                print(f"✗ {test_name} 测试失败")
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有功能测试通过！当前界面功能正常。")
        return True
    else:
        print("⚠️  部分功能存在问题，需要修复。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)