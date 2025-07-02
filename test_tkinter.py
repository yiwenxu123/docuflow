#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试tkinter GUI是否正常工作
"""

import tkinter as tk
from tkinter import ttk, messagebox

def test_gui():
    """测试GUI功能"""
    root = tk.Tk()
    root.title("DocuFlow - 文档转换器")
    root.geometry("400x300")
    
    # 创建标签
    label = ttk.Label(root, text="DocuFlow GUI 正常工作！", font=('Arial', 16))
    label.pack(pady=50)
    
    # 创建按钮
    def show_message():
        messagebox.showinfo("测试", "tkinter GUI 功能正常！")
    
    button = ttk.Button(root, text="测试按钮", command=show_message)
    button.pack(pady=20)
    
    # 3秒后自动关闭
    root.after(3000, root.destroy)
    
    root.mainloop()
    print("tkinter GUI 测试完成")

if __name__ == "__main__":
    test_gui()