#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 命令行版本文档转换器
避免GUI相关问题的简化版本
"""

import os
import sys
from pathlib import Path
from converter.document_converter import DocumentConverter
from utils.file_utils import get_supported_formats, is_supported_file

def print_banner():
    """打印程序横幅"""
    print("="*60)
    print("    DocuFlow - 文档转换器 (命令行版本)")
    print("="*60)
    print()

def print_supported_formats():
    """打印支持的格式"""
    formats = get_supported_formats()
    print("支持的输入格式:")
    for category, exts in formats.items():
        print(f"  {category}: {', '.join(exts)}")
    print()
    print("支持的输出格式: HTML, Markdown, TXT")
    print()

def convert_single_file():
    """转换单个文件"""
    print("=== 单文件转换 ===")
    
    # 获取输入文件
    input_file = input("请输入文件路径: ").strip()
    if not input_file:
        print("错误: 文件路径不能为空")
        return
    
    if not os.path.exists(input_file):
        print(f"错误: 文件不存在 - {input_file}")
        return
    
    if not is_supported_file(input_file):
        print(f"错误: 不支持的文件格式 - {input_file}")
        return
    
    # 获取输出格式
    print("\n选择输出格式:")
    print("1. HTML")
    print("2. Markdown")
    print("3. TXT")
    
    choice = input("请选择 (1-3): ").strip()
    format_map = {'1': 'html', '2': 'markdown', '3': 'txt'}
    
    if choice not in format_map:
        print("错误: 无效的选择")
        return
    
    output_format = format_map[choice]
    
    # 获取输出目录
    output_dir = input("请输入输出目录 (留空使用当前目录): ").strip()
    if not output_dir:
        output_dir = os.getcwd()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 执行转换
    print(f"\n正在转换: {input_file}")
    print(f"输出格式: {output_format.upper()}")
    print(f"输出目录: {output_dir}")
    print("-" * 40)
    
    try:
        converter = DocumentConverter()
        success, output_file, error = converter.convert_file(
            input_file, output_format, output_dir, keep_original_name=True
        )
        
        if success:
            print(f"✓ 转换成功: {output_file}")
        else:
            print(f"✗ 转换失败: {error}")
    
    except Exception as e:
        print(f"✗ 转换过程中发生错误: {str(e)}")

def convert_batch_files():
    """批量转换文件"""
    print("=== 批量文件转换 ===")
    
    # 获取输入目录
    input_dir = input("请输入包含文件的目录路径: ").strip()
    if not input_dir:
        print("错误: 目录路径不能为空")
        return
    
    if not os.path.exists(input_dir):
        print(f"错误: 目录不存在 - {input_dir}")
        return
    
    # 查找支持的文件
    supported_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if is_supported_file(file_path):
                supported_files.append(file_path)
    
    if not supported_files:
        print(f"在目录 {input_dir} 中未找到支持的文件")
        return
    
    print(f"\n找到 {len(supported_files)} 个支持的文件:")
    for i, file in enumerate(supported_files[:10], 1):  # 只显示前10个
        print(f"  {i}. {os.path.basename(file)}")
    if len(supported_files) > 10:
        print(f"  ... 还有 {len(supported_files) - 10} 个文件")
    
    # 获取输出格式
    print("\n选择输出格式:")
    print("1. HTML")
    print("2. Markdown")
    print("3. TXT")
    
    choice = input("请选择 (1-3): ").strip()
    format_map = {'1': 'html', '2': 'markdown', '3': 'txt'}
    
    if choice not in format_map:
        print("错误: 无效的选择")
        return
    
    output_format = format_map[choice]
    
    # 获取输出目录
    output_dir = input("请输入输出目录 (留空使用输入目录): ").strip()
    if not output_dir:
        output_dir = input_dir
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 执行批量转换
    print(f"\n开始批量转换 {len(supported_files)} 个文件...")
    print(f"输出格式: {output_format.upper()}")
    print(f"输出目录: {output_dir}")
    print("-" * 40)
    
    converter = DocumentConverter()
    success_count = 0
    
    for i, file_path in enumerate(supported_files, 1):
        print(f"[{i}/{len(supported_files)}] 转换: {os.path.basename(file_path)}")
        
        try:
            success, output_file, error = converter.convert_file(
                file_path, output_format, output_dir, keep_original_name=True
            )
            
            if success:
                print(f"  ✓ 成功: {os.path.basename(output_file)}")
                success_count += 1
            else:
                print(f"  ✗ 失败: {error}")
        
        except Exception as e:
            print(f"  ✗ 错误: {str(e)}")
    
    print("-" * 40)
    print(f"批量转换完成: {success_count}/{len(supported_files)} 个文件转换成功")

def main():
    """主函数"""
    print_banner()
    
    while True:
        print("请选择操作:")
        print("1. 查看支持的格式")
        print("2. 转换单个文件")
        print("3. 批量转换文件")
        print("4. 退出程序")
        print()
        
        choice = input("请输入选择 (1-4): ").strip()
        print()
        
        if choice == '1':
            print_supported_formats()
        elif choice == '2':
            convert_single_file()
        elif choice == '3':
            convert_batch_files()
        elif choice == '4':
            print("感谢使用 DocuFlow！")
            break
        else:
            print("无效的选择，请重新输入")
        
        print()
        input("按回车键继续...")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序发生错误: {str(e)}")
        sys.exit(1)