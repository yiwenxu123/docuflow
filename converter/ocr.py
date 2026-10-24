#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描 PDF 检测与 OCR 兜底

依赖外部 ocrmypdf（以及 tesseract 语言包）；未安装时调用方应给出明确提示。
"""

import shutil
import subprocess
from pathlib import Path
from typing import Union


def ocr_available() -> bool:
    return shutil.which("ocrmypdf") is not None


def needs_ocr(
    pdf_path: Union[str, Path],
    sample_pages: int = 3,
    min_chars_per_page: int = 20,
) -> bool:
    """抽样判断 PDF 是否为扫描件（文字很少）"""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        if total_pages == 0:
            return True
        if total_pages <= sample_pages:
            indexes = list(range(total_pages))
        else:
            indexes = sorted({
                0, 1, total_pages // 2,
                max(0, total_pages - 2), total_pages - 1,
            })
        total = sum(
            len((reader.pages[i].extract_text() or "").strip())
            for i in indexes
        )
        return total / len(indexes) < min_chars_per_page
    except Exception:
        return False


def run_ocr(
    src: Union[str, Path],
    dst: Union[str, Path],
    language: str = "chi_sim+eng",
    timeout: int = 300,
) -> Path:
    """对 PDF 执行 OCR，返回输出路径"""
    dst_path = Path(dst)
    cmd = [
        "ocrmypdf",
        "--skip-text",
        "--language",
        language,
        str(src),
        str(dst_path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        raise RuntimeError("ocrmypdf 未安装")
    except subprocess.TimeoutExpired:
        raise RuntimeError("OCR 超时")

    if result.returncode != 0:
        raise RuntimeError(f"OCR 失败: {result.stderr.strip()[:300]}")
    if not dst_path.exists():
        raise RuntimeError("OCR 未生成输出文件")
    return dst_path
