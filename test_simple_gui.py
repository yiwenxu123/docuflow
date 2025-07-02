#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import sys
import os

def test_basic_gui():
    """测试基本GUI功能"""
    print("开始创建基本GUI测试...")
    
    try:
        # 创建根窗口
        root = tk.Tk()
        root.title("基本GUI测试")
        root.geometry("400x300")
        
        print("根窗口创建成功")
        
        # 添加一些基本组件
        label = ttk.Label(root, text="这是一个测试标签", font=("Arial", 14))
        label.pack(pady=20)
        
        button = ttk.Button(root, text="测试按钮", command=lambda: print("按钮被点击了！"))
        button.pack(pady=10)
        
        entry = ttk.Entry(root, width=30)
        entry.pack(pady=10)
        entry.insert(0, "这是一个输入框")
        
        # 添加文本框
        text_frame = ttk.Frame(root)
        text_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, height=5, width=40)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.insert(tk.END, "这是一个多行文本框\n可以输入多行文本\n测试滚动条功能")
        
        print("所有组件创建完成")
        
        # 强制更新显示
        root.update_idletasks()
        root.update()
        
        print("开始主循环...")
        
        # 启动主循环
        root.mainloop()
        
        print("主循环结束")
        
    except Exception as e:
        print(f"GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print(f"Python版本: {sys.version}")
    print(f"Tkinter版本: {tk.TkVersion}")
    print(f"当前工作目录: {os.getcwd()}")
    
    success = test_basic_gui()
    if success:
        print("GUI测试成功完成")
    else:
        print("GUI测试失败")
        sys.exit(1)