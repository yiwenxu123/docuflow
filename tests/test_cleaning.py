#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容清理与图片过滤测试

覆盖 Markdown 清理（Gist 结构去除）、图片过滤、表格转换、MD→TXT 等纯函数逻辑。
"""

import pytest


GIST_MARKDOWN = """# 测试文档

::: {.markdown-body}
这是正文内容。

[文件引用](/Users/yiwenxu123/trae/文档转换/llm-wiki_filtered.md#L1-224)

![图片](image.jpg)

gist.github.com 页面结构标记
Created by 作者
Fork Share Star
:::
"""


class TestMarkdownCleanup:
    """Markdown 内容清理"""

    def test_removes_file_path_references(self, converter):
        content = "参考 /path/to/file.md#L1-224 的内容"
        cleaned = converter._clean_markdown_content(content)
        assert "L1-224" not in cleaned
        assert "参考" in cleaned

    def test_removes_gist_structural_markers(self, converter):
        cleaned = converter._clean_markdown_content(GIST_MARKDOWN)
        # 页面结构标记应被去除
        assert ":::" not in cleaned
        assert "gist.github.com" not in cleaned
        assert "Created by" not in cleaned
        # 正文内容保留
        assert "这是正文内容" in cleaned

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
