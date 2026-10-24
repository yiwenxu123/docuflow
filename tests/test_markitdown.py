#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarkItDown 集成测试

MarkItDown 命令不可用时自动跳过。
"""

import os

import pytest

from converter.markitdown_integration import (
    MarkItDownIntegration,
    get_markitdown_integration,
)


@pytest.fixture
def markitdown():
    md = get_markitdown_integration()
    if not md.is_available():
        pytest.skip("MarkItDown 未安装，跳过")
    return md


class TestMarkItDownIntegration:
    """MarkItDown 集成"""

    def test_is_available(self, markitdown):
        assert markitdown.is_available() is True

    def test_supported_formats_contains_pdf(self, markitdown):
        formats = markitdown.get_supported_formats()
        assert ".pdf" in formats
        assert ".docx" in formats

    def test_convert_to_markdown(self, markitdown, sample_pdf, tmp_path):
        out = tmp_path / "md_out.md"
        result = markitdown.convert_file(str(sample_pdf), output_file=str(out))
        assert os.path.exists(result)
        content = open(result, encoding="utf-8").read()
        assert content.strip() != ""

    def test_converter_use_markitdown_path(self, converter, sample_xlsx, tmp_path):
        """DocumentConverter 的 use_markitdown 路径"""
        if not converter.markitdown_integration.is_available():
            pytest.skip("MarkItDown 未安装，跳过")
        out = converter.convert_file(
            str(sample_xlsx), ".md", str(tmp_path), use_markitdown=True
        )
        assert os.path.exists(out)
        content = open(out, encoding="utf-8").read()
        assert "姓名" in content
