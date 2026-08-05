#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库管道（Knowledge Base Pipeline）

把文档集转换为 LLM/RAG 友好的结构化块（JSONL）：
1. 批量转换：任意支持格式 → 干净 Markdown（复用 DocumentConverter / MarkItDown）
2. 语义分块：按标题层级切分，保留标题上下文与相邻块重叠
3. 输出：chunks.jsonl（每条含 source/title/text/元数据）+ 转换后的 Markdown 目录

典型用法：
    from converter.kb_pipeline import KnowledgeBasePipeline
    pipeline = KnowledgeBasePipeline()
    pipeline.run("/path/to/sources", "/path/to/kb_out")
"""

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from converter.document_converter import DocumentConverter

SUPPORTED_SOURCE_EXTS = {".md", ".markdown", ".txt", ".html", ".htm", ".pdf", ".docx", ".xlsx", ".xls"}

DEFAULT_CHUNK_SIZE = 1500   # 每块目标字符数
DEFAULT_CHUNK_OVERLAP = 150  # 相邻块重叠字符数


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


def detect_llmwiki_project() -> Optional[str]:
    """检测 LLM Wiki 当前项目路径

    从 LLM Wiki 应用配置（com.llmwiki.app/app-state.json）读取，
    优先返回最近打开的项目。
    """
    state_path = (Path.home() / "Library" / "Application Support"
                  / "com.llmwiki.app" / "app-state.json")
    if not state_path.exists():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    # 优先最近打开的项目
    recent = data.get("recentProjects") or []
    for rp in recent:
        path = rp.get("path")
        if path and (Path(path) / ".llm-wiki").exists():
            return path

    # 回退：projectRegistry 中任一含 .llm-wiki 的项目
    for proj in (data.get("projectRegistry") or {}).values():
        path = proj.get("path")
        if path and (Path(path) / ".llm-wiki").exists():
            return path
    return None


def default_vault_dest(vault_dir: str) -> str:
    """根据 vault 结构选择合适的素材接收目录"""
    vault = Path(vault_dir)
    candidates = [
        "01-raw/markitdown-output",
        "01-raw/inbox",
        "01-raw",
        "raw/sources",
        "Inbox",
    ]
    for rel in candidates:
        if (vault / rel).exists():
            return rel
    return "01-raw/markitdown-output"


def llmwiki_ingest_target(vault_dir: str, dest_subdir: str = "") -> str:
    """LLM Wiki 项目的投递目标

    默认投递到 raw/sources/inbox（LLM Wiki 会按 folderContext 自动归类），
    也可显式指定 --dest 如 raw/sources/ai。
    """
    return dest_subdir or "raw/sources/inbox"


@dataclass
class Chunk:
    """单个知识库块"""
    text: str
    source: str            # 来源文件路径
    title: str             # 文档标题
    section_path: str      # 标题上下文路径，如 "架构 > 数据层"
    index: int             # 块在文档内的序号
    total: int             # 文档总块数

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": hashlib.md5(f"{self.source}|{self.section_path}|{self.index}".encode()).hexdigest()[:12],
            "source": self.source,
            "title": self.title,
            "section": self.section_path,
            "chunk_index": self.index,
            "total_chunks": self.total,
            "char_count": len(self.text),
            "text": self.text,
        }


_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*$')


def _heading_level(line: str) -> Optional[int]:
    """返回标题层级（1-6），非标题行返回 None"""
    m = _HEADING_RE.match(line.strip())
    return len(m.group(1)) if m else None


class KBChunker:
    """Markdown 语义分块器

    按标题层级把文档切成语义段；超长段再按段落递归切分，
    块之间保留重叠字符，避免关键信息被切散。
    """

    def __init__(self, max_chars: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP):
        if overlap >= max_chars:
            raise ValueError("overlap 必须小于 max_chars")
        self.max_chars = max_chars
        self.overlap = overlap

    def chunk_document(self, markdown: str, source: str = "", title: str = "") -> List[Chunk]:
        """将一篇 Markdown 文档切分为块列表

        Args:
            markdown: Markdown 内容
            source: 来源文件路径（用于元数据）
            title: 文档标题（缺省时从首个 H1 提取）

        Returns:
            List[Chunk]: 块列表
        """
        if not markdown.strip():
            return []

        # 提取文档标题
        if not title:
            title = self._extract_title(markdown)

        # 1. 按标题切分为语义段
        sections = self._split_by_headings(markdown)

        # 2. 将每个语义段进一步切分为块
        chunks: List[Chunk] = []
        for section_title, section_content in sections:
            for piece in self._split_long_text(section_content):
                chunks.append(Chunk(
                    text=piece.strip(),
                    source=source,
                    title=title,
                    section_path=section_title,
                    index=len(chunks),
                    total=0,  # 稍后回填
                ))

        total = len(chunks)
        for i, c in enumerate(chunks):
            c.index = i
            c.total = total
        return chunks

    def chunk_document_file(self, md_path: str, source: str = "") -> List[Chunk]:
        """从文件切分 Markdown 文档"""
        p = Path(md_path)
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        return self.chunk_document(content, source=source or str(p), title=p.stem)

    # ---- 内部实现 ----

    def _extract_title(self, markdown: str) -> str:
        for line in markdown.splitlines():
            m = _HEADING_RE.match(line.strip())
            if m and len(m.group(1)) == 1:
                return m.group(2).strip()
        return "Untitled"

    def _split_by_headings(self, markdown: str) -> List[tuple]:
        """按标题切分，返回 [(标题路径, 内容)] 列表"""
        lines = markdown.splitlines()
        sections: List[tuple] = []
        # 标题栈，用于构造 "父标题 > 子标题" 路径
        heading_stack: List[tuple] = []  # [(level, text)]

        current_path = ""
        current_lines: List[str] = []

        def flush():
            nonlocal current_lines, current_path
            text = "\n".join(current_lines).strip()
            if text:
                sections.append((current_path, text))

        for line in lines:
            level = _heading_level(line)
            if level is not None:
                flush()
                m = _HEADING_RE.match(line.strip())
                if m is None:
                    continue
                text = m.group(2).strip()
                # 弹出层级 >= 当前标题的祖先
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, text))
                current_path = " > ".join(t for _, t in heading_stack)
                current_lines = []
            else:
                current_lines.append(line)

        flush()
        return sections

    def _split_long_text(self, text: str, section_prefix: str = "") -> List[str]:
        """将超长文本切分为不超过 max_chars 的块，块间保留 overlap 字符"""
        if len(text) <= self.max_chars:
            return [text]

        pieces: List[str] = []
        remaining = text
        while len(remaining) > self.max_chars:
            cut = self._find_split_point(remaining[: self.max_chars])
            piece = remaining[:cut]
            pieces.append(piece)
            start = max(0, cut - self.overlap)
            remaining = remaining[start:]
        if remaining.strip():
            pieces.append(remaining)
        return pieces

    def _find_split_point(self, window: str) -> int:
        """在窗口内寻找合适的切分点：优先段落边界，其次句号，最后硬切"""
        # 优先：段落边界（最后一个 \n\n 之后）
        para_break = window.rfind("\n\n")
        if para_break > len(window) // 2:
            return para_break + 2

        # 其次：句号/问号/感叹号
        for punct in ("。", "！", "？", ". ", "! ", "? ", "\n"):
            idx = window.rfind(punct)
            if idx > len(window) // 2:
                return idx + len(punct)

        # 最后：单词/字符边界硬切
        return len(window)


class KnowledgeBasePipeline:
    """知识库构建管道

    流程：扫描源目录 → 批量转换为干净 Markdown → 分块 → 输出 JSONL
    """

    def __init__(self, chunker: Optional[KBChunker] = None, converter: Optional[DocumentConverter] = None):
        self.chunker = chunker or KBChunker()
        self.converter = converter or DocumentConverter()

    def run(self, source_dir: str, output_dir: str, use_markitdown: bool = False) -> Dict[str, Any]:
        """执行完整管道

        Args:
            source_dir: 源文档目录
            output_dir: 输出目录（生成 md/ 与 chunks.jsonl）
            use_markitdown: 优先使用 MarkItDown 转换

        Returns:
            统计信息 dict
        """
        out = Path(output_dir)
        md_dir = out / "md"
        md_dir.mkdir(parents=True, exist_ok=True)

        files = self._discover_files(source_dir)
        stats = {"total_files": len(files), "converted": 0, "failed": [], "chunks": 0}

        all_chunks: List[Chunk] = []
        for src in files:
            try:
                md_path = self._convert_one(src, md_dir, use_markitdown)
                chunks = self.chunker.chunk_document_file(str(md_path), source=str(src))
                all_chunks.extend(chunks)
                stats["converted"] += 1
            except Exception as e:
                stats["failed"].append({"file": str(src), "error": str(e)})

        # 写出 JSONL
        jsonl_path = out / "chunks.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for c in all_chunks:
                f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
        stats["chunks"] = len(all_chunks)

        # 写出摘要清单
        manifest = {
            "source_dir": str(Path(source_dir).resolve()),
            "output_dir": str(out.resolve()),
            "total_files": stats["total_files"],
            "converted": stats["converted"],
            "failed": stats["failed"],
            "total_chunks": stats["chunks"],
        }
        with open(out / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        return stats

    def _discover_files(self, source_dir: str) -> List[Path]:
        root = Path(source_dir)
        if root.is_file():
            return [root] if root.suffix.lower() in SUPPORTED_SOURCE_EXTS else []
        return sorted(
            p for p in root.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_SOURCE_EXTS
        )

    def ingest_to_vault(self, source_dir: str, vault_dir: str,
                        dest_subdir: str = "", use_markitdown: bool = False) -> Dict[str, Any]:
        """将文档集转换为干净 Markdown 并投递到 Obsidian vault 的素材目录

        Args:
            source_dir: 源文档文件或目录
            vault_dir: Obsidian vault 路径
            dest_subdir: vault 内的目标子目录；留空自动选择
            use_markitdown: 优先使用 MarkItDown 转换

        Returns:
            统计信息 dict（converted/failed/output_dir）
        """
        if not dest_subdir:
            dest_subdir = default_vault_dest(vault_dir)

        target = Path(vault_dir) / dest_subdir
        target.mkdir(parents=True, exist_ok=True)

        files = self._discover_files(source_dir)
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

    def _convert_one(self, src: Path, md_dir: Path, use_markitdown: bool) -> Path:
        """转换单个文件为 Markdown，返回输出路径"""
        # 非 Markdown 源文件带格式后缀命名，避免不同格式同名文件互相覆盖
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

        # 其余格式走转换器
        result = self.converter.convert_file(
            str(src), str(out), use_markitdown=use_markitdown
        )
        return Path(result)
