#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""状态库与哈希测试"""

from pathlib import Path

from converter.state import StateStore, sha256_bytes, sha256_file, sha256_text


class TestHashes:
    def test_bytes_and_text(self):
        assert sha256_bytes(b"abc") == sha256_text("abc")
        assert len(sha256_text("abc")) == 64

    def test_file_hash(self, tmp_path):
        p = tmp_path / "a.txt"
        p.write_text("abc", encoding="utf-8")
        assert sha256_file(p) == sha256_text("abc")


class TestStateStore:
    def test_record_and_find_success(self, tmp_path):
        state = StateStore(tmp_path / "state.db")
        state.record_success(
            "s1", "c1", "/src/a.md", "/vault/a.md", "标题", "docuflow", "builtin"
        )
        assert state.find_success_by_source("s1")["output_path"] == "/vault/a.md"
        assert state.find_success_by_content("c1")["title"] == "标题"
        assert state.find_success_by_source("missing") is None

    def test_failure_does_not_block_retry(self, tmp_path):
        state = StateStore(tmp_path / "state.db")
        state.record_failure("s1", "", "/src/a.pdf", "boom")
        assert state.find_success_by_source("s1") is None

    def test_run_summary_and_report(self, tmp_path):
        state = StateStore(tmp_path / "state.db")
        state.record_success("s1", "c1", "/src/a.md", "/vault/a.md", "A", "docuflow", "builtin")
        state.record_failure("s2", "", "/src/b.pdf", "bad pdf")

        run_id = state.start_run()
        report = {"converted": ["/vault/a.md"], "failed": [{"file": "/src/b.pdf"}]}
        state.finish_run(
            run_id,
            {"total": 2, "converted": 1, "skipped": 0, "failed": 1},
            report,
        )
        report_path = state.write_report(run_id, report)
        assert report_path.exists()

        summary = state.summary()
        assert summary["documents"]["success"] == 1
        assert summary["documents"]["failed"] == 1
        assert summary["last_run"]["id"] == run_id
        assert "report_json" not in summary["last_run"]
        assert summary["recent_runs"][0]["converted"] == 1
        assert summary["recent_failures"][0]["source_path"] == "/src/b.pdf"
