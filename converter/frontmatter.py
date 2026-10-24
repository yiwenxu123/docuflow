#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontmatter 生成

不引入 PyYAML：字符串用 JSON 引号包裹，JSON 字符串是合法 YAML。
"""

import json
import re
from typing import Any, Dict, Optional, Tuple


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def render_frontmatter(meta: Dict[str, Any]) -> str:
    """把字典渲染成 YAML frontmatter 块"""
    lines = ["---"]
    for key, value in meta.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {_yaml_scalar(item)}")
        else:
            lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def split_frontmatter(text: str) -> Tuple[Optional[str], str]:
    """拆分已有 frontmatter，返回 (frontmatter 内容或 None, 正文)

    仅在首行是 --- 且前 100 行内出现闭合 --- 时识别；
    frontmatter 内容不像 YAML 键值对时按正文处理。
    """
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text

    for i, line in enumerate(lines[1:100], start=1):
        if line.strip() == "---":
            block = "".join(lines[1:i]).rstrip("\r\n")
            if block and not re.search(r"^[A-Za-z0-9_\u4e00-\u9fff-]+:", block, re.M):
                return None, text
            body = "".join(lines[i + 1 :]).lstrip("\r\n")
            return block, body
    return None, text


def merge_frontmatter(existing_block: str, meta: Dict[str, Any]) -> str:
    """保留已有 frontmatter，把 ingest 元数据放进 docuflow 子块"""
    key = "docuflow"
    if re.search(r"^docuflow:", existing_block, re.M):
        key = "docuflow_ingest"

    lines = [existing_block.rstrip("\r\n"), f"{key}:"]
    for name, value in meta.items():
        if value is None:
            continue
        lines.append(f"  {name}: {_yaml_scalar(value)}")
    return "---\n" + "\n".join(lines) + "\n---\n\n"


def extract_title(markdown: str, fallback: str) -> str:
    """优先使用首个 H1 作为标题"""
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title
    return fallback


def detect_language(text: str) -> str:
    """粗略判断中英文，供检索/过滤参考"""
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    letters = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if cjk == 0 and letters == 0:
        return "unknown"
    if cjk >= 10 and cjk / max(cjk + letters, 1) >= 0.2:
        return "zh"
    if letters:
        return "en"
    return "unknown"
