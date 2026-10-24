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


class TestIngestToVault:
    """投递逻辑"""

    @pytest.fixture
    def vault(self, tmp_path):
        v = tmp_path / "vault"
        (v / "01-raw" / "inbox").mkdir(parents=True)
        return v

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
