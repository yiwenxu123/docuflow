#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Excel转换测试脚本
用于验证DocuFlow GUI界面的Excel转Markdown功能
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtCore import QTimer

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from converter.document_converter import DocumentConverter

def test_excel_conversion_gui():
    """测试Excel转换功能（GUI模式）"""
    app = QApplication(sys.argv)
    
    # 创建转换器实例
    converter = DocumentConverter()
    
    # 选择Excel文件
    excel_file, _ = QFileDialog.getOpenFileName(
        None,
        "选择Excel文件",
        os.path.expanduser("~/Downloads"),
        "Excel文件 (*.xlsx *.xls)"
    )
    
    if not excel_file:
        print("用户取消了文件选择")
        return
    
    print(f"选择的Excel文件: {excel_file}")
    
    # 选择输出目录
    output_dir = QFileDialog.getExistingDirectory(
        None,
        "选择输出目录",
        os.path.dirname(excel_file)
    )
    
    if not output_dir:
        print("用户取消了目录选择")
        return
    
    # 生成输出文件名
    excel_name = Path(excel_file).stem
    output_file = os.path.join(output_dir, f"{excel_name}.md")
    
    print(f"输出文件: {output_file}")
    
    try:
        # 执行转换
        print("开始转换...")
        result = converter.convert_file(excel_file, output_file)
        
        # 显示成功消息
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("转换成功")
        msg.setText(f"Excel文件已成功转换为Markdown格式！\n\n输出文件: {result}")
        msg.setStandardButtons(QMessageBox.Ok)
        
        # 添加打开文件按钮
        open_button = msg.addButton("打开文件", QMessageBox.ActionRole)
        open_folder_button = msg.addButton("打开文件夹", QMessageBox.ActionRole)
        
        msg.exec_()
        
        # 处理按钮点击
        if msg.clickedButton() == open_button:
            os.system(f'open "{result}"')
        elif msg.clickedButton() == open_folder_button:
            os.system(f'open "{output_dir}"')
            
        print(f"转换成功: {result}")
        
    except Exception as e:
        # 显示错误消息
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setWindowTitle("转换失败")
        error_msg.setText(f"Excel转换失败！\n\n错误信息: {str(e)}")
        error_msg.setDetailedText(f"文件: {excel_file}\n输出: {output_file}\n错误: {str(e)}")
        error_msg.setStandardButtons(QMessageBox.Ok)
        error_msg.exec_()
        
        print(f"转换失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("DocuFlow Excel转换测试工具")
    print("=" * 40)
    print("此工具用于测试Excel到Markdown的转换功能")
    print("请选择要转换的Excel文件...")
    print()
    
    test_excel_conversion_gui()
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()