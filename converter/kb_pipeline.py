#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库投递管道（收缩版）

只保留三件事：
1. 检测当前打开的 Obsidian vault；
2. 选择收件箱目录（默认 01-raw/inbox）；
3. 把文档转换为 Markdown 并投递到该目录。

RAG 分块、向量索引、LLM Wiki 自动分类均已移除。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from converter.document_converter import DocumentConverter

SUPPORTED_SOURCE_EXTS = {
    ".md", ".markdown", ".txt", ".html", ".htm",
    ".pdf", ".docx", ".xlsx",
}


def detect_obsidian_vault() -> Optional[str]:
    """检测当前打开的 Obsidian vault 路径

    读取 Obsidian 的 obsidian.json，返回 open=true 的 vault；
    无结果时返回第一个 vault。
    """
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
    """选择收件箱目录

    优先使用 01-raw/inbox；不再根据 markitdown-output 是否存在
    隐式切换目标，避免投递位置漂移。
    """
    vault = Path(vault_dir)
    candidates = ["01-raw/inbox", "01-raw", "raw/sources", "Inbox"]
    for rel in candidates:
        if (vault / rel).exists():
            return rel
    return "01-raw/inbox"


class KnowledgeBasePipeline:
    """文档转换并投递到 Obsidian vault"""

    def __init__(self, converter: Optional[DocumentConverter] = None):
        self.converter = converter or DocumentConverter()

    def ingest_to_vault(
        self,
        source: str,
        vault_dir: str,
        dest_subdir: str = "",
        use_markitdown: bool = False,
    ) -> Dict[str, Any]:
        """将文件或目录转换为 Markdown 并投递到 vault 的指定子目录

        Args:
            source: 源文件或目录
            vault_dir: Obsidian vault 路径
            dest_subdir: vault 内的目标子目录；留空自动选择
            use_markitdown: 优先使用 MarkItDown

        Returns:
            dict: converted / failed / output_dir / total_files
        """
        if not dest_subdir:
            dest_subdir = default_vault_dest(vault_dir)

        target = Path(vault_dir) / dest_subdir
        target.mkdir(parents=True, exist_ok=True)

        files = self._discover_files(source)
        converted, failed = [], []
        for src in files:
            try:
                out = self._convert_one(src, target, use_markitdown)
                converted.append(str(out))
            except Exception as e:
                failed.append({"file": str(src), "error": str(e)})

        return {
            "converted": converted,
            "failed": failed,
            "output_dir": str(target),
            "total_files": len(files),
        }

    def _discover_files(self, source: str) -> List[Path]:
        root = Path(source)
        if root.is_file():
            return [root] if root.suffix.lower() in SUPPORTED_SOURCE_EXTS else []
        if not root.is_dir():
            return []
        return sorted(
            p for p in root.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_SOURCE_EXTS
        )

    def _convert_one(self, src: Path, md_dir: Path, use_markitdown: bool) -> Path:
        """转换单个文件为 Markdown，返回输出路径"""
        ext = src.suffix.lstrip(".").lower()
        if ext in {"md", "markdown", "txt"}:
            out = md_dir / f"{src.stem}.md"
        else:
            out = md_dir / f"{src.stem}_{ext}.md"

        # Markdown/TXT 源文件无需格式转换，直接清理内容
        if ext in {"md", "markdown", "txt"}:
            content = src.read_text(encoding="utf-8", errors="replace")
            cleaned = self.converter._clean_content(
                content=content,
                content_type="markdown" if ext != "txt" else "text",
                filter_images=True,
                clean_content=True,
            )
            out.write_text(cleaned, encoding="utf-8")
            return out

        result = self.converter.convert_file(
            str(src), str(out), use_markitdown=use_markitdown
        )
        return Path(result)
