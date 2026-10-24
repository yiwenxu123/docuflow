#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片附件落盘

把 Markdown 中的本地图片复制到 attachments/<文档键>/，
并把链接改写为相对路径；远程 URL 保持原样。
"""

import base64
import hashlib
import re
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

IMAGE_RE = re.compile(
    r'!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(\s+"[^"]*")?\s*\)'
)

_MIME_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def _safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")


def _read_image(src: str, source_path: Path) -> Optional[Tuple[str, bytes]]:
    if src.startswith("data:"):
        match = re.match(r"data:([^;]+);base64,(.*)", src, re.S)
        if not match:
            return None
        mime, payload = match.groups()
        try:
            return _MIME_EXT.get(mime.lower(), ".png"), base64.b64decode(payload)
        except Exception:
            return None

    if src.startswith(("http://", "https://")):
        return None

    if src.startswith("file://"):
        path = Path(unquote(urlparse(src).path))
    else:
        path = Path(unquote(src))
        if not path.is_absolute():
            path = source_path.parent / path

    try:
        path = path.resolve()
        # 只复制来源目录内的本地图片，避免把任意本地路径带进 vault
        if not path.is_relative_to(source_path.parent.resolve()):
            return None
        if not path.is_file():
            return None
        return path.suffix.lower() or ".png", path.read_bytes()
    except OSError:
        return None


def materialize_images(
    markdown: str,
    source_path: Path,
    dest_dir: Path,
    attachment_key: str,
    dry_run: bool = False,
) -> Tuple[str, int]:
    """复制本地图片并重写链接，返回 (新 Markdown, 附件数)"""
    source_path = Path(source_path)
    dest_dir = Path(dest_dir)
    attachment_key = _safe_name(attachment_key) or "document"
    count = 0
    seen = set()

    def replace(match: re.Match) -> str:
        nonlocal count
        alt, src, title = match.group(1), match.group(2), match.group(3) or ""
        image = _read_image(src, source_path)
        if image is None:
            return match.group(0)

        ext, data = image
        digest = hashlib.sha256(data).hexdigest()[:8]
        original_name = Path(unquote(src)).name
        name = _safe_name(original_name) or f"image{ext}"
        if not Path(name).suffix:
            name += ext

        target = dest_dir / "attachments" / attachment_key / f"{digest}-{name}"
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(data)

        if target not in seen:
            count += 1
            seen.add(target)
        new_src = f"attachments/{attachment_key}/{target.name}"
        return f"![{alt}]({new_src}{title})"

    return IMAGE_RE.sub(replace, markdown), count
