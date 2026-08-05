#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian ingest 集成测试

覆盖 vault 自动检测、目标目录选择与 ingest_to_vault 投递逻辑。
"""

import json
from pathlib import Path

import pytest

from converter.kb_pipeline import (
    KnowledgeBasePipeline, default_vault_dest, detect_obsidian_vault,
    detect_llmwiki_project, llmwiki_ingest_target,
    classify_source, auto_ingest_target,
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
        result = detect_obsidian_vault()
        assert result == "/vault/active"

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
    """目标子目录自动选择"""

    def test_prefers_markitdown_output(self, tmp_path):
        (tmp_path / "01-raw" / "markitdown-output").mkdir(parents=True)
        (tmp_path / "01-raw" / "inbox").mkdir(parents=True)
        assert default_vault_dest(str(tmp_path)) == "01-raw/markitdown-output"

    def test_prefers_inbox_when_no_markitdown(self, tmp_path):
        (tmp_path / "01-raw" / "inbox").mkdir(parents=True)
        assert default_vault_dest(str(tmp_path)) == "01-raw/inbox"

    def test_prefers_raw_sources_for_llm_wiki_vault(self, tmp_path):
        (tmp_path / "raw" / "sources").mkdir(parents=True)
        assert default_vault_dest(str(tmp_path)) == "raw/sources"

    def test_fallback_default(self, tmp_path):
        assert default_vault_dest(str(tmp_path)) == "01-raw/markitdown-output"


class TestLlmwikiDetection:
    """LLM Wiki 项目检测与投递目标"""

    def test_detect_project_from_recent(self, tmp_path, monkeypatch):
        app_dir = tmp_path / "Library" / "Application Support" / "com.llmwiki.app"
        app_dir.mkdir(parents=True)
        project = tmp_path / "my-wiki"
        (project / ".llm-wiki").mkdir(parents=True)
        (app_dir / "app-state.json").write_text(json.dumps({
            "recentProjects": [
                {"path": str(project), "name": "my-wiki"},
                {"path": "/old/project", "name": "old"},
            ]
        }), encoding="utf-8")
        monkeypatch.setattr("converter.kb_pipeline.Path.home", lambda: tmp_path)
        assert detect_llmwiki_project() == str(project)

    def test_detect_fallback_registry(self, tmp_path, monkeypatch):
        app_dir = tmp_path / "Library" / "Application Support" / "com.llmwiki.app"
        app_dir.mkdir(parents=True)
        project = tmp_path / "wiki2"
        (project / ".llm-wiki").mkdir(parents=True)
        (app_dir / "app-state.json").write_text(json.dumps({
            "recentProjects": [],
            "projectRegistry": {"a": {"path": str(project)}},
        }), encoding="utf-8")
        monkeypatch.setattr("converter.kb_pipeline.Path.home", lambda: tmp_path)
        assert detect_llmwiki_project() == str(project)

    def test_detect_none_when_no_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr("converter.kb_pipeline.Path.home", lambda: tmp_path)
        assert detect_llmwiki_project() is None

    def test_ingest_target_default_inbox(self, tmp_path):
        assert llmwiki_ingest_target(str(tmp_path)) == "raw/sources/inbox"

    def test_ingest_target_custom(self, tmp_path):
        assert llmwiki_ingest_target(str(tmp_path), "raw/sources/ai") == "raw/sources/ai"


class TestAutoClassify:
    """文件名自动分类"""

    @pytest.mark.parametrize("filename,expected", [
        ("AI_Agent上下文管理最佳实践.md", "ai"),
        ("文案写作技巧汇总.md", "writing"),
        ("方法论框架整理.md", "methodology"),
        ("毛泽东传读书笔记.md", "books"),
        ("deepseek入门指南.pdf", "ai"),
        ("随便一个文件名.txt", "inbox"),
        ("unknown.docx", "inbox"),
    ])
    def test_classify_source(self, filename, expected):
        assert classify_source(filename) == expected

    def test_auto_target(self, tmp_path):
        assert auto_ingest_target(str(tmp_path), "AI报告.pdf") == "raw/sources/ai"
        assert auto_ingest_target(str(tmp_path), "杂项.txt") == "raw/sources/inbox"


class TestIngestAuto:
    """自动分类投递"""

    def test_ingest_auto_mixed(self, converter, sample_pdf, tmp_path):
        vault = tmp_path / "llmwiki"
        (vault / ".llm-wiki").mkdir(parents=True)
        (vault / "raw" / "sources").mkdir(parents=True)

        sources = tmp_path / "src"
        sources.mkdir()
        (sources / "AI调研报告.pdf").write_bytes(sample_pdf.read_bytes())
        (sources / "文案笔记.md").write_text("# 文案\n\n写作技巧", encoding="utf-8")
        (sources / "杂项.txt").write_text("杂项", encoding="utf-8")

        pipeline = KnowledgeBasePipeline(converter=converter)
        result = pipeline.ingest_auto(str(sources), str(vault))

        assert result["total_files"] == 3
        assert len(result["converted"]) == 3
        assert result["dest_dirs"] == ["raw/sources/ai", "raw/sources/inbox", "raw/sources/writing"]
        assert (vault / "raw" / "sources" / "ai" / "AI调研报告_pdf.md").exists()
        assert (vault / "raw" / "sources" / "writing" / "文案笔记.md").exists()
        assert (vault / "raw" / "sources" / "inbox" / "杂项.md").exists()


class TestIngestToVault:
    """投递逻辑"""

    @pytest.fixture
    def vault(self, tmp_path):
        v = tmp_path / "vault"
        (v / "01-raw" / "markitdown-output").mkdir(parents=True)
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
        assert "01-raw" in result["output_dir"] and "inbox" in result["output_dir"]
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
