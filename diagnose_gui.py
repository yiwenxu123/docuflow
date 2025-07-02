#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI环境诊断脚本
用于诊断 macOS 上 Tkinter GUI 无法显示的问题
"""

import sys
import os
import platform
import subprocess

def check_environment():
    """检查运行环境"""
    print("=== 环境诊断 ===")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前用户: {os.getenv('USER', 'unknown')}")
    print(f"HOME目录: {os.getenv('HOME', 'unknown')}")
    print(f"DISPLAY: {os.getenv('DISPLAY', 'not set')}")
    print(f"SSH_CLIENT: {os.getenv('SSH_CLIENT', 'not set')}")
    print(f"SSH_TTY: {os.getenv('SSH_TTY', 'not set')}")
    print(f"TERM: {os.getenv('TERM', 'not set')}")
    print()

def check_tkinter():
    """检查Tkinter可用性"""
    print("=== Tkinter 检查 ===")
    try:
        import tkinter as tk
        print(f"✓ Tkinter导入成功")
        print(f"✓ Tkinter版本: {tk.TkVersion}")
        print(f"✓ Tcl版本: {tk.TclVersion}")
        
        # 尝试创建根窗口但不显示
        try:
            root = tk.Tk()
            root.withdraw()  # 隐藏窗口
            print("✓ 根窗口创建成功")
            root.destroy()
        except Exception as e:
            print(f"✗ 根窗口创建失败: {e}")
            return False
            
    except ImportError as e:
        print(f"✗ Tkinter导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ Tkinter检查失败: {e}")
        return False
    
    print()
    return True

def check_display_capability():
    """检查显示能力"""
    print("=== 显示能力检查 ===")
    
    # 检查是否在SSH会话中
    if os.getenv('SSH_CLIENT') or os.getenv('SSH_TTY'):
        print("⚠ 检测到SSH会话 - GUI可能无法显示")
        print("  建议: 使用 ssh -X 或 ssh -Y 启用X11转发")
        print("  或者在本地终端中运行")
    else:
        print("✓ 不在SSH会话中")
    
    # 检查终端类型
    term = os.getenv('TERM', '')
    if 'screen' in term or 'tmux' in term:
        print(f"⚠ 检测到终端复用器: {term}")
        print("  GUI显示可能受限")
    
    # 检查是否有图形界面
    try:
        # 在macOS上检查是否有窗口服务器
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'WindowServer' in result.stdout:
            print("✓ 检测到 macOS 窗口服务器")
        else:
            print("⚠ 未检测到窗口服务器")
    except:
        print("? 无法检查窗口服务器状态")
    
    print()

def test_minimal_gui():
    """测试最小GUI"""
    print("=== 最小GUI测试 ===")
    
    try:
        import tkinter as tk
        
        print("创建隐藏窗口...")
        root = tk.Tk()
        root.withdraw()  # 先隐藏
        root.title("诊断测试")
        root.geometry("200x100")
        
        print("添加组件...")
        label = tk.Label(root, text="测试")
        label.pack()
        
        print("尝试显示窗口...")
        root.deiconify()  # 显示窗口
        root.update_idletasks()
        
        print("设置自动关闭...")
        root.after(3000, root.quit)  # 3秒后自动关闭
        
        print("启动主循环 (3秒后自动关闭)...")
        root.mainloop()
        
        print("✓ GUI测试完成")
        return True
        
    except Exception as e:
        print(f"✗ GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("DocuFlow GUI 环境诊断工具")
    print("=" * 40)
    
    check_environment()
    
    if not check_tkinter():
        print("❌ Tkinter不可用，无法运行GUI")
        return False
    
    check_display_capability()
    
    print("开始GUI测试...")
    success = test_minimal_gui()
    
    print("\n=== 诊断结果 ===")
    if success:
        print("✅ GUI环境正常，应该可以显示窗口")
        print("如果DocuFlow GUI仍然无法显示，可能是应用程序特定的问题")
    else:
        print("❌ GUI环境有问题")
        print("建议:")
        print("1. 确保在本地图形终端中运行")
        print("2. 如果使用SSH，启用X11转发")
        print("3. 检查系统权限和安全设置")
        print("4. 尝试重启终端或系统")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n诊断过程出错: {e}")
        import traceback
        traceback.print_exc()