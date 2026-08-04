#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心转换冒烟测试

覆盖主要格式转换路径：md/docx/pdf/xlsx/html 互转、批量转换、异步批量。
"""

import os

import pytest

from exceptions import ConversionError


class TestMarkdownConversions:
    """Markdown 相关转换"""

    def test_md_to_docx(self, converter, sample_md, tmp_path):
        out = converter.convert_file(str(sample_md), ".docx", str(tmp_path))
        assert os.path.exists(out)
        assert out.endswith(".docx")
        assert os.path.getsize(out) > 0

    def test_md_to_html(self, converter, sample_md, tmp_path):
        out = converter.convert_file(str(sample_md), ".html", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "测试文档" in content
        assert "<table>" in content

    def test_md_to_txt(self, converter, sample_md, tmp_path):
        out = converter.convert_file(str(sample_md), ".txt", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        # 标题标记应被移除
        assert "测试文档" in content


class TestDocxConversions:
    """Word 相关转换"""

    def test_docx_to_markdown(self, converter, sample_docx, tmp_path):
        out = converter.convert_file(str(sample_docx), ".md", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "测试文档" in content

    def test_docx_to_html(self, converter, sample_docx, tmp_path):
        out = converter.convert_file(str(sample_docx), ".html", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "测试文档" in content


class TestPdfConversions:
    """PDF 相关转换"""

    def test_pdf_to_markdown(self, converter, sample_pdf, tmp_path):
        out = converter.convert_file(str(sample_pdf), ".md", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "Hello PDF Extraction Test 123" in content

    def test_pdf_to_txt(self, converter, sample_pdf, tmp_path):
        out = converter.convert_file(str(sample_pdf), ".txt", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "Hello PDF Extraction Test 123" in content

    def test_pdf_to_html(self, converter, sample_pdf, tmp_path):
        out = converter.convert_file(str(sample_pdf), ".html", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "Hello PDF Extraction Test 123" in content


class TestExcelConversions:
    """Excel 相关转换"""

    def test_xlsx_to_markdown_preserves_table(self, converter, sample_xlsx, tmp_path):
        out = converter.convert_file(str(sample_xlsx), ".md", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "姓名" in content
        assert "张三" in content
        assert "|" in content  # 表格结构保留

    def test_xlsx_to_html(self, converter, sample_xlsx, tmp_path):
        out = converter.convert_file(str(sample_xlsx), ".html", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "张三" in content

    def test_xlsx_to_txt(self, converter, sample_xlsx, tmp_path):
        out = converter.convert_file(str(sample_xlsx), ".txt", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "张三" in content


class TestHtmlConversions:
    """HTML 相关转换"""

    def test_html_to_markdown_cleaned(self, converter, sample_html, tmp_path):
        out = converter.convert_file(str(sample_html), ".md", str(tmp_path))
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "网页标题" in content
        assert "加粗" in content
        # 原始 HTML 标签应被清理
        assert "<h1>" not in content

    def test_html_to_markdown_filters_images(self, converter, sample_html, tmp_path):
        out = converter.convert_file(
            str(sample_html), ".md", str(tmp_path), filter_images=True
        )
        content = open(out, encoding="utf-8").read()
        assert "test.jpg" not in content


class TestBatchConversions:
    """批量转换"""

    def test_batch_convert(self, converter, sample_md, sample_xlsx, tmp_path):
        out_dir = tmp_path / "batch"
        results = converter.batch_convert(
            [str(sample_md), str(sample_xlsx)], ".html", str(out_dir)
        )
        assert len(results) == 2
        for r in results:
            assert os.path.exists(r)
            assert r.endswith(".html")

    def test_batch_convert_partial_failure(self, converter, sample_md, tmp_path):
        """批量中混入坏文件，成功的应照常完成"""
        bad = tmp_path / "broken.docx"
        bad.write_bytes(b"not a real docx file")
        out_dir = tmp_path / "batch2"
        results = converter.batch_convert(
            [str(sample_md), str(bad)], ".html", str(out_dir)
        )
        # 只有 md 成功
        assert len(results) == 1
        assert results[0].endswith(".html")

    def test_async_batch_convert(self, converter, sample_md, sample_xlsx, tmp_path):
        out_dir = tmp_path / "batch3"
        results = converter.async_batch_convert(
            [str(sample_md), str(sample_xlsx)], ".txt", str(out_dir), max_workers=2
        )
        assert len(results) == 2


class TestFormatSupport:
    """格式支持判断"""

    def test_can_convert_supported(self, converter):
        assert converter.can_convert(".md", ".docx") is True
        assert converter.can_convert(".pdf", ".md") is True
        assert converter.can_convert(".xlsx", ".md") is True

    def test_can_convert_unsupported(self, converter):
        assert converter.can_convert(".md", ".xlsx") is False

    def test_unsupported_conversion_raises(self, converter, sample_md, tmp_path):
        from exceptions import UnsupportedFormatError
        with pytest.raises(UnsupportedFormatError):
            converter.convert_file(str(sample_md), ".xlsx", str(tmp_path))
