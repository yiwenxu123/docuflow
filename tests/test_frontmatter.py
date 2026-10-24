#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Frontmatter 生成测试"""

from converter.frontmatter import (
    detect_language,
    extract_title,
    merge_frontmatter,
    render_frontmatter,
    split_frontmatter,
)


class TestFrontmatter:
    def test_render(self):
        text = render_frontmatter({
            "title": '报告 "A"',
            "pages": 2,
            "ok": True,
            "empty": None,
            "tags": ["a", "b"],
        })
        assert text.startswith("---\n")
        assert 'title: "报告 \\"A\\""' in text
        assert "pages: 2" in text
        assert "ok: true" in text
        assert "empty" not in text
        assert "  - \"a\"" in text
        assert text.endswith("---\n\n")

    def test_extract_title(self):
        assert extract_title("# 标题\n\n正文", "fallback") == "标题"
        assert extract_title("正文", "fallback") == "fallback"

    def test_detect_language(self):
        assert detect_language("这是一段足够长的中文内容，用来判断语言。") == "zh"
        assert detect_language("This is an English paragraph.") == "en"
        assert detect_language("123") == "unknown"


class TestExistingFrontmatter:
    def test_split(self):
        block, body = split_frontmatter("---\ntags:\n  - a\n---\n# 标题\n正文")
        assert block == "tags:\n  - a"
        assert body == "# 标题\n正文"

    def test_no_frontmatter(self):
        text = "# 标题\n\n正文"
        assert split_frontmatter(text) == (None, text)

    def test_chinese_key(self):
        block, body = split_frontmatter("---\n标题: 测试\n---\n正文")
        assert block == "标题: 测试"
        assert body == "正文"

    def test_merge_preserves_existing(self):
        merged = merge_frontmatter(
            "tags:\n  - a", {"source_hash": "sha256:x", "title": "标题"}
        )
        assert merged.startswith("---\ntags:\n  - a\ndocuflow:\n")
        assert '  source_hash: "sha256:x"' in merged
        assert '  title: "标题"' in merged
        assert merged.endswith("---\n\n")
