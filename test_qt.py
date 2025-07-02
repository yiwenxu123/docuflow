#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

def test_qt():
    """测试PyQt5是否能正常工作"""
    print("正在测试PyQt5...")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建简单窗口
    window = QWidget()
    window.setWindowTitle("PyQt5 测试")
    window.setGeometry(100, 100, 300, 200)
    
    # 添加标签
    layout = QVBoxLayout()
    label = QLabel("PyQt5 正常工作！")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    window.setLayout(layout)
    
    # 显示窗口
    window.show()
    print("窗口已显示，PyQt5 工作正常！")
    
    # 3秒后自动关闭
    from PyQt5.QtCore import QTimer
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(3000)  # 3秒
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_qt()