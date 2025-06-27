#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 命令行版本文档转换器
用于测试核心转换功能
"""

import os
import sys
import argparse
from converter.document_converter import DocumentConverter
from utils.file_utils import is_supported_file, get_supported_formats

def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description="DocuFlow 文档转换器 - 命令行版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python cli_converter.py input.md -f .pdf
  python cli_converter.py input.docx -f .html -o /path/to/output
  python cli_converter.py *.md -f .pdf
        """
    )
    
    parser.add_argument('files', nargs='+', help='要转换的文件路径')
    parser.add_argument('-f', '--format', required=True, 
                       choices=['.pdf', '.md', '.docx', '.html'],
                       help='输出格式')
    parser.add_argument('-o', '--output', help='输出目录（默认为源文件目录）')
    parser.add_argument('--keep-name', action='store_true', 
                       help='保留原文件名（默认添加格式后缀）')
    parser.add_argument('--list-formats', action='store_true',
                       help='显示支持的格式')
    
    args = parser.parse_args()
    
    # 显示支持的格式
    if args.list_formats:
        formats = get_supported_formats()
        print("支持的输入格式:")
        for ext, desc in formats.items():
            print(f"  {ext} - {desc}")
        print("\n支持的输出格式: .pdf, .md, .docx, .html")
        return
    
    # 检查文件
    valid_files = []
    for file_path in args.files:
        if os.path.exists(file_path) and is_supported_file(file_path):
            valid_files.append(file_path)
        else:
            print(f"⚠️  跳过文件: {file_path} (不存在或不支持的格式)")
    
    if not valid_files:
        print("❌ 没有找到有效的文件")
        return 1
    
    # 创建转换器
    try:
        converter = DocumentConverter()
    except Exception as e:
        print(f"❌ 转换器初始化失败: {e}")
        return 1
    
    # 执行转换
    print(f"🚀 开始转换 {len(valid_files)} 个文件...")
    success_count = 0
    
    for file_path in valid_files:
        try:
            print(f"📄 转换: {os.path.basename(file_path)}")
            output_file = converter.convert_file(
                file_path, 
                args.format, 
                args.output, 
                args.keep_name
            )
            
            if output_file:
                print(f"✅ 成功: {output_file}")
                success_count += 1
            else:
                print(f"❌ 失败: {file_path}")
                
        except Exception as e:
            print(f"❌ 错误: {file_path} - {e}")
    
    print(f"\n📊 转换完成: {success_count}/{len(valid_files)} 成功")
    
    if success_count > 0:
        output_dir = args.output or os.path.dirname(valid_files[0])
        print(f"📁 输出目录: {output_dir}")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())