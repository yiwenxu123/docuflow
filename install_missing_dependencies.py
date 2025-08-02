#!/usr/bin/env python3
"""
安装缺失的依赖包
"""

import subprocess
import sys
import importlib
import os

def check_and_install_package(package_name, import_name=None):
    """检查并安装包"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} 已安装")
        return True
    except ImportError:
        print(f"❌ {package_name} 未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ {package_name} 安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ {package_name} 安装失败: {e}")
            return False

def main():
    """主函数"""
    print("检查并安装缺失的依赖包...")
    
    # 需要检查的包列表
    packages = [
        ("docx2txt", "docx2txt"),
        ("python-docx", "docx"),
        ("markdownify", "markdownify"),
        ("openpyxl", "openpyxl"),
        ("xlrd", "xlrd"),
        ("pdfplumber", "pdfplumber"),
        ("PyPDF2", "PyPDF2"),
        ("beautifulsoup4", "bs4"),
        ("lxml", "lxml"),
        ("requests", "requests"),
        ("flask", "flask"),
        ("werkzeug", "werkzeug")
    ]
    
    success_count = 0
    total_count = len(packages)
    
    for package_name, import_name in packages:
        if check_and_install_package(package_name, import_name):
            success_count += 1
    
    print(f"\n安装结果: {success_count}/{total_count} 个包安装成功")
    
    if success_count == total_count:
        print("✅ 所有依赖包都已安装完成！")
    else:
        print("⚠️ 部分依赖包安装失败，请手动检查")

if __name__ == "__main__":
    main()