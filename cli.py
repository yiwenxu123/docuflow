#!/usr/bin/env python3
"""
DocuFlow 命令行工具 - 非交互式 + 交互式
"""

import argparse
import os
import sys
from pathlib import Path
from converter.document_converter import DocumentConverter
from utils.file_utils import get_supported_formats, is_supported_file


def interactive_mode():
    """交互式向导（原 main_cli.py 功能）"""
    from utils.file_utils import get_supported_formats
    import shutil

    print("=" * 50)
    print("  DocuFlow 文档转换器 - 交互模式")
    print("=" * 50)

    formats = get_supported_formats()
    format_map = {'.html': 'HTML', '.md': 'Markdown', '.txt': 'TXT', '.docx': 'Word', '.pdf': 'PDF'}
    print("\n支持的输入格式:", ", ".join(formats))

    def pick_output_format(input_file=None):
        """选择输出格式；提供输入文件时仅显示可用的转换目标"""
        converter = DocumentConverter()
        choices = list(format_map.items())
        if input_file:
            src_ext = Path(input_file).suffix.lower()
            choices = [(ext, name) for ext, name in choices
                       if converter.can_convert(src_ext, ext)]
            if not choices:
                print(f"错误: 该文件（{src_ext}）没有可用的转换格式")
                return None
        print("\n选择输出格式:")
        for i, (ext, name) in enumerate(choices, 1):
            print(f"  {i}. {name}")
        choice = input(f"请选择 (1-{len(choices)}): ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(choices)):
            print("错误: 无效的选择")
            return None
        return choices[int(choice) - 1][0]

    while True:
        print("\n请选择操作:")
        print("1. 转换单个文件")
        print("2. 批量转换文件夹")
        print("3. 查看支持的格式")
        print("4. 退出程序")
        choice = input("请选择 (1-4): ").strip()

        if choice == "4":
            print("再见！")
            return 0

        if choice == "3":
            print("\n支持的输入格式:", ", ".join(formats))
            continue

        converter = DocumentConverter()

        if choice == "1":
            input_file = input("请输入文件路径: ").strip()
            if not input_file or not os.path.exists(input_file):
                print(f"错误: 文件不存在 - {input_file}")
                continue
            if not is_supported_file(input_file):
                print(f"错误: 不支持的文件格式 - {input_file}")
                continue

            output_format = pick_output_format()
            if not output_format:
                continue

            output_dir = input("请输入输出目录 (留空使用输入目录): ").strip() or os.path.dirname(input_file)
            try:
                result = converter.convert_file(input_file, output_format, output_dir)
                print(f"✓ 转换成功: {result}")
            except Exception as e:
                print(f"✗ 转换失败: {e}")

        elif choice == "2":
            input_dir = input("请输入包含文件的目录路径: ").strip()
            if not input_dir or not os.path.exists(input_dir):
                print(f"错误: 目录不存在 - {input_dir}")
                continue

            supported_files = [
                str(p) for p in Path(input_dir).rglob("*")
                if p.is_file() and is_supported_file(str(p))
            ]
            if not supported_files:
                print(f"在目录 {input_dir} 中未找到支持的文件")
                continue

            print(f"\n找到 {len(supported_files)} 个支持的文件:")
            for i, f in enumerate(supported_files[:10], 1):
                print(f"  {i}. {os.path.basename(f)}")
            if len(supported_files) > 10:
                print(f"  ... 还有 {len(supported_files) - 10} 个文件")

            output_format = pick_output_format()
            if not output_format:
                continue

            output_dir = input("请输入输出目录 (留空使用输入目录): ").strip() or input_dir
            os.makedirs(output_dir, exist_ok=True)

            success_count, failed = 0, []
            for i, f in enumerate(supported_files, 1):
                print(f"[{i}/{len(supported_files)}] 转换: {os.path.basename(f)}")
                try:
                    result = converter.convert_file(f, output_format, output_dir)
                    print(f"  ✓ 成功: {os.path.basename(result)}")
                    success_count += 1
                except Exception as e:
                    print(f"  ✗ 失败: {e}")
                    failed.append(os.path.basename(f))

            print("=" * 50)
            print(f"批量转换完成: 成功 {success_count}/{len(supported_files)}")
            if failed:
                print("失败文件:")
                for f in failed:
                    print(f"  • {f}")
            print("=" * 50)

        else:
            print("错误: 无效的选择，请输入 1-4")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='DocuFlow - 文档转换器')
    parser.add_argument('input', nargs='*', help='输入文件路径（支持多个，批量转换）')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互式模式')
    parser.add_argument('-o', '--output', help='输出文件路径或目录（批量时必填目录）')
    parser.add_argument('-f', '--format', help='目标格式（如 .html, .md, .txt）')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 交互模式（无参数或 -i）
    if args.interactive or (not args.input and not args.output):
        return interactive_mode()
    
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