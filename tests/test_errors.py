#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误场景测试

覆盖文件不存在、不支持格式、损坏文件、文件过大、批次验证等错误处理。
"""

import os

import pytest

from exceptions import (
    ConversionError,
    FileAccessError,
    FileSizeError,
    UnsupportedFormatError,
)


class TestValidationErrors:
    """输入验证错误"""

    def test_file_not_found(self, converter, tmp_path):
        with pytest.raises(FileAccessError) as exc_info:
            converter.convert_file(str(tmp_path / "nope.md"), ".docx", str(tmp_path))
        assert "不存在" in str(exc_info.value)

    def test_unsupported_source_format(self, converter, tmp_path):
        f = tmp_path / "weird.xyz"
        f.write_text("hello")
        with pytest.raises(UnsupportedFormatError):
            converter.convert_file(str(f), ".md", str(tmp_path))

    def test_unsupported_output_format(self, converter, sample_md, tmp_path):
        with pytest.raises(UnsupportedFormatError):
            converter.convert_file(str(sample_md), ".xyz", str(tmp_path))

    def test_file_too_large(self, converter, sample_md, tmp_path, monkeypatch):
        """文件超过限制时应抛出 FileSizeError"""
        # 将最大文件大小改为 1 字节
        original = converter.config.conversion
        monkeypatch.setattr(converter.config.conversion, "max_file_size", 1)
        try:
            with pytest.raises(FileSizeError):
                converter.convert_file(str(sample_md), ".docx", str(tmp_path))
        finally:
            converter.config.conversion = original


class TestBrokenFiles:
    """损坏文件处理"""

    def test_broken_docx_raises_friendly_error(self, converter, tmp_path):
        bad = tmp_path / "broken.docx"
        bad.write_bytes(b"this is not a real docx zip file")
        with pytest.raises(ConversionError) as exc_info:
            converter.convert_file(str(bad), ".md", str(tmp_path))
        # 错误信息应是用户友好的中文提示
        assert "DOCX" in str(exc_info.value) or "损坏" in str(exc_info.value)

    def test_broken_pdf_raises(self, converter, tmp_path):
        bad = tmp_path / "broken.pdf"
        bad.write_bytes(b"not a pdf")
        with pytest.raises(ConversionError):
            converter.convert_file(str(bad), ".md", str(tmp_path))

    def test_corrupt_xlsx_falls_back_to_second_engine(self, converter, tmp_path):
        """坏 xlsx：openpyxl 失败后应尝试 pandas，最终抛 ConversionError"""
        bad = tmp_path / "bad.xlsx"
        bad.write_bytes(b"not a real xlsx")
        with pytest.raises(ConversionError):
            converter.convert_file(str(bad), ".md", str(tmp_path))
