#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 问答模块（RAG）

流程：向量检索相关块 → 组装上下文 → 调用 OpenAI 兼容 Chat API 生成回答。
API 不可用/失败时降级为仅返回检索结果（引用文本），保证功能不中断。

配置（环境变量）：
    DASHSCOPE_API_KEY / OPENAI_API_KEY
    OPENAI_CHAT_MODEL（默认 qwen-plus / gpt-4o-mini 按服务商适配）
"""

import json
import os
import urllib.request
from typing import Any, List

from converter.vector_store import VectorStore, get_embedder

SYSTEM_PROMPT = (
    "你是一个基于本地知识库的回答助手。只依据提供的参考资料回答用户问题；"
    "如果资料不足，明确说明。回答使用中文，并引用相关资料的章节标题。"
)


def _chat_model(base_url: str) -> str:
    """按服务商选择默认对话模型"""
    model = os.environ.get("OPENAI_CHAT_MODEL", "")
    if model:
        return model
    if "dashscope" in base_url:
        return "qwen-plus"
    return "gpt-4o-mini"


def chat_completion(api_key: str, base_url: str, model: str, messages: List[dict],
                    timeout: int = 60) -> str:
    """调用 OpenAI 兼容 Chat Completions API，返回回答文本"""
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def answer_question(query: str, index_dir: str, top_k: int = 4,
                    engine: str = "auto", api_key: str = "",
                    base_url: str = "", model: str = "") -> dict:
    """知识库问答：检索 + LLM 生成回答

    Args:
        query: 用户问题
        index_dir: 向量索引目录
        top_k: 检索块数量
        engine: embedding 引擎（auto/hash/openai）
        api_key: Chat API key（缺省读环境变量）
        base_url: Chat API base_url
        model: Chat 模型名

    Returns:
        dict: {
            answer: 回答文本（LLM 生成；不可用时为检索结果摘要）
            sources: [{source, section, score, text}]
            llm_used: bool
            error: 可选错误信息
        }
    """
    # 1. 检索（API 引擎失败自动降级本地哈希）
    store = VectorStore(index_dir)
    try:
        embedder = get_embedder(engine=engine)
        results = store.search(query, embedder, top_k=top_k)
    except Exception:
        embedder = get_embedder(engine="hash")
        results = store.search(query, embedder, top_k=top_k)

    sources = [
        {
            "source": r.source,
            "section": r.section,
            "score": r.score,
            "text": r.text,
        }
        for r in results
    ]

    if not sources:
        return {
            "answer": "知识库中未找到与问题相关的内容。请先构建索引（kb_cli.py index）或调整问题表述。",
            "sources": [],
            "llm_used": False,
        }

    # 2. 组装上下文并调用 LLM
    context_blocks = [
        f"【资料 {i+1}】来源: {s['source']} | 章节: {s['section']}\n{s['text']}"
        for i, s in enumerate(sources)
    ]
    context = "\n\n".join(context_blocks)

    chat_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
    if chat_key:
        chat_base = base_url or os.environ.get("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        chat_model = model or _chat_model(chat_base)
        try:
            answer = chat_completion(
                chat_key, chat_base, chat_model,
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"参考资料：\n{context}\n\n问题：{query}"},
                ],
            )
            return {"answer": answer, "sources": sources, "llm_used": True}
        except Exception as e:
            # LLM 失败降级：返回检索到的原文摘要
            fallback = (
                f"（LLM 回答不可用：{e}\n"
                "以下是知识库中的相关内容，供参考：）\n\n"
                + "\n\n".join(f"【{s['section']}】{s['text'][:300]}" for s in sources)
            )
            return {"answer": fallback, "sources": sources, "llm_used": False, "error": str(e)}

    # 无 API key：直接返回检索结果
    fallback = (
        "（未配置 OPENAI_API_KEY / DASHSCOPE_API_KEY，无法生成回答。以下是检索到的相关内容：）\n\n"
        + "\n\n".join(f"【{s['section']}】{s['text'][:300]}" for s in sources)
    )
    return {"answer": fallback, "sources": sources, "llm_used": False}
