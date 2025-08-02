#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 一键安装脚本
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    print("🚀 DocuFlow 一键安装")
    print("=" * 40)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要3.8+")
        print(f"当前版本: {sys.version}")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    print(f"✅ 操作系统: {platform.system()} {platform.release()}")
    
    # 安装依赖
    print("\n📦 安装依赖包...")
    
    # 优先使用轻量化依赖
    requirements_files = ["requirements_lite.txt", "requirements.txt"]
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            try:
                print(f"📋 使用 {req_file}...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "-r", req_file, "--user", "--upgrade", "--no-cache-dir"
                ], check=True, timeout=300)
                print("✅ 依赖安装完成")
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"⚠️  {req_file} 安装失败: {e}")
                continue
    else:
        print("❌ 所有依赖文件安装失败")
        print("💡 您可以手动安装核心依赖:")
        print("   pip install flask pypandoc python-docx openpyxl pandas")
        return False
    
    # 创建桌面快捷方式（可选）
    create_shortcuts()
    
    print("\n🎉 安装完成！")
    print("\n🚀 启动方式:")
    print("  ./start_docuflow.sh web    # Web界面")
    print("  ./start_docuflow.sh gui    # 图形界面")
    print("  ./start_docuflow.sh cli    # 命令行")
    
    return True

def create_shortcuts():
    """创建桌面快捷方式"""
    try:
        current_dir = Path(__file__).parent.absolute()
        
        if platform.system() == "Darwin":  # macOS
            # 创建 .command 文件
            command_file = Path.home() / "Desktop" / "DocuFlow.command"
            with open(command_file, 'w') as f:
                f.write(f'#!/bin/bash\ncd "{current_dir}"\n./start_docuflow.sh web\n')
            os.chmod(command_file, 0o755)
            print("✅ 已创建桌面快捷方式")
            
        elif platform.system() == "Windows":
            # 创建 .bat 文件
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "DocuFlow.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = str(current_dir / "start_docuflow.bat")
            shortcut.WorkingDirectory = str(current_dir)
            shortcut.save()
            print("✅ 已创建桌面快捷方式")
            
    except Exception as e:
        print(f"⚠️  快捷方式创建失败: {e}")

if __name__ == "__main__":
    main()
