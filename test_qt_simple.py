#!/usr/bin/env python3
import os
import sys

# 设置Qt插件路径
qt_plugin_path = "/Users/yiwenxu123/Documents/tare/文档转换/venv/lib/python3.13/site-packages/PySide6/Qt/plugins"
os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path

print(f"设置QT_PLUGIN_PATH: {qt_plugin_path}")
print(f"设置QT_QPA_PLATFORM_PLUGIN_PATH: {qt_plugin_path}")

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication, Qt
    
    # 设置应用程序属性
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    
    app = QApplication(sys.argv)
    print("Qt应用程序创建成功！")
    
    # 立即退出，不显示窗口
    app.quit()
    print("测试完成")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()