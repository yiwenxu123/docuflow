#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的PySide6测试脚本
"""

import sys
import os

# 设置环境变量
os.environ['QT_QPA_PLATFORM'] = 'cocoa'

try:
    from PySide6.QtWidgets import QApplication, QLabel, QWidget
    from PySide6.QtCore import Qt
    
    print("PySide6导入成功")
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建简单窗口
    window = QWidget()
    window.setWindowTitle("PySide6测试")
    window.resize(300, 200)
    
    label = QLabel("Hello PySide6!", window)
    label.setAlignment(Qt.AlignCenter)
    label.resize(300, 200)
    
    window.show()
    
    print("窗口已显示，测试成功！")
    
    # 运行应用（注释掉以避免阻塞）
    # sys.exit(app.exec())
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()