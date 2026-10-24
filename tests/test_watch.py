#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投递箱 watch 命令测试"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_watch(tmp_path, *extra):
    box = tmp_path / "box"
    vault = tmp_path / "vault"
    (vault / "01-raw" / "inbox").mkdir(parents=True)
    env = os.environ.copy()
    env["DOCUFLOW_STATE_DB"] = str(tmp_path / "state.db")
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "kb_cli.py"),
            "watch",
            "--box",
            str(box),
            "--vault",
            str(vault),
            "--once",
            *extra,
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    return result, box, vault


def test_watch_once_keep_originals(tmp_path):
    box = tmp_path / "box"
    box.mkdir()
    (box / "a.md").write_text("# A\n\n内容", encoding="utf-8")

    result, box, vault = run_watch(tmp_path, "--keep-originals")
    assert result.returncode == 0, result.stderr
    assert (box / "a.md").exists()
    assert (vault / "01-raw" / "inbox" / "a.md").exists()


def test_watch_moves_processed_file(tmp_path):
    box = tmp_path / "box"
    box.mkdir()
    (box / "a.md").write_text("# A\n\n内容", encoding="utf-8")

    result, box, vault = run_watch(tmp_path)
    assert result.returncode == 0, result.stderr
    assert not (box / "a.md").exists()
    assert (box / "_processed" / "a.md").exists()
    assert (vault / "01-raw" / "inbox" / "a.md").exists()


def test_watch_processes_folder(tmp_path):
    box = tmp_path / "box"
    batch = box / "batch"
    batch.mkdir(parents=True)
    (batch / "a.md").write_text("# A\n\n内容", encoding="utf-8")

    result, box, vault = run_watch(tmp_path)
    assert result.returncode == 0, result.stderr
    assert not (box / "batch").exists()
    assert (box / "_processed" / "batch" / "a.md").exists()
    assert (vault / "01-raw" / "inbox" / "a.md").exists()


def test_watch_moves_unsupported_file(tmp_path):
    box = tmp_path / "box"
    box.mkdir()
    (box / "a.xyz").write_text("unsupported", encoding="utf-8")

    result, box, vault = run_watch(tmp_path)
    assert result.returncode == 0, result.stderr
    assert (box / "_unsupported" / "a.xyz").exists()
