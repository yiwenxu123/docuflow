#!/usr/bin/env python3
"""
DocuFlow 命令行工具 - 非交互式版本
"""

import argparse
import os
import sys
from pathlib import Path
from converter.document_converter import DocumentConverter

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='DocuFlow - 文档转换器')
    parser.add_argument('input', nargs='+', help='输入文件路径（支持多个，批量转换）')
    parser.add_argument('-o', '--output', help='输出文件路径或目录（批量时必填目录）')
    parser.add_argument('-f', '--format', help='目标格式（如 .html, .md, .txt）')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    input_paths = [Path(p) for p in args.input]
    missing = [p for p in input_paths if not p.exists()]
    if missing:
        print(f"错误: 输入文件不存在: {missing[0]}", file=sys.stderr)
        sys.exit(1)
    
    batch_mode = len(input_paths) > 1
    if args.output:
        output_path = Path(args.output)
        output_is_dir = batch_mode or output_path.is_dir() or str(args.output).endswith(('/', os.sep))
    else:
        output_path = None
        output_is_dir = False
    
    # 批量模式必须有输出目录
    if batch_mode and (not args.output or not output_is_dir):
        print("错误: 批量转换必须指定输出目录（-o 目录路径）", file=sys.stderr)
        sys.exit(1)
    
    # 单文件模式：无输出路径时，使用输入文件名加新扩展名
    if not batch_mode and output_path is None:
        if args.format:
            output_path = input_paths[0].with_suffix(args.format)
        else:
            print("错误: 需要指定输出格式或输出文件", file=sys.stderr)
            sys.exit(1)
    
    if output_is_dir and output_path is not None:
        output_path.mkdir(parents=True, exist_ok=True)
    
    # 确定目标格式
    if args.format:
        target_format = args.format if args.format.startswith('.') else f".{args.format}"
    elif not batch_mode and output_path is not None:
        target_format = output_path.suffix
    else:
        print("错误: 批量转换需要指定目标格式（-f）", file=sys.stderr)
        sys.exit(1)
    
    if args.verbose:
        for p in input_paths:
            print(f"输入文件: {p}")
        print(f"目标格式: {target_format}")
        print(f"输出目录: {output_path if output_is_dir else '自动'}")
    
    try:
        converter = DocumentConverter()
    except Exception as e:
        print(f"❌ 初始化转换器失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    failed = []
    for input_path in input_paths:
        if output_is_dir and output_path is not None:
            out = output_path / f"{input_path.stem}{target_format}"
        else:
            out = output_path
        if args.verbose:
            print(f"输入文件: {input_path}")
            print(f"输出文件: {out}")
        try:
            result_path = converter.convert_file(
                str(input_path), str(out), target_format
            )
            if result_path:
                if args.verbose:
                    print(f"✅ 转换成功: {result_path}")
                else:
                    print(result_path)
            else:
                print(f"❌ 转换失败: {input_path} (未知错误)", file=sys.stderr)
                failed.append(str(input_path))
        except Exception as e:
            print(f"❌ 转换失败: {input_path} - {e}", file=sys.stderr)
            failed.append(str(input_path))
    
    if failed:
        print(f"共 {len(failed)} 个文件转换失败", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()