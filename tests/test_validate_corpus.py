#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证脚本指标测试"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from validate_corpus import analyze_output, classify_failure  # noqa: E402


def test_analyze_output_detects_noise(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text(
        "---\ntitle: 测试\n---\n\n# 标题\n\n"
        + "## 第 1 页\n\n正文内容。\n\n" * 4,
        encoding="utf-8",
    )
    metrics = analyze_output(doc, min_chars=20)
    assert metrics["frontmatter"] is True
    assert metrics["usable"] is True
    assert metrics["noisy"] is True


def test_analyze_output_detects_low_content(tmp_path):
    doc = tmp_path / "short.md"
    doc.write_text("---\ntitle: 短\n---\n\nx", encoding="utf-8")
    metrics = analyze_output(doc, min_chars=40)
    assert metrics["usable"] is False


def test_classify_failure():
    assert classify_failure("扫描版 PDF 需要 OCR") == "ocr_needed"
    assert classify_failure("转换结果为空") == "empty_output"
    assert classify_failure("pandoc 转换失败") == "pandoc_error"
    assert classify_failure("something else") == "other"
