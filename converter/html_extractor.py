#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 正文抽取

用 trafilatura 提取文章主体并输出 Markdown；失败时返回 None，
由调用方回退到 pandoc。
"""

from pathlib import Path
from typing import Optional


def html_to_markdown(html_path: Path) -> Optional[str]:
    try:
        import trafilatura
    except ImportError:
        return None

    try:
        html = html_path.read_text(encoding="utf-8", errors="replace")
        result = trafilatura.extract(
            html,
            url=str(html_path),
            output_format="markdown",
            include_comments=False,
            include_tables=True,
            include_images=True,
            include_formatting=True,
            include_links=True,
            deduplicate=True,
        )
    except Exception:
        return None

    return result if result and result.strip() else None
