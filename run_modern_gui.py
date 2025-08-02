#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 现代化GUI启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查必要的依赖"""
    missing_deps = []
    
    try:
        import PyPDF2
    except ImportError:
        missing_deps.append('PyPDF2')
    
    try:
        import pdfplumber
    except ImportError:
        missing_deps.append('pdfplumber')
    
    try:
        import openpyxl
    except ImportError:
        missing_deps.append('openpyxl')
    
    try:
        import pandas
    except ImportError:
        missing_deps.append('pandas')
    
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        try:
            from PyQt5.QtWidgets import QApplication
        except ImportError:
            missing_deps.append('PySide6 或 PyQt5')
    
    if missing_deps:
        print("❌ 缺少以下依赖:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n请运行以下命令安装:")
        print("pip install PyPDF2 pdfplumber openpyxl pandas PySide6")
        return False
    
    print("✅ 所有依赖检查通过")
    return True

def main():
    """主函数"""
    print("🚀 启动 DocuFlow 现代化文档转换器...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # 导入并启动现代化GUI
        from ui.modern_main_window import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有文件都在正确的位置")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()