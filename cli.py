#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 非交互式转换 CLI

用法：
    ./venv/bin/python3 cli.py input.docx -f .md
    ./venv/bin/python3 cli.py a.pdf b.docx -f .md -o output_dir/
"""

import argparse
import sys
from pathlib import Path

from converter.document_converter import DocumentConverter
from utils.file_utils import is_supported_file


def main() -> int:
    parser = argparse.ArgumentParser(description="DocuFlow 文档转换")
    parser.add_argument("input", nargs="*", help="输入文件（支持多个）")
    parser.add_argument("-o", "--output", help="输出文件路径或目录")
    parser.add_argument("-f", "--format", help="目标格式（如 .md, .html, .txt, .docx）")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        return 1

    input_paths = [Path(p) for p in args.input]
    missing = [p for p in input_paths if not p.exists()]
    if missing:
        print(f"错误: 输入文件不存在: {missing[0]}", file=sys.stderr)
        return 1

    unsupported = [p for p in input_paths if not is_supported_file(str(p))]
    if unsupported:
        print(f"错误: 不支持的文件格式: {unsupported[0].suffix}", file=sys.stderr)
        return 1

    batch_mode = len(input_paths) > 1
    output_path = Path(args.output) if args.output else None
    output_is_dir = bool(
        output_path
        and (batch_mode or output_path.is_dir() or str(args.output).endswith(("/", "\\")))
    )

    if batch_mode and (not output_path or not output_is_dir):
        print("错误: 批量转换必须指定输出目录（-o 目录路径）", file=sys.stderr)
        return 1

    if not batch_mode and output_path is None:
        if not args.format:
            print("错误: 需要指定输出格式或输出文件", file=sys.stderr)
            return 1
        output_path = input_paths[0].with_suffix(args.format)

    if output_is_dir and output_path is not None:
        output_path.mkdir(parents=True, exist_ok=True)

    if args.format:
        target_format = args.format if args.format.startswith(".") else f".{args.format}"
    elif output_path is not None:
        target_format = output_path.suffix
    else:
        print("错误: 批量转换需要指定目标格式（-f）", file=sys.stderr)
        return 1

    try:
        converter = DocumentConverter()
    except Exception as e:
        print(f"初始化转换器失败: {e}", file=sys.stderr)
        return 1

    failed = []
    for input_path in input_paths:
        out = (
            output_path / f"{input_path.stem}{target_format}"
            if output_is_dir and output_path is not None
            else output_path
        )
        if args.verbose:
            print(f"输入: {input_path}")
            print(f"输出: {out}")
        try:
            result_path = converter.convert_file(str(input_path), str(out), target_format)
            print(result_path)
        except Exception as e:
            print(f"转换失败: {input_path} - {e}", file=sys.stderr)
            failed.append(str(input_path))

    if failed:
        print(f"共 {len(failed)} 个文件转换失败", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
