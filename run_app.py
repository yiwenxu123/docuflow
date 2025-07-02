#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 应用启动器
简化的启动脚本，避免Qt插件问题
"""

import sys
import os
from pathlib import Path

# 设置Qt环境变量
def setup_qt_environment():
    """设置Qt环境"""
    # 首先尝试找到Qt插件路径
    import glob
    possible_paths = [
        '/opt/homebrew/lib/python3.*/site-packages/PySide6/Qt/plugins',
        '/usr/local/lib/python3.*/site-packages/PySide6/Qt/plugins', 
        'venv/lib/python3.*/site-packages/PySide6/Qt/plugins',
    ]
    
    plugin_path = None
    for pattern in possible_paths:
        matches = glob.glob(pattern)
        if matches:
            plugin_path = matches[0]
            break
    
    if plugin_path:
        # 设置绝对路径
        abs_plugin_path = os.path.abspath(plugin_path)
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = abs_plugin_path
        print(f"设置Qt插件路径: {abs_plugin_path}")
        
        # 检查cocoa插件是否存在
        cocoa_plugin = os.path.join(abs_plugin_path, 'platforms', 'libqcocoa.dylib')
        if os.path.exists(cocoa_plugin):
            print(f"找到cocoa插件: {cocoa_plugin}")
            os.environ['QT_QPA_PLATFORM'] = 'cocoa'
        else:
            print("警告: 未找到cocoa插件，尝试使用minimal平台")
            os.environ['QT_QPA_PLATFORM'] = 'minimal'
    else:
        print("警告: 未找到Qt插件路径")
        os.environ['QT_QPA_PLATFORM'] = 'minimal'

setup_qt_environment()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    try:
        # 导入必要模块
        from PySide6.QtWidgets import QApplication
        from main_pyside import DocuFlowGUI
        from config import config
        
        print(f"启动 {config.app.name} v{config.app.version}...")
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName(config.app.name)
        app.setApplicationVersion(config.app.version)
        
        # 创建主窗口
        window = DocuFlowGUI()
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖包")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()