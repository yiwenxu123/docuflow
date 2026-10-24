#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 正文抽取测试"""

from converter.html_extractor import html_to_markdown


def test_extracts_article_body(tmp_path):
    html = tmp_path / "article.html"
    html.write_text(
        """
        <html><body>
          <nav>首页 | 关于 | 登录</nav>
          <article>
            <h1>正文标题</h1>
            <p>这是文章正文，包含 <strong>粗体</strong> 和
               <a href="https://example.com">链接</a>。</p>
            <p>Code 与 Share 都是正常词。</p>
          </article>
          <footer>版权所有</footer>
        </body></html>
        """,
        encoding="utf-8",
    )

    markdown = html_to_markdown(html)
    assert markdown
    assert "正文标题" in markdown
    assert "这是文章正文" in markdown
    assert "Code" in markdown
    assert "Share" in markdown
    assert "https://example.com" in markdown


def test_returns_none_for_empty_html(tmp_path):
    html = tmp_path / "empty.html"
    html.write_text("<html><body></body></html>", encoding="utf-8")
    assert html_to_markdown(html) is None
