#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 共享夹具

提供转换器实例与各类测试样本文件（md/docx/pdf/xlsx/html）。
"""

import os
import sys
import subprocess
from pathlib import Path

import pytest

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from converter.document_converter import DocumentConverter  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_docuflow_state(tmp_path, monkeypatch):
    """避免测试写入用户真实的状态库"""
    monkeypatch.setenv("DOCUFLOW_STATE_DB", str(tmp_path / "state.db"))


SAMPLE_MD = """# 测试文档

## 二级标题

这是**加粗**正文，包含`代码`。

- 列表项一
- 列表项二

| 列A | 列B |
|-----|-----|
| 1 | 2 |

[链接文本](https://example.com)
"""

SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>测试页面</title></head>
<body>
    <h1>网页标题</h1>
    <p>这是<strong>加粗</strong>正文</p>
    <img src="test.jpg" alt="测试图片">
    <ul>
        <li>项目一</li>
        <li>项目二</li>
    </ul>
    <table>
        <tr><th>姓名</th><th>分数</th></tr>
        <tr><td>张三</td><td>95</td></tr>
    </table>
</body>
</html>
"""

# 最小合法 PDF（含一行 Helvetica 文本）
MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 88>>stream
BT /F1 24 Tf 72 720 Td (Hello PDF Extraction Test 123) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
0000000221 00000 n
0000000351 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
413
%%EOF
"""


@pytest.fixture(scope="session")
def converter():
    """全局转换器实例（会话级，避免重复初始化）"""
    return DocumentConverter()


@pytest.fixture
def sample_md(tmp_path):
    """Markdown 样本文件"""
    p = tmp_path / "sample.md"
    p.write_text(SAMPLE_MD, encoding="utf-8")
    return p


@pytest.fixture
def sample_docx(tmp_path):
    """Word 样本文件（由 pandoc 从 Markdown 生成）"""
    md = tmp_path / "_src.md"
    md.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "sample.docx"
    result = subprocess.run(
        ["pandoc", str(md), "-o", str(out)], capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        pytest.skip(f"pandoc 无法生成 docx: {result.stderr}")
    return out


@pytest.fixture
def sample_pdf(tmp_path):
    """PDF 样本文件（最小手写 PDF）"""
    p = tmp_path / "sample.pdf"
    p.write_bytes(MINIMAL_PDF)
    return p


@pytest.fixture
def sample_xlsx(tmp_path):
    """Excel 样本文件"""
    openpyxl = pytest.importorskip("openpyxl")
    p = tmp_path / "sample.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["姓名", "分数"])
    ws.append(["张三", 95])
    ws.append(["李四", 88])
    wb.save(p)
    return p


@pytest.fixture
def sample_html(tmp_path):
    """HTML 样本文件（含图片引用）"""
    p = tmp_path / "sample.html"
    p.write_text(SAMPLE_HTML, encoding="utf-8")
    return p
