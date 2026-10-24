#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 PDF 检测与 OCR 失败提示测试"""

from pathlib import Path

import pytest
from pypdf import PdfWriter

from converter.kb_pipeline import KnowledgeBasePipeline
from converter.ocr import needs_ocr


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    (v / "01-raw" / "inbox").mkdir(parents=True)
    return v


def make_blank_pdf(path: Path) -> Path:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with open(path, "wb") as f:
        writer.write(f)
    return path


def test_text_pdf_does_not_need_ocr(sample_pdf):
    assert needs_ocr(sample_pdf) is False


def test_blank_pdf_needs_ocr(tmp_path):
    assert needs_ocr(make_blank_pdf(tmp_path / "blank.pdf")) is True


def test_scanned_pdf_reports_ocr_needed(converter, vault, tmp_path, monkeypatch):
    blank = make_blank_pdf(tmp_path / "scan.pdf")
    monkeypatch.setattr("converter.kb_pipeline.ocr_available", lambda: False)

    pipeline = KnowledgeBasePipeline(converter=converter)
    result = pipeline.ingest_to_vault(str(blank), str(vault))

    assert result["converted"] == []
    assert len(result["failed"]) == 1
    assert "OCR" in result["failed"][0]["error"]


def test_ocr_off_reports_clear_error(converter, vault, tmp_path):
    blank = make_blank_pdf(tmp_path / "scan.pdf")
    pipeline = KnowledgeBasePipeline(converter=converter)
    result = pipeline.ingest_to_vault(str(blank), str(vault), ocr_mode="off")

    assert result["converted"] == []
    assert len(result["failed"]) == 1
    assert "OCR" in result["failed"][0]["error"]
