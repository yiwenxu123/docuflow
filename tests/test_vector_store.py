#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量检索测试

覆盖 HashEmbedder 确定性、VectorStore 索引/检索/持久化/去重/过滤，
以及 get_embedder 自动选择逻辑。
"""

import json
import os

import pytest

from converter.vector_store import (
    HashEmbedder, OpenAICompatibleEmbedder, VectorStore, get_embedder,
)


def make_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


SAMPLE_RECORDS = [
    {"id": "a1", "source": "/docs/llm.md", "title": "LLM 知识库", "section": "核心理念",
     "chunk_index": 0, "total_chunks": 2, "char_count": 100,
     "text": "知识库的核心是让 LLM 持续积累并维护结构化笔记，而不是每次重新检索。"},
    {"id": "a2", "source": "/docs/llm.md", "title": "LLM 知识库", "section": "架构",
     "chunk_index": 1, "total_chunks": 2, "char_count": 90,
     "text": "架构分三层：原始素材、LLM 生成的 wiki 页面、以及查询时的检索层。"},
    {"id": "b1", "source": "/docs/obsidian.md", "title": "Obsidian 笔记", "section": "双链笔记",
     "chunk_index": 0, "total_chunks": 1, "char_count": 80,
     "text": "Obsidian 使用双向链接组织笔记，支持图谱视图与 Markdown 存储。"},
    {"id": "c1", "source": "/docs/python.md", "title": "Python 编程", "section": "向量检索",
     "chunk_index": 0, "total_chunks": 1, "char_count": 70,
     "text": "Python 中实现向量检索可以使用 numpy 计算余弦相似度，检索最相似的文本块。"},
]


class TestHashEmbedder:
    """本地哈希 Embedding"""

    def test_deterministic(self):
        e = HashEmbedder()
        v1 = e.embed("知识库 向量 检索")
        v2 = e.embed("知识库 向量 检索")
        assert (v1 == v2).all()
        assert v1.shape == (512,)

    def test_normalized(self):
        e = HashEmbedder()
        v = e.embed("测试文本")
        assert abs(float(v @ v) - 1.0) < 1e-4

    def test_similar_texts_close(self):
        e = HashEmbedder()
        a = e.embed("向量检索的相似度计算")
        b = e.embed("向量检索的相似度计算与排序")
        c = e.embed("今天天气很好适合出门散步")
        assert float(a @ b) > float(a @ c)


class TestVectorStore:
    """向量存储与检索"""

    @pytest.fixture
    def store_and_jsonl(self, tmp_path):
        jsonl = tmp_path / "chunks.jsonl"
        make_jsonl(jsonl, SAMPLE_RECORDS)
        store = VectorStore(str(tmp_path / "index"))
        embedder = HashEmbedder()
        added = store.add_from_jsonl(str(jsonl), embedder)
        return store, embedder, jsonl

    def test_index_adds_all(self, store_and_jsonl):
        store, _, _ = store_and_jsonl
        assert store.count() == 4

    def test_search_finds_related(self, store_and_jsonl):
        store, embedder, _ = store_and_jsonl
        results = store.search("如何用 Python 做向量检索", embedder, top_k=3)
        assert len(results) > 0
        # Python 向量检索块应排在前列
        assert results[0].chunk_id == "c1"

    def test_search_returns_text_and_metadata(self, store_and_jsonl):
        store, embedder, _ = store_and_jsonl
        results = store.search("Obsidian 笔记", embedder, top_k=1)
        assert results[0].chunk_id == "b1"
        assert results[0].text
        assert results[0].source == "/docs/obsidian.md"
        assert 0.0 <= results[0].score <= 1.0

    def test_search_filter_by_source(self, store_and_jsonl):
        store, embedder, _ = store_and_jsonl
        results = store.search("知识库", embedder, top_k=10, filter_source="llm.md")
        assert all("llm.md" in r.source for r in results)
        assert len(results) == 2

    def test_persistence(self, store_and_jsonl, tmp_path):
        store, embedder, jsonl = store_and_jsonl
        # 重新加载（新实例，从磁盘读）
        store2 = VectorStore(str(tmp_path / "index"))
        assert store2.count() == 4
        results = store2.search("numpy 余弦相似度", embedder, top_k=1)
        assert len(results) == 1
        assert results[0].text

    def test_idempotent_reindex(self, store_and_jsonl):
        store, _, jsonl = store_and_jsonl
        embedder = HashEmbedder()
        # 重复索引同一 jsonl 不应重复添加
        added = store.add_from_jsonl(str(jsonl), embedder)
        assert added == 0
        assert store.count() == 4

    def test_search_empty_store(self, tmp_path):
        store = VectorStore(str(tmp_path / "empty"))
        assert store.search("任何内容", HashEmbedder()) == []

    def test_clear(self, store_and_jsonl, tmp_path):
        store, _, _ = store_and_jsonl
        store.clear()
        assert store.count() == 0


class TestEmbedderSelection:
    """Embedding 引擎自动选择"""

    def test_auto_prefers_api_key(self, monkeypatch):
        monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
        e = get_embedder(engine="auto")
        assert isinstance(e, OpenAICompatibleEmbedder)

    def test_auto_falls_back_to_hash(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        e = get_embedder(engine="auto")
        assert isinstance(e, HashEmbedder)

    def test_force_hash_ignores_key(self, monkeypatch):
        monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
        e = get_embedder(engine="hash")
        assert isinstance(e, HashEmbedder)

    def test_force_openai_without_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        with pytest.raises(RuntimeError):
            get_embedder(engine="openai")
