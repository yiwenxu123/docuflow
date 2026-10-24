#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 知识库投递 CLI

用法：
    ./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理
    ./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 --dry-run --json
    ./venv/bin/python3 kb_cli.py status
    ./venv/bin/python3 kb_cli.py doctor
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from converter.kb_pipeline import (
    KnowledgeBasePipeline,
    default_vault_dest,
    detect_obsidian_vault,
)
from converter.markitdown_integration import get_markitdown_integration
from converter.state import StateStore, default_state_db_path


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_ingest(args) -> int:
    vault_dir = args.vault or detect_obsidian_vault()
    if not vault_dir:
        print("未检测到 Obsidian vault，请用 --vault 指定路径", file=sys.stderr)
        return 2

    vault_dir = os.path.expanduser(vault_dir)
    if not os.path.isdir(vault_dir):
        print(f"目标路径不存在: {vault_dir}", file=sys.stderr)
        return 2

    dest = args.dest or default_vault_dest(vault_dir)
    try:
        pipeline = KnowledgeBasePipeline()
        result = pipeline.ingest_to_vault(
            args.source,
            vault_dir,
            dest_subdir=dest,
            use_markitdown=args.markitdown,
            dry_run=args.dry_run,
            allow_duplicate=args.allow_duplicate,
        )
    except Exception as e:
        print(f"投递失败: {e}", file=sys.stderr)
        return 2

    if args.json:
        _print_json(result)
    else:
        action = "预演完成" if result["dry_run"] else "投递完成"
        print(
            f"{action}: {len(result['converted'])} 转换, "
            f"{len(result['skipped'])} 跳过, "
            f"{len(result['planned'])} 待处理, "
            f"{len(result['failed'])} 失败 / 共 {result['total_files']} 个文件"
        )
        print(f"目标: {result['output_dir']}")
        for item in result["skipped"][:5]:
            print(f"  跳过: {Path(item['file']).name} ({item['reason']})")
        for item in result["failed"]:
            print(f"  失败: {item['file']}: {item['error']}", file=sys.stderr)

    if result["total_files"] == 0:
        print("没有找到支持的文件", file=sys.stderr)
        return 1
    return 1 if result["failed"] else 0


def cmd_status(args) -> int:
    try:
        state = StateStore()
        summary = state.summary()
    except Exception as e:
        print(f"状态库不可用: {e}", file=sys.stderr)
        return 2

    vault_dir = args.vault or detect_obsidian_vault()
    if vault_dir:
        summary["vault"] = os.path.expanduser(vault_dir)
        summary["dest"] = args.dest or default_vault_dest(summary["vault"])

    if args.json:
        _print_json(summary)
        return 0

    docs = summary["documents"]
    print(f"状态库: {summary['db_path']}")
    print(f"文档记录: 成功 {docs['success']} | 失败 {docs['failed']} | 总计 {docs['total']}")
    if summary.get("vault"):
        print(f"当前 vault: {summary['vault']} -> {summary['dest']}")

    last = summary.get("last_run")
    if last:
        print(
            f"最近运行 #{last['id']}: "
            f"{last.get('converted', 0)} 转换 / "
            f"{last.get('skipped', 0)} 跳过 / "
            f"{last.get('failed', 0)} 失败"
        )
    for item in summary["recent_failures"]:
        print(f"  失败: {item['source_path']}: {item['error']}")
    return 0


def cmd_doctor(args) -> int:
    vault_dir = args.vault or detect_obsidian_vault()
    dest = args.dest or (default_vault_dest(vault_dir) if vault_dir else "")
    markitdown = get_markitdown_integration()

    try:
        state_db = {
            "available": True,
            "path": str(StateStore().db_path),
            "required": False,
        }
    except Exception as e:
        state_db = {
            "available": False,
            "path": str(default_state_db_path()),
            "required": False,
            "error": str(e),
        }

    checks = {
        "pandoc": {
            "available": shutil.which("pandoc") is not None,
            "path": shutil.which("pandoc") or "",
            "required": True,
        },
        "markitdown": {
            "available": markitdown.is_available(),
            "path": markitdown.markitdown_cmd,
            "required": False,
        },
        "docling": {
            "available": shutil.which("docling") is not None,
            "required": False,
        },
        "ocrmypdf": {
            "available": shutil.which("ocrmypdf") is not None,
            "required": False,
        },
        "vault": {
            "available": bool(vault_dir and Path(vault_dir).is_dir()),
            "path": vault_dir or "",
            "required": True,
        },
        "dest": {
            "available": bool(vault_dir and os.access(vault_dir, os.W_OK)),
            "path": str(Path(vault_dir) / dest) if vault_dir else "",
            "required": True,
        },
        "state_db": state_db,
    }

    ok = all(item["available"] for item in checks.values() if item["required"])
    result = {"ok": ok, "checks": checks}

    if args.json:
        _print_json(result)
    else:
        print(f"整体状态: {'可用' if ok else '需要处理'}")
        for name, item in checks.items():
            status = "可用" if item["available"] else ("缺失" if item["required"] else "未安装（可选）")
            print(f"  {name}: {status}" + (f" ({item['path']})" if item.get("path") else ""))
    return 0 if ok else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="DocuFlow 知识库投递")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="转换并投递到 Obsidian vault")
    p_ingest.add_argument("source", help="源文件或目录")
    p_ingest.add_argument("--vault", help="Obsidian vault 路径（缺省自动检测）")
    p_ingest.add_argument("--dest", help="vault 内目标子目录（缺省 01-raw/inbox）")
    p_ingest.add_argument("--markitdown", action="store_true", help="优先使用 MarkItDown")
    p_ingest.add_argument("--dry-run", action="store_true", help="只预演，不写文件、不写状态")
    p_ingest.add_argument("--allow-duplicate", action="store_true", help="跳过哈希去重（仍不覆盖）")
    p_ingest.add_argument("--json", action="store_true", help="输出 JSON 报告")
    p_ingest.set_defaults(func=cmd_ingest)

    p_status = sub.add_parser("status", help="查看投递状态与最近运行")
    p_status.add_argument("--vault", help="Obsidian vault 路径（缺省自动检测）")
    p_status.add_argument("--dest", help="vault 内目标子目录")
    p_status.add_argument("--json", action="store_true", help="输出 JSON")
    p_status.set_defaults(func=cmd_status)

    p_doctor = sub.add_parser("doctor", help="检查运行环境")
    p_doctor.add_argument("--vault", help="Obsidian vault 路径（缺省自动检测）")
    p_doctor.add_argument("--dest", help="vault 内目标子目录")
    p_doctor.add_argument("--json", action="store_true", help="输出 JSON")
    p_doctor.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
