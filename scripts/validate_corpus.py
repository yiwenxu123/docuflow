#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5 验证脚本：用真实文件跑两轮投递，统计可用率与幂等性。

用法：
    ./venv/bin/python3 scripts/validate_corpus.py \
        --manifest archive/phase5/manifest.txt \
        --output archive/phase5/report-$(date +%Y%m%d-%H%M%S)

所有输出写入临时 vault，不会碰真实知识库。
"""

import argparse
import hashlib
import json
import re
import statistics
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from converter.document_converter import DocumentConverter
from converter.frontmatter import split_frontmatter
from converter.kb_pipeline import KnowledgeBasePipeline
from converter.state import StateStore


def read_manifest(path: Path, limit: int) -> List[Path]:
    files = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = Path(line).expanduser()
        if p.is_file():
            files.append(p)
    return files[:limit] if limit else files


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path) -> Dict[str, str]:
    if not root.exists():
        return {}
    return {
        str(p.relative_to(root)): sha256_file(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def analyze_output(path: Path, min_chars: int) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = split_frontmatter(text)
    body = body or text
    stripped = body.strip()
    chars = len(stripped)
    nonempty = [line for line in body.splitlines() if line.strip()]
    unique = len(set(nonempty))
    duplicate_ratio = 1 - (unique / len(nonempty)) if nonempty else 0

    engine = ""
    attachments = 0
    if frontmatter:
        match = re.search(r'^engine:\s*"?([^"\n]+)"?', frontmatter, re.M)
        if match:
            engine = match.group(1).strip()
        match = re.search(r"^attachments:\s*(\d+)", frontmatter, re.M)
        if match:
            attachments = int(match.group(1))

    replacement = body.count("\ufffd")
    metrics = {
        "chars": chars,
        "lines": len(nonempty),
        "headings": len(re.findall(r"^#{1,6}\s+\S", body, re.M)),
        "page_headers": len(re.findall(r"^## 第 \d+ 页", body, re.M)),
        "table_headers": body.count("### 表格"),
        "replacement": replacement,
        "duplicate_ratio": round(duplicate_ratio, 3),
        "frontmatter": bool(text.startswith("---\n")),
        "engine": engine,
        "attachments": attachments,
        "snippet": stripped[:500],
    }
    metrics["usable"] = (
        chars >= min_chars
        and metrics["frontmatter"]
        and replacement <= max(3, chars // 100)
    )
    metrics["noisy"] = (
        metrics["page_headers"] >= 3
        or metrics["table_headers"] >= 3
        or duplicate_ratio > 0.4
    )
    return metrics


def classify_failure(error: str) -> str:
    text = error.lower()
    if "ocr" in text:
        return "ocr_needed"
    if "转换结果为空" in error:
        return "empty_output"
    if "不支持" in error or "unsupported" in text:
        return "unsupported_format"
    if "pandoc" in text:
        return "pandoc_error"
    if "超时" in error or "timeout" in text:
        return "timeout"
    return "other"


def run_pass(pipeline: KnowledgeBasePipeline, files: List[Path], vault: Path,
             use_markitdown: bool, ocr_mode: str) -> List[Dict[str, Any]]:
    results = []
    for path in files:
        start = time.perf_counter()
        try:
            result = pipeline.ingest_to_vault(
                [str(path)],
                str(vault),
                dest_subdir="01-raw/inbox",
                use_markitdown=use_markitdown,
                ocr_mode=ocr_mode,
            )
            error = result["failed"][0]["error"] if result["failed"] else ""
            status = "failed" if result["failed"] else (
                "skipped" if result["skipped"] else "converted"
            )
        except Exception as e:
            result = {"converted": [], "skipped": [], "failed": [{"error": str(e)}]}
            error = str(e)
            status = "failed"
        outputs = list(result.get("converted") or [])
        if not outputs and result.get("skipped"):
            outputs = [result["skipped"][0].get("output")]
        results.append({
            "file": str(path),
            "status": status,
            "duration": round(time.perf_counter() - start, 3),
            "output": outputs[0] if outputs else None,
            "error": error,
        })
    return results


def write_reports(report: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary = report["summary"]
    lines = [
        "# DocuFlow Phase 5 验证报告",
        "",
        f"- 时间：{report['started_at']}",
        f"- 文件数：{summary['total']}",
        f"- 成功转换：{summary['converted']}",
        f"- 跳过：{summary['skipped']}",
        f"- 失败：{summary['failed']}",
        f"- 自动可用率：{summary['usable_rate']}%",
        f"- 干净可用率（无页头/表格重复）：{summary['clean_usable_rate']}%",
        f"- 低内容页面：{summary['quality_issues']['low_content']}",
        f"- 噪声页面：{summary['quality_issues']['noisy']}",
        f"- 二次投递全部跳过：{summary['idempotent']}",
        f"- 平均耗时：{summary['avg_duration']}s，中位数：{summary['median_duration']}s",
        f"- 失败类型：{json.dumps(summary['failure_types'], ensure_ascii=False)}",
        "",
        "## 按格式",
        "",
        "| 格式 | 总数 | 成功 | 可用 | 失败 |",
        "|---|---:|---:|---:|---:|",
    ]
    for ext, data in sorted(report["by_ext"].items()):
        lines.append(
            f"| {ext} | {data['total']} | {data['converted']} | "
            f"{data['usable']} | {data['failed']} |"
        )

    lines += [
        "",
        "## 文件明细",
        "",
        "| # | 文件 | 格式 | 状态 | 可用 | 噪声 | 字符 | 耗时 | 引擎/错误 |",
        "|---:|---|---|---|---|---|---:|---:|---|",
    ]
    for i, item in enumerate(report["files"], 1):
        metrics = item.get("metrics", {})
        detail = metrics.get("engine") or item.get("error", "")
        lines.append(
            f"| {i} | {Path(item['file']).name} | {item['ext']} | {item['status']} | "
            f"{metrics.get('usable', '-')} | {metrics.get('noisy', '-')} | "
            f"{metrics.get('chars', '-')} | {item['duration']}s | {detail} |"
        )

    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    review = ["# 人工复核摘要", ""]
    for i, item in enumerate(report["files"], 1):
        review.append(f"## {i}. {Path(item['file']).name}")
        review.append(f"- 状态：{item['status']}，可用：{item.get('metrics', {}).get('usable')}")
        review.append(f"- 错误：{item.get('error') or '无'}")
        snippet = item.get("metrics", {}).get("snippet", "")
        if snippet:
            review.append("")
            review.append("```text")
            review.append(snippet.replace("```", "` ` `"))
            review.append("```")
        review.append("")
    (output_dir / "review.md").write_text("\n".join(review), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="DocuFlow 真实文件验证")
    parser.add_argument("--manifest", required=True, help="每行一个文件路径")
    parser.add_argument("--output", help="报告输出目录")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--min-chars", type=int, default=40)
    parser.add_argument("--markitdown", action="store_true")
    parser.add_argument("--ocr", choices=["auto", "off"], default="auto")
    args = parser.parse_args()

    files = read_manifest(Path(args.manifest), args.limit)
    if not files:
        print("清单中没有可用文件")
        return 1

    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    output_dir = Path(args.output) if args.output else (
        Path(__file__).resolve().parent.parent / "archive" / "phase5" /
        datetime.now().strftime("report-%Y%m%d-%H%M%S")
    )

    with tempfile.TemporaryDirectory(prefix="docuflow_validate_") as tmp:
        vault = Path(tmp) / "vault"
        (vault / "01-raw" / "inbox").mkdir(parents=True)
        state = StateStore(Path(tmp) / "state.db")
        pipeline = KnowledgeBasePipeline(
            converter=DocumentConverter(), state=state
        )

        first = run_pass(pipeline, files, vault, args.markitdown, args.ocr)
        before = snapshot(vault / "01-raw" / "inbox")
        second = run_pass(pipeline, files, vault, args.markitdown, args.ocr)
        after = snapshot(vault / "01-raw" / "inbox")

        records = []
        by_ext = defaultdict(lambda: {"total": 0, "converted": 0, "usable": 0, "failed": 0})
        failure_types = Counter()

        for item in first:
            path = Path(item["file"])
            ext = path.suffix.lower() or "(none)"
            metrics = {}
            if item["output"] and Path(item["output"]).exists():
                metrics = analyze_output(Path(item["output"]), args.min_chars)
            if item["status"] == "failed":
                failure_types[classify_failure(item["error"])] += 1

            record = {
                **item,
                "ext": ext,
                "size": path.stat().st_size,
                "metrics": metrics,
                "low_content": bool(
                    metrics
                    and not metrics.get("usable")
                    and metrics.get("chars", 0) < args.min_chars
                ),
            }
            records.append(record)
            by_ext[ext]["total"] += 1
            if item["status"] == "converted":
                by_ext[ext]["converted"] += 1
            if metrics.get("usable"):
                by_ext[ext]["usable"] += 1
            if item["status"] == "failed":
                by_ext[ext]["failed"] += 1

        converted = sum(1 for r in records if r["status"] == "converted")
        skipped = sum(1 for r in records if r["status"] == "skipped")
        failed = sum(1 for r in records if r["status"] == "failed")
        usable = sum(1 for r in records if r["metrics"].get("usable"))
        noisy = sum(
            1 for r in records
            if r["metrics"].get("usable") and r["metrics"].get("noisy")
        )
        low_content = sum(1 for r in records if r["low_content"])
        clean_usable = usable - noisy
        durations = [r["duration"] for r in records]
        second_converted = sum(1 for r in second if r["status"] == "converted")
        second_skipped = sum(1 for r in second if r["status"] == "skipped")
        second_failed = sum(1 for r in second if r["status"] == "failed")

        report = {
            "started_at": started_at,
            "manifest": str(Path(args.manifest).resolve()),
            "markitdown": args.markitdown,
            "ocr_mode": args.ocr,
            "summary": {
                "total": len(records),
                "converted": converted,
                "skipped": skipped,
                "failed": failed,
                "usable": usable,
                "usable_rate": round(usable / len(records) * 100, 1),
                "clean_usable": clean_usable,
                "clean_usable_rate": round(clean_usable / len(records) * 100, 1),
                "noisy_usable": noisy,
                "quality_issues": {
                    "low_content": low_content,
                    "noisy": noisy,
                },
                "failure_types": dict(failure_types),
                "avg_duration": round(statistics.mean(durations), 2),
                "median_duration": round(statistics.median(durations), 2),
                "second_pass_converted": second_converted,
                "second_pass_skipped": second_skipped,
                "second_pass_failed": second_failed,
                "idempotent": second_converted == 0 and before == after,
                "output_files": len(after),
            },
            "by_ext": dict(by_ext),
            "files": records,
        }

    write_reports(report, output_dir)
    summary = report["summary"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"报告目录: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
