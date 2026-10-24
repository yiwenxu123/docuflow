#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian 投递测试

覆盖 vault 自动检测、收件箱选择与 ingest_to_vault 投递逻辑。
"""

import json
from pathlib import Path

import pytest

from converter.kb_pipeline import (
    KnowledgeBasePipeline,
    default_vault_dest,
    detect_obsidian_vault,
)


class TestVaultDetection:
    """Obsidian vault 检测"""

    def test_detect_open_vault(self, tmp_path, monkeypatch):
        obsidian_dir = tmp_path / "Library" / "Application Support" / "obsidian"
        obsidian_dir.mkdir(parents=True)
        (obsidian_dir / "obsidian.json").write_text(json.dumps({
            "vaults": {
                "1": {"path": "/vault/closed", "open": False},
                "2": {"path": "/vault/active", "open": True},
            }
        }), encoding="utf-8")
        monkeypatch.setattr("converter.kb_pipeline.Path.home", lambda: tmp_path)
        assert detect_obsidian_vault() == "/vault/active"

    def test_detect_fallback_first_vault(self, tmp_path, monkeypatch):
        obsidian_dir = tmp_path / "Library" / "Application Support" / "obsidian"
        obsidian_dir.mkdir(parents=True)
        (obsidian_dir / "obsidian.json").write_text(json.dumps({
            "vaults": {
                "1": {"path": "/vault/a"},
                "2": {"path": "/vault/b"},
            }
        }), encoding="utf-8")
        monkeypatch.setattr("converter.kb_pipeline.Path.home", lambda: tmp_path)
        assert detect_obsidian_vault() == "/vault/a"

    def test_detect_no_obsidian(self, tmp_path, monkeypatch):
        monkeypatch.setattr("converter.kb_pipeline.Path.home", lambda: tmp_path)
        assert detect_obsidian_vault() is None


class TestVaultDestSelection:
    """收件箱选择"""

    def test_prefers_inbox(self, tmp_path):
        (tmp_path / "01-raw" / "inbox").mkdir(parents=True)
        (tmp_path / "01-raw" / "markitdown-output").mkdir(parents=True)
        assert default_vault_dest(str(tmp_path)) == "01-raw/inbox"

    def test_falls_back_to_01_raw(self, tmp_path):
        (tmp_path / "01-raw").mkdir(parents=True)
        assert default_vault_dest(str(tmp_path)) == "01-raw"

    def test_falls_back_to_raw_sources(self, tmp_path):
        (tmp_path / "raw" / "sources").mkdir(parents=True)
        assert default_vault_dest(str(tmp_path)) == "raw/sources"

    def test_default_is_inbox(self, tmp_path):
        assert default_vault_dest(str(tmp_path)) == "01-raw/inbox"


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    (v / "01-raw" / "inbox").mkdir(parents=True)
    return v


class TestIngestToVault:
    """投递逻辑"""

    def test_ingest_mixed_sources(self, converter, sample_md, sample_pdf, vault):
        sources = vault.parent / "sources"
        sources.mkdir()
        (sources / "a.md").write_text("# 文档\n\n内容", encoding="utf-8")
        (sources / "b.pdf").write_bytes(sample_pdf.read_bytes())

        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault(str(sources), str(vault))

        assert result["total_files"] == 2
        assert len(result["converted"]) == 2
        assert result["failed"] == []
        out_dir = Path(result["output_dir"])
        assert (out_dir / "a.md").exists()
        assert (out_dir / "b_pdf.md").exists()

    def test_ingest_accepts_file_list(self, converter, sample_md, vault):
        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault([str(sample_md)], str(vault))
        assert result["total_files"] == 1
        assert len(result["converted"]) == 1

    def test_ingest_custom_dest(self, converter, sample_md, vault):
        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault(
            str(sample_md), str(vault), dest_subdir="01-raw/inbox"
        )
        assert result["output_dir"].endswith("01-raw/inbox")
        assert Path(result["output_dir"]).exists()

    def test_ingest_failed_file_reported(self, converter, vault, tmp_path):
        sources = tmp_path / "src"
        sources.mkdir()
        bad = sources / "bad.docx"
        bad.write_bytes(b"not a docx")

        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault(str(sources), str(vault))
        assert len(result["converted"]) == 0
        assert len(result["failed"]) == 1
        assert "bad.docx" in result["failed"][0]["file"]


class TestIngestContract:
    """frontmatter 与去重契约"""

    def test_frontmatter_and_dedupe(self, converter, vault, tmp_path):
        src = tmp_path / "single"
        src.mkdir()
        doc = src / "doc.md"
        doc.write_text("# 标题\n\n正文内容", encoding="utf-8")

        pipeline = KnowledgeBasePipeline(converter=converter)
        first = pipeline.ingest_to_vault(str(doc), str(vault))
        assert len(first["converted"]) == 1

        output = Path(first["converted"][0])
        text = output.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "source_hash:" in text
        assert "content_hash:" in text
        assert 'title: "标题"' in text

        second = pipeline.ingest_to_vault(str(doc), str(vault))
        assert second["converted"] == []
        assert len(second["skipped"]) == 1
        assert len(list((vault / "01-raw" / "inbox").glob("*.md"))) == 1

    def test_markdown_content_not_overcleaned(self, converter, vault, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        doc = src / "note.md"
        doc.write_text(
            "# 标题\n\nCode 与 Share 都是正常词。\n\n![图](img.png)",
            encoding="utf-8",
        )

        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault(str(doc), str(vault))
        text = Path(result["converted"][0]).read_text(encoding="utf-8")

        assert "Code" in text
        assert "Share" in text
        assert "![图](img.png)" in text

    def test_html_uses_body_extraction(self, converter, vault, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        doc = src / "article.html"
        doc.write_text(
            "<html><body><article><h1>标题</h1>"
            "<p>Code 与 Share 都是正常词。</p></article></body></html>",
            encoding="utf-8",
        )

        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault(str(doc), str(vault))
        text = Path(result["converted"][0]).read_text(encoding="utf-8")

        assert 'engine: "trafilatura"' in text
        assert "Code" in text
        assert "Share" in text

    def test_local_image_materialized(self, converter, vault, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        doc = src / "note.md"
        doc.write_text("# 图\n\n![图](pic.png)", encoding="utf-8")
        (src / "pic.png").write_bytes(b"fake-png-data")

        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault(str(doc), str(vault))
        output = Path(result["converted"][0])
        text = output.read_text(encoding="utf-8")

        assert "attachments/" in text
        assert "attachments: 1" in text
        attachments = list((vault / "01-raw" / "inbox" / "attachments").rglob("*.png"))
        assert len(attachments) == 1

    def test_existing_frontmatter_preserved(self, converter, vault, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        doc = src / "note.md"
        doc.write_text(
            "---\ntags:\n  - test\naliases:\n  - 别名\n---\n# 标题\n\n正文",
            encoding="utf-8",
        )

        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault(str(doc), str(vault))
        text = Path(result["converted"][0]).read_text(encoding="utf-8")

        assert text.startswith("---\n")
        assert len([line for line in text.splitlines() if line.strip() == "---"]) == 2
        assert "tags:" in text
        assert "  - test" in text
        assert "aliases:" in text
        assert "docuflow:" in text
        assert "  source_hash:" in text

    def test_dry_run_does_not_write(self, converter, sample_md, vault):
        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_to_vault(str(sample_md), str(vault), dry_run=True)
        assert result["converted"] == []
        assert len(result["planned"]) == 1
        assert len(list((vault / "01-raw" / "inbox").glob("*.md"))) == 0


class TestNoOverwrite:
    """同名文件不得覆盖"""

    def test_collision_gets_hash_suffix(self, converter, tmp_path):
        vault = tmp_path / "vault"
        (vault / "01-raw" / "inbox").mkdir(parents=True)
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "same.md").write_text("# A\n\nfirst content", encoding="utf-8")
        (b / "same.md").write_text("# B\n\nsecond content", encoding="utf-8")

        pipeline = KnowledgeBasePipeline(converter=converter)
        first = pipeline.ingest_to_vault(str(a), str(vault))
        first_path = Path(first["converted"][0])
        first_text = first_path.read_text(encoding="utf-8")

        second = pipeline.ingest_to_vault(str(b), str(vault))
        second_path = Path(second["converted"][0])

        assert second_path != first_path
        assert first_path.read_text(encoding="utf-8") == first_text
        assert second_path.exists()
        assert len(list((vault / "01-raw" / "inbox").glob("*.md"))) == 2


class TestAllowDuplicate:
    """显式允许重复时生成副本，不覆盖"""

    def test_allow_duplicate_creates_copy(self, converter, sample_md, vault):
        pipeline = KnowledgeBasePipeline(converter=converter)
        first = pipeline.ingest_to_vault(str(sample_md), str(vault))
        second = pipeline.ingest_to_vault(
            str(sample_md), str(vault), allow_duplicate=True
        )
        assert len(first["converted"]) == 1
        assert len(second["converted"]) == 1
        assert second["converted"][0] != first["converted"][0]
        assert len(list((vault / "01-raw" / "inbox").glob("*.md"))) == 2


class TestGateTwo:
    """Gate 2：20 个文件二次投递全部跳过"""

    def test_20_files_second_run_skips_all(self, converter, tmp_path):
        vault = tmp_path / "vault"
        (vault / "01-raw" / "inbox").mkdir(parents=True)
        src = tmp_path / "src"
        src.mkdir()
        for i in range(20):
            (src / f"doc{i:02d}.md").write_text(
                f"# 文档 {i}\n\n这是第 {i} 篇内容。", encoding="utf-8"
            )

        pipeline = KnowledgeBasePipeline(converter=converter)
        first = pipeline.ingest_to_vault(str(src), str(vault))
        assert len(first["converted"]) == 20
        assert first["failed"] == []

        second = pipeline.ingest_to_vault(str(src), str(vault))
        assert second["converted"] == []
        assert len(second["skipped"]) == 20
        assert len(list((vault / "01-raw" / "inbox").glob("*.md"))) == 20
