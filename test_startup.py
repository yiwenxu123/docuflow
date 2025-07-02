#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试应用启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有必要的模块导入"""
    try:
        print("测试基础模块导入...")
        import logging
        from pathlib import Path
        print("✓ 基础模块导入成功")
        
        print("测试配置模块导入...")
        from config import config
        print(f"✓ 配置模块导入成功 - {config.app.name} v{config.app.version}")
        
        print("测试PySide6模块导入...")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        print("✓ PySide6模块导入成功")
        
        print("测试转换器模块导入...")
        from converter.document_converter import DocumentConverter
        print("✓ 转换器模块导入成功")
        
        print("测试异常模块导入...")
        from exceptions import ConversionError
        print("✓ 异常模块导入成功")
        
        print("测试工具模块导入...")
        from utils.file_utils import get_file_extension
        print("✓ 工具模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        return False

def test_gui_creation():
    """测试GUI创建"""
    try:
        print("\n测试GUI创建...")
        from PySide6.QtWidgets import QApplication
        from main_pyside import DocuFlowGUI
        
        app = QApplication([])
        gui = DocuFlowGUI()
        print("✓ GUI创建成功")
        
        # 不显示GUI，只测试创建
        app.quit()
        return True
        
    except Exception as e:
        print(f"✗ GUI创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("DocuFlow 启动测试")
    print("=" * 50)
    
    # 测试模块导入
    if not test_imports():
        print("\n❌ 模块导入测试失败")
        return False
    
    # 测试GUI创建
    if not test_gui_creation():
        print("\n❌ GUI创建测试失败")
        return False
    
    print("\n✅ 所有测试通过！应用可以正常启动。")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)