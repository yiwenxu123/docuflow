#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换功能诊断工具
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from converter.document_converter import DocumentConverter
from utils.config_manager import ConfigManager

def create_test_files():
    """创建测试文件"""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # 创建简单的文本文件
    txt_file = test_dir / "test.txt"
    txt_file.write_text("这是一个测试文档。\n\n包含多行内容。", encoding='utf-8')
    
    # 创建简单的Markdown文件
    md_file = test_dir / "test.md"
    md_file.write_text("# 测试标题\n\n这是测试内容。", encoding='utf-8')
    
    return test_dir, txt_file, md_file

def test_conversion():
    """测试转换功能"""
    print("=== DocuFlow 转换功能诊断 ===\n")
    
    try:
        # 初始化配置和转换器
        print("1. 初始化配置管理器...")
        config = ConfigManager()
        print("   ✓ 配置管理器初始化成功")
        
        print("2. 初始化文档转换器...")
        converter = DocumentConverter(config)
        print("   ✓ 文档转换器初始化成功")
        
        # 创建测试文件
        print("3. 创建测试文件...")
        test_dir, txt_file, md_file = create_test_files()
        print(f"   ✓ 测试文件创建成功: {test_dir}")
        
        # 测试文本到Markdown转换
        print("4. 测试 TXT -> MD 转换...")
        try:
            output_path = converter.convert_file(str(txt_file), '.md', str(test_dir))
            if os.path.exists(output_path):
                print(f"   ✓ 转换成功: {output_path}")
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"   内容预览: {content[:100]}...")
            else:
                print(f"   ✗ 转换失败: 输出文件不存在")
        except Exception as e:
            print(f"   ✗ 转换失败: {e}")
        
        # 测试Markdown到HTML转换
        print("5. 测试 MD -> HTML 转换...")
        try:
            output_path = converter.convert_file(str(md_file), '.html', str(test_dir))
            if os.path.exists(output_path):
                print(f"   ✓ 转换成功: {output_path}")
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"   内容预览: {content[:100]}...")
            else:
                print(f"   ✗ 转换失败: 输出文件不存在")
        except Exception as e:
            print(f"   ✗ 转换失败: {e}")
        
        # 检查依赖
        print("6. 检查系统依赖...")
        try:
            import subprocess
            result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"   ✓ Pandoc 可用: {version}")
            else:
                print(f"   ✗ Pandoc 不可用")
        except FileNotFoundError:
            print(f"   ✗ Pandoc 未安装")
        
        # 检查Python依赖
        print("7. 检查Python依赖...")
        required_packages = ['pypdf', 'pdfplumber', 'openpyxl', 'pandas']
        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✓ {package} 已安装")
            except ImportError:
                print(f"   ✗ {package} 未安装")
        
    except Exception as e:
        print(f"诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversion()