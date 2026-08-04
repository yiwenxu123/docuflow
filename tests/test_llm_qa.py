#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 问答模块测试

覆盖：检索+生成（mock API）、无 key 降级、API 失败降级、空索引。
"""

import json

import pytest

from converter.llm_qa import _chat_model, answer_question, chat_completion
from converter.vector_store import HashEmbedder, VectorStore


@pytest.fixture
def kb_store(tmp_path):
    """构造一个小型向量索引"""
    jsonl = tmp_path / "chunks.jsonl"
    records = [
        {"id": "a1", "source": "/docs/a.md", "title": "知识库", "section": "架构",
         "chunk_index": 0, "total_chunks": 1, "char_count": 50,
         "text": "知识库分三层：原始素材、LLM 生成的 wiki 页面、检索层。"},
        {"id": "a2", "source": "/docs/b.md", "title": "Python", "section": "向量",
         "chunk_index": 0, "total_chunks": 1, "char_count": 50,
         "text": "numpy 计算余弦相似度实现向量检索。"},
    ]
    with open(jsonl, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    store = VectorStore(str(tmp_path / "index"))
    store.add_from_jsonl(str(jsonl), HashEmbedder())
    return str(tmp_path / "index")


class TestAnswerQuestion:
    """问答主流程"""

    def test_no_key_falls_back_to_sources(self, kb_store, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        result = answer_question("知识库架构", kb_store, engine="hash")
        assert result["llm_used"] is False
        assert len(result["sources"]) > 0
        assert "知识库" in result["answer"]

    def test_api_failure_falls_back(self, kb_store, monkeypatch):
        monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-invalid")

        def boom(*args, **kwargs):
            raise RuntimeError("HTTP Error 400: Bad Request")

        import converter.llm_qa as llm_qa
        monkeypatch.setattr(llm_qa, "chat_completion", boom)
        result = answer_question("知识库架构", kb_store, engine="hash")
        assert result["llm_used"] is False
        assert result["error"]
        assert len(result["sources"]) > 0

    def test_llm_used_on_success(self, kb_store, monkeypatch):
        monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")

        def fake_chat(api_key, base_url, model, messages, timeout=60):
            assert messages[0]["role"] == "system"
            assert "参考资料" in messages[1]["content"]
            return "根据资料，知识库分三层架构。"

        import converter.llm_qa as llm_qa
        monkeypatch.setattr(llm_qa, "chat_completion", fake_chat)
        result = answer_question("知识库架构", kb_store, engine="hash")
        assert result["llm_used"] is True
        assert "三层架构" in result["answer"]
        assert result["sources"]

    def test_empty_index(self, tmp_path):
        store = VectorStore(str(tmp_path / "empty"))
        result = answer_question("任何问题", str(tmp_path / "empty"), engine="hash")
        assert result["sources"] == []
        assert "未找到" in result["answer"]


class TestChatHelpers:
    """辅助函数"""

    def test_chat_model_dashscope_default(self, monkeypatch):
        monkeypatch.delenv("OPENAI_CHAT_MODEL", raising=False)
        assert _chat_model("https://dashscope.aliyuncs.com/compatible-mode/v1") == "qwen-plus"

    def test_chat_model_openai_default(self, monkeypatch):
        monkeypatch.delenv("OPENAI_CHAT_MODEL", raising=False)
        assert _chat_model("https://api.openai.com/v1") == "gpt-4o-mini"

    def test_chat_model_env_override(self, monkeypatch):
        monkeypatch.setenv("OPENAI_CHAT_MODEL", "my-model")
        assert _chat_model("https://any") == "my-model"

    def test_chat_completion_real_call_raises_on_bad_key(self):
        """无效 key 应抛出异常（不静默）"""
        with pytest.raises(Exception):
            chat_completion(
                "sk-invalid-key-for-test",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "qwen-plus",
                [{"role": "user", "content": "hi"}],
                timeout=15,
            )
