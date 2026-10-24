#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_cli ingest/status 的 JSON 契约测试"""

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args, env):
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "kb_cli.py"), *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


def test_ingest_json_and_status(tmp_path):
    vault = tmp_path / "vault"
    (vault / "01-raw" / "inbox").mkdir(parents=True)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.md").write_text("# A\n\n内容", encoding="utf-8")

    env = os.environ.copy()
    env["DOCUFLOW_STATE_DB"] = str(tmp_path / "state.db")

    first = run_cli("ingest", str(src), "--vault", str(vault), "--json", env=env)
    assert first.returncode == 0, first.stderr
    first_data = json.loads(first.stdout)
    assert len(first_data["converted"]) == 1

    second = run_cli("ingest", str(src), "--vault", str(vault), "--json", env=env)
    assert second.returncode == 0, second.stderr
    second_data = json.loads(second.stdout)
    assert second_data["converted"] == []
    assert len(second_data["skipped"]) == 1

    status = run_cli("status", "--vault", str(vault), "--json", env=env)
    assert status.returncode == 0, status.stderr
    summary = json.loads(status.stdout)
    assert summary["documents"]["success"] == 1
    assert any(run["converted"] == 1 for run in summary["recent_runs"])
    assert summary["last_run"]["skipped"] == 1
