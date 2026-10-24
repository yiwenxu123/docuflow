#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容清理与图片过滤测试

覆盖 Markdown 安全清理、图片过滤、表格转换、MD→TXT 等纯函数逻辑。
"""

import pytest


class TestMarkdownCleanup:
    """Markdown 内容清理"""

    def test_keeps_normal_words(self, converter):
        content = "Code 和 Share、Star、Fork 都是正常词。"
        cleaned = converter._clean_markdown_content(content)
        for word in ["Code", "Share", "Star", "Fork"]:
            assert word in cleaned

    def test_preserves_indentation(self, converter):
        content = "- 项一\n  - 子项\n\n    code block"
        cleaned = converter._clean_markdown_content(content)
        assert "  - 子项" in cleaned
        assert "    code block" in cleaned

    def test_keeps_links_and_content(self, converter):
        content = "[链接](https://example.com) 正文"
        cleaned = converter._clean_markdown_content(content)
        assert "链接" in cleaned
        assert "正文" in cleaned

    def test_cleans_html_tags_to_markdown(self, converter):
        content = "<h1>标题</h1><p><strong>粗体</strong></p><ul><li>项一</li></ul>"
        cleaned = converter._clean_markdown_content(content)
        assert "<h1>" not in cleaned
        assert "标题" in cleaned
        assert "粗体" in cleaned

    def test_clean_content_disabled_returns_original(self, converter):
        content = "原始内容 ![图](a.jpg)"
        cleaned = converter._clean_content(content, content_type="markdown", clean_content=False)
        assert cleaned == content


class TestImageFiltering:
    """图片过滤"""

    def test_filter_markdown_images(self, converter):
        content = "文本 ![图片](test.jpg) 文本"
        filtered = converter._filter_images_from_markdown(content)
        assert "test.jpg" not in filtered
        assert "文本" in filtered

    def test_filter_html_images(self, converter):
        content = '<p>文本</p><img src="a.jpg"><picture><img src="b.webp"></picture>'
        filtered = converter._filter_images_from_html(content)
        assert "a.jpg" not in filtered
        assert "b.webp" not in filtered
        assert "文本" in filtered

    def test_filter_pdf_image_placeholders(self, converter):
        content = "文本 [图] 内容 [image] 结尾 [图片]"
        filtered = converter._filter_images_from_pdf(content)
        assert "[图]" not in filtered
        assert "文本" in filtered

    def test_filter_word_delegates_to_markdown(self, converter):
        content = "![图](x.jpg)"
        filtered = converter._filter_images_from_word(content)
        assert "x.jpg" not in filtered


class TestPdfTableDedupe:
    """PDF 表格去重"""

    def test_table_already_in_text(self, converter):
        table = [["姓名", "分数"], ["张三", "95"]]
        assert converter._table_already_in_text(table, "姓名 分数 张三 95")
        assert not converter._table_already_in_text(table, "姓名 分数")


class TestTableConversion:
    """表格 → Markdown"""

    def test_table_to_markdown(self, converter):
        table = [["姓名", "分数"], ["张三", 95], ["李四", 88]]
        md = converter._convert_table_to_markdown(table)
        lines = md.split("\n")
        assert "| 姓名 | 分数 |" == lines[0]
        assert "| ---" in lines[1]
        assert "张三" in lines[2]

    def test_empty_table(self, converter):
        assert converter._convert_table_to_markdown([]) == ""
        assert converter._convert_table_to_markdown(None) == ""


class TestMarkdownToTxt:
    """Markdown → 纯文本"""

    def test_strips_markdown_markers(self, converter):
        md = "# 标题\n\n**粗体** 和 *斜体*\n\n[链接](https://x.com)\n\n`代码`"
        txt = converter._convert_markdown_to_txt(md)
        assert "#" not in txt.split("\n")[0]
        assert "**" not in txt
        assert "链接" in txt
        assert "代码" in txt
