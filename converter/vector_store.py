#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量向量检索（零依赖）

Embedding 双引擎：
- OpenAICompatibleEmbedder: 调用 OpenAI 兼容 Embedding API（OpenAI / DashScope 通义等）
- HashEmbedder: 本地字符 bigram 哈希特征向量，离线可用（质量一般，用于演示/兜底）

VectorStore: numpy 余弦相似度检索 + JSON 持久化。

典型用法：
    from converter.vector_store import VectorStore, get_embedder
    store = VectorStore("/path/to/kb/.vector")
    store.add_from_jsonl("/path/to/chunks.jsonl", embedder=get_embedder())
    results = store.search("知识库的核心理念")
"""

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# ---- Embedding 提供者 ----


class HashEmbedder:
    """本地字符 bigram 哈希特征向量（离线 fallback，512 维）"""

    DIM = 512

    def __init__(self, dim: int = DIM):
        self.dim = dim

    def name(self) -> str:
        return "hash"

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        text = text.lower()
        # 中英文 bigram 特征
        grams = [text[i:i + 2] for i in range(max(0, len(text) - 1))]
        if len(text) == 1:
            grams = [text]
        for gram in grams:
            h = int(hashlib.md5(gram.encode("utf-8")).hexdigest()[:8], 16)
            vec[h % self.dim] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        return np.vstack([self.embed(t) for t in texts])


class OpenAICompatibleEmbedder:
    """OpenAI 兼容 Embedding API（OpenAI / DashScope 通义等）

    通过环境变量或显式参数配置：
        OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_EMBEDDING_MODEL
        DASHSCOPE_API_KEY（DashScope 兼容模式：base_url=https://dashscope.aliyuncs.com/compatible-mode/v1）
    """

    def __init__(self, api_key: str, base_url: str = "", model: str = ""):
        import urllib.request  # 延迟导入，避免拖慢索引

        self.api_key = api_key
        if not base_url:
            base_url = os.environ.get("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.base_url = base_url.rstrip("/")

        # 默认模型按服务商适配
        if not model:
            model = os.environ.get("OPENAI_EMBEDDING_MODEL", "")
        if not model:
            if "dashscope" in self.base_url:
                model = "text-embedding-v3"
            else:
                model = "text-embedding-3-small"
        self.model = model

    def name(self) -> str:
        return f"openai:{self.model}"

    def embed(self, text: str) -> np.ndarray:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        import urllib.request
        import json as _json

        url = f"{self.base_url}/embeddings"
        payload = _json.dumps({
            "model": self.model,
            "input": texts,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = _json.loads(resp.read().decode("utf-8"))

        vectors = [item["embedding"] for item in data["data"]]
        return np.asarray(vectors, dtype=np.float32)


def get_embedder(engine: str = "auto", api_key: Optional[str] = None) -> Any:
    """自动选择 Embedding 引擎

    Args:
        engine: "auto" | "hash" | "openai"
        api_key: OpenAI 兼容 API key（缺省时读环境变量）

    Raises:
        RuntimeError: auto 模式下无可用引擎
    """
    if engine == "hash":
        return HashEmbedder()

    key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
    if engine == "openai":
        if not key:
            raise RuntimeError("openai 引擎需要 OPENAI_API_KEY 或 DASHSCOPE_API_KEY 环境变量")
        return OpenAICompatibleEmbedder(key)

    # auto：有 key 用 API，否则本地哈希
    if key:
        return OpenAICompatibleEmbedder(key)
    return HashEmbedder()


# ---- 检索结果 ----


@dataclass
class SearchResult:
    """检索结果"""
    chunk_id: str
    source: str
    title: str
    section: str
    chunk_index: int
    score: float
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "chunk_index": self.chunk_index,
            "score": round(float(self.score), 4),
            "text": self.text,
        }


# ---- 向量存储 ----


class VectorStore:
    """本地向量存储：numpy 矩阵 + JSON 元数据，余弦相似度检索"""

    def __init__(self, store_dir: str):
        self.dir = Path(store_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.vectors_path = self.dir / "vectors.npy"
        self.meta_path = self.dir / "meta.json"
        self._vectors: Optional[np.ndarray] = None
        self._meta: List[Dict[str, Any]] = []

    # ---- 索引 ----

    def add_from_jsonl(self, jsonl_path: str, embedder: Any) -> int:
        """从 chunks.jsonl 构建向量索引，返回新增块数

        Args:
            jsonl_path: chunks.jsonl 路径
            embedder: Embedding 引擎
        """
        with open(jsonl_path, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        if not records:
            return 0

        texts = [r["text"] for r in records]
        vectors = embedder.embed_batch(texts)

        existing_ids = {m["id"] for m in self._meta}
        new_meta = []
        new_vecs = []
        for rec, vec in zip(records, vectors):
            if rec["id"] in existing_ids:
                continue
            new_meta.append({
                "id": rec["id"],
                "source": rec.get("source", ""),
                "title": rec.get("title", ""),
                "section": rec.get("section", ""),
                "chunk_index": rec.get("chunk_index", 0),
                "total_chunks": rec.get("total_chunks", 0),
                "char_count": rec.get("char_count", 0),
                "text": rec.get("text", ""),
            })
            new_vecs.append(vec)

        if not new_vecs:
            return 0

        self._meta.extend(new_meta)
        new_matrix = np.vstack(new_vecs).astype(np.float32)
        if self._vectors is None:
            self._vectors = new_matrix
        else:
            self._vectors = np.vstack([self._vectors, new_matrix])

        self._persist()
        return len(new_meta)

    def _persist(self) -> None:
        if self._vectors is None:
            return
        np.save(self.vectors_path, self._vectors)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self._meta, f, ensure_ascii=False, indent=1)

    def _load(self) -> None:
        if self._vectors is not None:
            return
        if self.vectors_path.exists() and self.meta_path.exists():
            self._vectors = np.load(self.vectors_path)
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self._meta = json.load(f)
        else:
            self._vectors = None
            self._meta = []

    # ---- 检索 ----

    def search(self, query: str, embedder: Any, top_k: int = 5,
               filter_source: Optional[str] = None) -> List[SearchResult]:
        """语义检索

        Args:
            query: 查询文本
            embedder: 与索引时相同的 Embedding 引擎
            top_k: 返回条数
            filter_source: 按来源文件路径子串过滤

        Returns:
            List[SearchResult]: 按相似度降序
        """
        self._load()
        if self._vectors is None or len(self._meta) == 0:
            return []

        q_vec = embedder.embed(query).astype(np.float32)
        scores = self._vectors @ q_vec  # 已归一化 → 余弦相似度

        order = np.argsort(scores)[::-1]
        results = []
        for idx in order:
            if len(results) >= top_k:
                break
            meta = self._meta[idx]
            if filter_source and filter_source not in meta["source"]:
                continue
            results.append(SearchResult(
                chunk_id=meta["id"],
                source=meta["source"],
                title=meta["title"],
                section=meta["section"],
                chunk_index=meta["chunk_index"],
                score=float(scores[idx]),
                text=meta.get("text", ""),
            ))
        return results

    def count(self) -> int:
        self._load()
        return len(self._meta)

    def clear(self) -> None:
        self._vectors = None
        self._meta = []
        if self.vectors_path.exists():
            self.vectors_path.unlink()
        if self.meta_path.exists():
            self.meta_path.unlink()
