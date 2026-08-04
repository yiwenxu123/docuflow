#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 集成测试

通过 subprocess 调用 cli.py，验证单文件、批量转换与错误处理。
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI = [sys.executable, str(PROJECT_ROOT / "cli.py")]


def run_cli(*args, timeout=60):
    """运行 CLI 并返回 (returncode, stdout, stderr)"""
    result = subprocess.run(
        CLI + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(PROJECT_ROOT),
    )
    return result.returncode, result.stdout, result.stderr


class TestCliSingleFile:
    """CLI 单文件转换"""

    def test_convert_with_output_path(self, sample_md, tmp_path):
        out = tmp_path / "cli_out.docx"
        code, stdout, stderr = run_cli(str(sample_md), "-f", ".docx", "-o", str(out))
        assert code == 0, stderr
        assert os.path.exists(out)

    def test_convert_without_output_uses_same_dir(self, sample_md):
        """不指定 -o 时，输出到源文件同目录（默认格式后缀）"""
        code, stdout, stderr = run_cli(str(sample_md), "-f", ".txt")
        assert code == 0, stderr
        expected = sample_md.with_suffix(".txt")
        assert os.path.exists(expected)
        expected.unlink()  # 清理

    def test_missing_input_returns_error(self, tmp_path):
        code, stdout, stderr = run_cli(str(tmp_path / "ghost.md"), "-f", ".md")
        assert code == 1
        assert "不存在" in stderr

    def test_missing_format_returns_error(self, sample_md):
        code, stdout, stderr = run_cli(str(sample_md))
        assert code == 1
        assert "格式" in stderr


class TestCliBatch:
    """CLI 批量转换"""

    def test_batch_with_output_dir(self, sample_md, sample_xlsx, tmp_path):
        out_dir = tmp_path / "cli_batch"
        code, stdout, stderr = run_cli(
            str(sample_md), str(sample_xlsx), "-f", ".html", "-o", str(out_dir)
        )
        assert code == 0, stderr
        assert (out_dir / "sample.html").exists()

    def test_batch_without_output_dir_errors(self, sample_md, sample_xlsx):
        code, stdout, stderr = run_cli(str(sample_md), str(sample_xlsx), "-f", ".html")
        assert code == 1
        assert "输出目录" in stderr

    def test_batch_with_bad_file_keeps_going(self, sample_md, tmp_path):
        bad = tmp_path / "bad.docx"
        bad.write_bytes(b"not a docx")
        out_dir = tmp_path / "cli_batch2"
        code, stdout, stderr = run_cli(
            str(sample_md), str(bad), "-f", ".html", "-o", str(out_dir)
        )
        # 好文件成功，坏文件失败 → 整体退出码 1
        assert code == 1
        assert (out_dir / "sample.html").exists()
        assert "转换失败" in stderr
