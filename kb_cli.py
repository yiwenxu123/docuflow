#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 素材投递 CLI（收缩版）

用法：
    # 投递到当前打开的 Obsidian vault 的 01-raw/inbox
    ./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理

    # 指定 vault 和目标子目录
    ./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 \
        --vault ~/Documents/我的123 --dest 01-raw/inbox

    # 优先使用 MarkItDown
    ./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 --markitdown
"""

import argparse
import os
import sys

from converter.kb_pipeline import (
    KnowledgeBasePipeline,
    default_vault_dest,
    detect_obsidian_vault,
)


def cmd_ingest(args) -> int:
    """把文件或目录转换后投递到 Obsidian vault"""
    vault_dir = args.vault or detect_obsidian_vault()
    if not vault_dir:
        print("未检测到 Obsidian vault，请用 --vault 指定路径", file=sys.stderr)
        return 1

    vault_dir = os.path.expanduser(vault_dir)
    if not os.path.isdir(vault_dir):
        print(f"目标路径不存在: {vault_dir}", file=sys.stderr)
        return 1

    dest = args.dest or default_vault_dest(vault_dir)
    pipeline = KnowledgeBasePipeline()
    result = pipeline.ingest_to_vault(
        args.source, vault_dir, dest_subdir=dest, use_markitdown=args.markitdown
    )

    print(f"投递完成: {len(result['converted'])}/{result['total_files']} 个文件")
    print(f"目标: {result['output_dir']}")
    if result["failed"]:
        print(f"{len(result['failed'])} 个文件失败:", file=sys.stderr)
        for item in result["failed"]:
            print(f"  - {item['file']}: {item['error']}", file=sys.stderr)
        return 1
    if result["total_files"] == 0:
        print("没有找到支持的文件", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DocuFlow 知识库投递")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="转换并投递到 Obsidian vault")
    p_ingest.add_argument("source", help="源文件或目录")
    p_ingest.add_argument("--vault", help="Obsidian vault 路径（缺省自动检测）")
    p_ingest.add_argument("--dest", help="vault 内目标子目录（缺省 01-raw/inbox）")
    p_ingest.add_argument("--markitdown", action="store_true", help="优先使用 MarkItDown")
    p_ingest.set_defaults(func=cmd_ingest)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
