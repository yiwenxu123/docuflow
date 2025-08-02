#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 文档转换器
主程序入口
"""

import sys
import os
from pathlib import Path

# 设置Qt插件路径
if hasattr(sys, '_MEIPASS'):
    # 如果是打包后的应用
    plugin_path = os.path.join(sys._MEIPASS, 'PySide6', 'plugins')
else:
    # 开发环境
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    plugin_path = os.path.join(venv_path, 'lib', 'python3.13', 'site-packages', 'PySide6', 'Qt', 'plugins')

os.environ['QT_PLUGIN_PATH'] = plugin_path
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(plugin_path, 'platforms')
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    QT_VERSION = "PySide6"
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        QT_VERSION = "PyQt5"
    except ImportError:
        print("错误：未找到可用的Qt库（PySide6或PyQt5）")
        sys.exit(1)

from ui.modern_main_window import ModernMainWindow

def main():
    """主函数"""
    print(f"使用Qt库: {QT_VERSION}")
    
    # 设置高DPI支持（必须在创建QApplication之前）
    if QT_VERSION == "PySide6":
        # PySide6的高DPI设置
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    else:
        # PyQt5的高DPI设置
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("DocuFlow")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用程序样式
    app.setStyle('Fusion')  # 使用现代化样式
    
    # 创建现代化主窗口
    window = ModernMainWindow()
    window.show()
    
    # 运行应用程序
    if QT_VERSION == "PySide6":
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()