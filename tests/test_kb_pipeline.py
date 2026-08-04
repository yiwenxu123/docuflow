#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库管道测试

覆盖 KBChunker 分块算法与 KnowledgeBasePipeline 端到端处理。
"""

import json
from pathlib import Path

import pytest

from converter.kb_pipeline import KBChunker, KnowledgeBasePipeline


LONG_DOC = """# 主标题

文档简介段落。

## 第一节

这是第一节的内容，包含足够长的文本来触发分块。
""" + ("这是一段用于填充长度的内容。" * 60) + """

## 第二节

第二节内容。

### 子节 A

子节 A 的内容。

### 子节 B

子节 B 的内容。
"""


class TestKBChunker:
    """分块器单元测试"""

    def test_splits_by_headings(self):
        chunker = KBChunker(max_chars=10000)
        chunks = chunker.chunk_document(LONG_DOC)
        # 标题路径应正确保留
        sections = {c.section_path for c in chunks}
        assert "主标题" in sections
        assert "主标题 > 第一节" in sections
        assert "主标题 > 第二节 > 子节 A" in sections
        assert "主标题 > 第二节 > 子节 B" in sections

    def test_title_extracted_from_h1(self):
        chunker = KBChunker()
        chunks = chunker.chunk_document(LONG_DOC)
        assert all(c.title == "主标题" for c in chunks)

    def test_long_section_splits_with_overlap(self):
        chunker = KBChunker(max_chars=300, overlap=30)
        chunks = chunker.chunk_document(LONG_DOC)
        first = [c for c in chunks if c.section_path == "主标题 > 第一节"]
        assert len(first) > 1
        # 相邻块应重叠
        texts = [c.text for c in first]
        overlaps = [
            set(texts[i]) & set(texts[i + 1])
            for i in range(len(texts) - 1)
        ]
        assert all(len(o) > 0 for o in overlaps)

    def test_each_chunk_within_max_chars(self):
        chunker = KBChunker(max_chars=500, overlap=50)
        chunks = chunker.chunk_document(LONG_DOC)
        for c in chunks:
            assert len(c.text) <= 500

    def test_chunk_metadata(self):
        chunker = KBChunker(max_chars=10000)
        chunks = chunker.chunk_document(LONG_DOC, source="/tmp/a.md")
        assert len(chunks) >= 4
        for c in chunks:
            assert c.source == "/tmp/a.md"
            assert c.index < c.total
        d = chunks[0].to_dict()
        assert d["source"] == "/tmp/a.md"
        assert d["chunk_index"] == 0
        assert d["total_chunks"] == len(chunks)
        assert d["id"]
        assert d["text"]

    def test_validate_overlap_smaller_than_max(self):
        with pytest.raises(ValueError):
            KBChunker(max_chars=100, overlap=100)

    def test_empty_document(self):
        chunker = KBChunker()
        assert chunker.chunk_document("") == []
        assert chunker.chunk_document("   ") == []


class TestKnowledgeBasePipeline:
    """端到端管道测试"""

    def test_process_mixed_folder(self, converter, sample_md, sample_pdf, tmp_path):
        sources = tmp_path / "sources"
        sources.mkdir()
        (sources / "a.md").write_text(LONG_DOC, encoding="utf-8")
        (sources / "b.pdf").write_bytes(sample_pdf.read_bytes())

        out_dir = tmp_path / "kb_out"
        pipeline = KnowledgeBasePipeline(converter=converter)
        stats = pipeline.run(str(sources), str(out_dir))

        assert stats["total_files"] == 2
        assert stats["converted"] == 2
        assert stats["failed"] == []
        assert stats["chunks"] > 0

        # 产物检查
        assert (out_dir / "chunks.jsonl").exists()
        assert (out_dir / "manifest.json").exists()
        assert (out_dir / "md" / "a.md").exists()
        assert (out_dir / "md" / "b_pdf.md").exists()

    def test_chunks_jsonl_valid(self, converter, sample_md, tmp_path):
        sources = tmp_path / "sources"
        sources.mkdir()
        (sources / "a.md").write_text(LONG_DOC, encoding="utf-8")

        out_dir = tmp_path / "kb_out2"
        pipeline = KnowledgeBasePipeline(converter=converter)
        pipeline.run(str(sources), str(out_dir))

        records = []
        with open(out_dir / "chunks.jsonl", encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
        assert len(records) > 0
        assert all("text" in r and "source" in r and "title" in r for r in records)

    def test_process_single_file(self, converter, sample_md, tmp_path):
        out_dir = tmp_path / "kb_out3"
        pipeline = KnowledgeBasePipeline(converter=converter)
        stats = pipeline.run(str(sample_md), str(out_dir))
        assert stats["total_files"] == 1
        assert stats["converted"] == 1

    def test_failed_file_reported(self, converter, tmp_path):
        sources = tmp_path / "sources"
        sources.mkdir()
        (sources / "good.md").write_text("# 好文档\n\n内容", encoding="utf-8")
        bad = sources / "bad.docx"
        bad.write_bytes(b"not a docx")

        out_dir = tmp_path / "kb_out4"
        pipeline = KnowledgeBasePipeline(converter=converter)
        stats = pipeline.run(str(sources), str(out_dir))

        assert stats["converted"] == 1
        assert len(stats["failed"]) == 1
        assert "bad.docx" in stats["failed"][0]["file"]
