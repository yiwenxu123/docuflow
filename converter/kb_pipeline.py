#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库投递管道

流程：
1. 检测 Obsidian vault 与收件箱；
2. 扫描文件并计算 source hash；
3. 转换为 Markdown，计算 content hash；
4. 去重、生成 frontmatter、原子写入；
5. 记录 SQLite 状态并输出报告。

不覆盖任何已有文件；同名冲突追加内容哈希后缀。
"""

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import config as app_config
from converter.document_converter import DocumentConverter
from converter.frontmatter import (
    detect_language,
    extract_title,
    merge_frontmatter,
    render_frontmatter,
    split_frontmatter,
)
from converter.state import StateStore, now_iso, sha256_file, sha256_text

SUPPORTED_SOURCE_EXTS = {
    ".md", ".markdown", ".txt", ".html", ".htm",
    ".pdf", ".docx", ".xlsx",
}


def detect_obsidian_vault() -> Optional[str]:
    """检测当前打开的 Obsidian vault 路径"""
    obsidian_json = Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json"
    if not obsidian_json.exists():
        return None
    try:
        data = json.loads(obsidian_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    vaults = data.get("vaults", {})
    for vault in vaults.values():
        if vault.get("open") and vault.get("path"):
            return vault["path"]
    for vault in vaults.values():
        if vault.get("path"):
            return vault["path"]
    return None


def default_vault_dest(vault_dir: str) -> str:
    """优先使用 01-raw/inbox，不在 markitdown-output 之间隐式切换"""
    vault = Path(vault_dir)
    candidates = ["01-raw/inbox", "01-raw", "raw/sources", "Inbox"]
    for rel in candidates:
        if (vault / rel).exists():
            return rel
    return "01-raw/inbox"


def _sanitize_name(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")
    return cleaned[:80] or "document"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def _normalize_text(text: str) -> str:
    """轻量规范化：统一换行、压缩空行、去掉行尾空白，不删除正文内容"""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
    return normalized.strip() + "\n"


def _file_hash(path: Path) -> str:
    try:
        return sha256_text(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return ""


def _pdf_pages(path: Path) -> Optional[int]:
    if path.suffix.lower() != ".pdf":
        return None
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(path)).pages)
    except Exception:
        return None


class KnowledgeBasePipeline:
    """文档转换、去重并投递到 Obsidian vault"""

    def __init__(
        self,
        converter: Optional[DocumentConverter] = None,
        state: Optional[StateStore] = None,
    ):
        self.converter = converter or DocumentConverter()
        self.state = state or StateStore()

    def ingest_to_vault(
        self,
        source: Union[str, List[str]],
        vault_dir: str,
        dest_subdir: str = "",
        use_markitdown: bool = False,
        dry_run: bool = False,
        allow_duplicate: bool = False,
    ) -> Dict[str, Any]:
        """转换并投递文件或目录

        Args:
            source: 源文件或目录
            vault_dir: Obsidian vault 路径
            dest_subdir: vault 内目标子目录；留空自动选择
            use_markitdown: 优先使用 MarkItDown
            dry_run: 只预演，不写文件、不写状态
            allow_duplicate: 跳过哈希去重（仍不会覆盖文件）

        Returns:
            dict: converted / skipped / planned / failed / output_dir / run_id
        """
        vault = Path(vault_dir).expanduser()
        if not vault.is_dir():
            raise FileNotFoundError(f"vault 路径不存在: {vault}")

        dest_subdir = dest_subdir or default_vault_dest(str(vault))
        target = vault / dest_subdir
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)

        files = self._discover_files(source)
        run_id = None if dry_run else self.state.start_run()

        converted: List[str] = []
        skipped: List[Dict[str, str]] = []
        planned: List[Dict[str, str]] = []
        failed: List[Dict[str, str]] = []

        for src in files:
            source_hash = ""
            engine = self._engine_for(src, use_markitdown)
            try:
                source_hash = sha256_file(src)

                if not allow_duplicate:
                    existing = self.state.find_success_by_source(source_hash)
                    if existing and Path(existing["output_path"]).exists():
                        skipped.append({
                            "file": str(src),
                            "output": existing["output_path"],
                            "reason": "source hash already ingested",
                        })
                        continue

                existing_frontmatter, body = self._to_markdown(src, use_markitdown)
                if not body.strip():
                    raise ValueError("转换结果为空")
                content_hash = sha256_text(body)

                if not allow_duplicate:
                    existing = self.state.find_success_by_content(content_hash)
                    if existing and Path(existing["output_path"]).exists():
                        skipped.append({
                            "file": str(src),
                            "output": existing["output_path"],
                            "reason": "content hash already ingested",
                        })
                        continue

                title = extract_title(body, src.stem)
                meta = self._build_frontmatter(src, body, title, source_hash, content_hash, engine)
                if existing_frontmatter is not None:
                    final_text = merge_frontmatter(existing_frontmatter, meta) + body
                else:
                    final_text = render_frontmatter(meta) + body
                final_hash = sha256_text(final_text)

                base = self._output_base(src)
                final_path, identical = self._resolve_output_path(
                    target, base, final_hash, allow_duplicate
                )

                if identical:
                    if not dry_run:
                        self.state.record_success(
                            source_hash, content_hash, str(src.resolve()),
                            str(final_path), title,
                            f"docuflow {app_config.app.version}", engine,
                        )
                    skipped.append({
                        "file": str(src),
                        "output": str(final_path),
                        "reason": "identical file already exists",
                    })
                    continue

                if dry_run:
                    planned.append({"file": str(src), "output": str(final_path)})
                    continue

                _atomic_write(final_path, final_text)
                self.state.record_success(
                    source_hash, content_hash, str(src.resolve()),
                    str(final_path), title,
                    f"docuflow {app_config.app.version}", engine,
                )
                converted.append(str(final_path))

            except Exception as e:
                error = str(e)
                if not dry_run:
                    self.state.record_failure(
                        source_hash, "", str(src), error,
                        f"docuflow {app_config.app.version}", engine,
                    )
                failed.append({"file": str(src), "error": error})

        report: Dict[str, Any] = {
            "run_id": run_id,
            "vault": str(vault),
            "dest": dest_subdir,
            "output_dir": str(target),
            "dry_run": dry_run,
            "total_files": len(files),
            "converted": converted,
            "skipped": skipped,
            "planned": planned,
            "failed": failed,
        }

        if run_id is not None:
            stats = {
                "total": len(files),
                "converted": len(converted),
                "skipped": len(skipped),
                "failed": len(failed),
            }
            self.state.finish_run(run_id, stats, report)
            report_path = self.state.write_report(run_id, report)
            report["report_path"] = str(report_path)

        return report

    def _discover_files(self, source: Union[str, List[str]]) -> List[Path]:
        if isinstance(source, (list, tuple)):
            files: List[Path] = []
            for item in source:
                files.extend(self._discover_files(item))
            return sorted(set(files))

        root = Path(source).expanduser()
        if root.is_file():
            return [root] if root.suffix.lower() in SUPPORTED_SOURCE_EXTS else []
        if not root.is_dir():
            return []
        return sorted(
            p for p in root.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_SOURCE_EXTS
        )

    def _to_markdown(self, src: Path, use_markitdown: bool) -> tuple:
        ext = src.suffix.lower()
        with tempfile.TemporaryDirectory(prefix="docuflow_convert_") as tmp_dir:
            tmp_md = Path(tmp_dir) / "converted.md"
            if ext in {".md", ".markdown", ".txt"}:
                content = src.read_text(encoding="utf-8", errors="replace")
                existing_frontmatter, content_body = split_frontmatter(content)
                cleaned = _normalize_text(content_body)
                tmp_md.write_text(cleaned, encoding="utf-8")
                return existing_frontmatter, cleaned

            self.converter.convert_file(
                str(src), str(tmp_md), use_markitdown=use_markitdown
            )
            text = tmp_md.read_text(encoding="utf-8", errors="replace")
            return split_frontmatter(text)

    def _output_base(self, src: Path) -> str:
        ext = src.suffix.lstrip(".").lower()
        base = src.stem if ext in {"md", "markdown", "txt"} else f"{src.stem}_{ext}"
        return _sanitize_name(base)

    def _resolve_output_path(
        self,
        target: Path,
        base: str,
        final_hash: str,
        allow_duplicate: bool = False,
    ) -> tuple:
        candidate = target / f"{base}.md"
        if not candidate.exists():
            return candidate, False
        if not allow_duplicate and _file_hash(candidate) == final_hash:
            return candidate, True

        candidate = target / f"{base}-{final_hash[:6]}.md"
        counter = 2
        while candidate.exists():
            if not allow_duplicate and _file_hash(candidate) == final_hash:
                return candidate, True
            candidate = target / f"{base}-{final_hash[:6]}-{counter}.md"
            counter += 1
        return candidate, False

    def _engine_for(self, src: Path, use_markitdown: bool) -> str:
        ext = src.suffix.lower()
        if ext in {".md", ".markdown", ".txt"}:
            return "builtin"
        if use_markitdown and self.converter.markitdown_integration.is_available():
            return "markitdown"
        return {
            ".pdf": "pdfplumber",
            ".xlsx": "openpyxl",
            ".docx": "pandoc",
            ".html": "pandoc",
            ".htm": "pandoc",
        }.get(ext, "pandoc")

    def _build_frontmatter(
        self,
        src: Path,
        body: str,
        title: str,
        source_hash: str,
        content_hash: str,
        engine: str,
    ) -> Dict[str, Any]:
        try:
            captured_at = datetime.fromtimestamp(
                src.stat().st_mtime
            ).astimezone().isoformat(timespec="seconds")
        except OSError:
            captured_at = None

        return {
            "title": title,
            "source": str(src.resolve()),
            "source_type": src.suffix.lstrip(".").lower(),
            "captured_at": captured_at,
            "converted_at": now_iso(),
            "converter": f"docuflow {app_config.app.version}",
            "engine": engine,
            "source_hash": f"sha256:{source_hash}" if source_hash else None,
            "content_hash": f"sha256:{content_hash}",
            "language": detect_language(body),
            "pages": _pdf_pages(src),
            "attachments": 0,
        }
