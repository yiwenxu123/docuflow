#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 状态库

SQLite 记录每次投递的来源、输出、哈希与结果，用于：
- 同一文件重复投递时跳过；
- 不同格式但内容相同的文件去重；
- 查询最近运行与失败记录。
"""

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Union[str, Path], chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_state_db_path() -> Path:
    override = os.environ.get("DOCUFLOW_STATE_DB")
    if override:
        return Path(override).expanduser()
    return Path.home() / "Library" / "Application Support" / "DocuFlow" / "state.db"


class StateStore:
    """投递状态与去重记录"""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = (
            Path(db_path).expanduser() if db_path else default_state_db_path()
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.runs_dir = self.db_path.parent / "runs"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_hash TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    title TEXT,
                    status TEXT NOT NULL,
                    converter TEXT,
                    engine TEXT,
                    created_at TEXT NOT NULL,
                    error TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_documents_source
                    ON documents(source_hash, status);
                CREATE INDEX IF NOT EXISTS idx_documents_content
                    ON documents(content_hash, status);

                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    total INTEGER NOT NULL DEFAULT 0,
                    converted INTEGER NOT NULL DEFAULT 0,
                    skipped INTEGER NOT NULL DEFAULT 0,
                    failed INTEGER NOT NULL DEFAULT 0,
                    report_json TEXT
                );
                """)

    def find_success_by_source(self, source_hash: str) -> Optional[Dict[str, Any]]:
        return self._find_success("source_hash", source_hash)

    def find_success_by_content(self, content_hash: str) -> Optional[Dict[str, Any]]:
        return self._find_success("content_hash", content_hash)

    def _find_success(self, column: str, value: str) -> Optional[Dict[str, Any]]:
        with closing(self._connect()) as conn:
            row = conn.execute(
                f"""
                SELECT * FROM documents
                WHERE {column} = ? AND status = 'success'
                ORDER BY id DESC LIMIT 1
                """,
                (value,),
            ).fetchone()
        return dict(row) if row else None

    def record_success(
        self,
        source_hash: str,
        content_hash: str,
        source_path: str,
        output_path: str,
        title: str,
        converter: str,
        engine: str,
    ) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO documents (
                    source_hash, content_hash, source_path, output_path,
                    title, status, converter, engine, created_at, error
                ) VALUES (?, ?, ?, ?, ?, 'success', ?, ?, ?, NULL)
                """,
                (
                    source_hash,
                    content_hash,
                    source_path,
                    output_path,
                    title,
                    converter,
                    engine,
                    now_iso(),
                ),
            )

    def record_failure(
        self,
        source_hash: str,
        content_hash: str,
        source_path: str,
        error: str,
        converter: str = "",
        engine: str = "",
    ) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO documents (
                    source_hash, content_hash, source_path, output_path,
                    title, status, converter, engine, created_at, error
                ) VALUES (?, ?, ?, '', '', 'failed', ?, ?, ?, ?)
                """,
                (
                    source_hash,
                    content_hash,
                    source_path,
                    converter,
                    engine,
                    now_iso(),
                    error[:2000],
                ),
            )

    def start_run(self) -> int:
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute(
                "INSERT INTO runs (started_at) VALUES (?)", (now_iso(),)
            )
            return int(cursor.lastrowid)

    def finish_run(
        self, run_id: int, stats: Dict[str, int], report: Dict[str, Any]
    ) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                UPDATE runs
                SET finished_at = ?, total = ?, converted = ?, skipped = ?, failed = ?,
                    report_json = ?
                WHERE id = ?
                """,
                (
                    now_iso(),
                    stats.get("total", 0),
                    stats.get("converted", 0),
                    stats.get("skipped", 0),
                    stats.get("failed", 0),
                    json.dumps(report, ensure_ascii=False),
                    run_id,
                ),
            )

    def write_report(self, run_id: int, report: Dict[str, Any]) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / f"{run_id:06d}.json"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    def summary(self) -> Dict[str, Any]:
        with closing(self._connect()) as conn:
            counts = {"total": 0, "success": 0, "failed": 0}
            for row in conn.execute(
                "SELECT status, COUNT(*) AS n FROM documents GROUP BY status"
            ):
                counts["total"] += row["n"]
                if row["status"] in counts:
                    counts[row["status"]] = row["n"]

            last_run = conn.execute("""
                SELECT id, started_at, finished_at, total, converted, skipped, failed
                FROM runs ORDER BY id DESC LIMIT 1
                """).fetchone()
            recent_runs = conn.execute("""
                SELECT id, started_at, finished_at, total, converted, skipped, failed
                FROM runs ORDER BY id DESC LIMIT 5
                """).fetchall()
            recent_failures = conn.execute("""
                SELECT source_path, error, created_at
                FROM documents WHERE status = 'failed'
                ORDER BY id DESC LIMIT 5
                """).fetchall()

        return {
            "db_path": str(self.db_path),
            "documents": counts,
            "last_run": dict(last_run) if last_run else None,
            "recent_runs": [dict(r) for r in recent_runs],
            "recent_failures": [dict(r) for r in recent_failures],
        }
