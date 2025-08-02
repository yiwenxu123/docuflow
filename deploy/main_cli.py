#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 命令行版本文档转换器
避免GUI相关问题的简化版本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    failed_files = []  # 记录失败的文件
    
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
                failed_files.append((os.path.basename(file_path), error))
        
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ 错误: {error_msg}")
            failed_files.append((os.path.basename(file_path), error_msg))
    
    # 显示详细的转换结果
    print("=" * 60)
    total_files = len(supported_files)
    failed_count = len(failed_files)
    
    if success_count == total_files:
        # 全部成功
        print(f"🎉 批量转换完成！")
        print(f"✅ 成功转换了全部 {success_count} 个文件")
        print(f"📁 输出目录: {output_dir}")
    elif success_count > 0:
        # 部分成功
        print(f"⚠️  批量转换完成，但有部分文件转换失败")
        print(f"✅ 成功转换: {success_count} 个文件")
        print(f"❌ 转换失败: {failed_count} 个文件")
        print(f"📁 输出目录: {output_dir}")
        
        if failed_files:
            print(f"\n失败的文件列表:")
            for i, (filename, error) in enumerate(failed_files, 1):
                print(f"  {i}. {filename} - {error}")
                if i >= 10 and len(failed_files) > 10:
                    print(f"     ... 还有 {len(failed_files) - 10} 个失败文件")
                    break
    else:
        # 全部失败
        print(f"❌ 批量转换失败")
        print(f"所有 {total_files} 个文件都转换失败")
        print(f"\n失败原因分析:")
        if failed_files:
            for i, (filename, error) in enumerate(failed_files, 1):
                print(f"  {i}. {filename} - {error}")
                if i >= 5 and len(failed_files) > 5:
                    print(f"     ... 还有 {len(failed_files) - 5} 个失败文件")
                    break
        print(f"\n建议检查:")
        print(f"  • 文件格式是否为支持的类型")
        print(f"  • 文件是否损坏或被占用")
        print(f"  • 是否有足够的磁盘空间")
        print(f"  • 是否安装了 pandoc 工具")
    
    print("=" * 60)

def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) == 3:
        # 命令行模式：python main_cli.py input_file output_file
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        print_banner()
        print(f"命令行模式转换:")
        print(f"输入文件: {input_file}")
        print(f"输出文件: {output_file}")
        print("-" * 40)
        
        if not os.path.exists(input_file):
            print(f"❌ 错误: 输入文件不存在 - {input_file}")
            sys.exit(1)
        
        try:
            converter = DocumentConverter()
            result = converter.convert_file(input_file, output_file)
            print(f"✅ 转换成功: {result}")
            sys.exit(0)
        except Exception as e:
            print(f"❌ 转换失败: {str(e)}")
            sys.exit(1)
    
    elif len(sys.argv) > 1:
        print("用法:")
        print("  交互模式: python main_cli.py")
        print("  命令行模式: python main_cli.py <输入文件> <输出文件>")
        sys.exit(1)
    
    # 交互模式
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