#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 素材处理 CLI

核心用法（Obsidian 素材预处理）：

    # 投递文档集到 Obsidian vault（自动检测当前打开的 vault，输出到 01-raw/markitdown-output）
    ./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理

    # 指定 vault 与目标子目录
    ./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 --vault ~/Documents/我的123 --dest 01-raw/inbox

    # 优先用 MarkItDown（高质量 LLM 输出）
    ./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 --markitdown

通用能力（可选）：

    # 构建独立知识库管道（转换 → 分块 → chunks.jsonl）
    ./venv/bin/python3 kb_cli.py process ~/Documents/sources ~/kb_out

    # 向量索引与语义检索（可选，Obsidian 用户可用 LLM Wiki 的 lancedb 代替）
    ./venv/bin/python3 kb_cli.py index ~/kb_out/chunks.jsonl ~/kb_out/.vector
    ./venv/bin/python3 kb_cli.py search "知识库的核心理念" ~/kb_out/.vector --top-k 5
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from converter.kb_pipeline import (
    KBChunker, KnowledgeBasePipeline, detect_obsidian_vault, default_vault_dest,
    detect_llmwiki_project, llmwiki_ingest_target,
)
from converter.vector_store import VectorStore, get_embedder


def cmd_process(args) -> int:
    """执行完整管道：转换 + 分块 + 输出"""
    try:
        chunker = KBChunker(max_chars=args.chunk_size, overlap=args.overlap)
        pipeline = KnowledgeBasePipeline(chunker=chunker)
        stats = pipeline.run(args.source, args.output, use_markitdown=args.markitdown)
    except Exception as e:
        print(f"❌ 管道执行失败: {e}", file=sys.stderr)
        return 1

    print(f"✅ 处理完成: {stats['converted']}/{stats['total_files']} 个文件 → {stats['chunks']} 个块")
    print(f"   输出目录: {Path(args.output).resolve()}")
    if stats["failed"]:
        print(f"   ⚠️ {len(stats['failed'])} 个文件失败:")
        for f in stats["failed"]:
            print(f"      - {f['file']}: {f['error']}")
    return 0


def cmd_chunk(args) -> int:
    """仅对已有 Markdown 目录执行分块"""
    try:
        chunker = KBChunker(max_chars=args.chunk_size, overlap=args.overlap)
        md_dir = Path(args.md_dir)
        md_files = sorted(p for p in md_dir.rglob("*.md") if p.is_file())
        if not md_files:
            print("❌ 目录中没有找到 .md 文件", file=sys.stderr)
            return 1

        all_chunks = []
        for md in md_files:
            all_chunks.extend(chunker.chunk_document_file(str(md)))

        import json
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            for c in all_chunks:
                f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
        print(f"✅ 分块完成: {len(md_files)} 个文件 → {len(all_chunks)} 个块 → {out}")
        return 0
    except Exception as e:
        print(f"❌ 分块失败: {e}", file=sys.stderr)
        return 1


def _is_api_engine(engine: str) -> bool:
    """该引擎是否可能调用远程 API（可降级）"""
    if engine == "openai":
        return True
    if engine == "auto":
        return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("DASHSCOPE_API_KEY"))
    return False


def _resolve_embedder(engine: str, api_key: Optional[str] = None):
    """获取 Embedding 引擎；API 引擎失败时自动降级本地哈希并提示"""
    try:
        return get_embedder(engine=engine, api_key=api_key)
    except Exception as e:
        print(f"⚠️ Embedding 引擎初始化失败（{e}），降级为本地哈希引擎（离线可用，效果一般）", file=sys.stderr)
        return get_embedder(engine="hash")


def cmd_index(args) -> int:
    """构建向量索引（API 引擎失败自动降级本地哈希）"""
    embedder = _resolve_embedder(args.engine, args.api_key)
    store = VectorStore(args.index_dir)
    try:
        added = store.add_from_jsonl(args.jsonl, embedder)
    except Exception as e:
        if _is_api_engine(args.engine):
            print(f"⚠️ {args.engine} 引擎调用失败（{e}），降级为本地哈希引擎重试", file=sys.stderr)
            try:
                embedder = get_embedder(engine="hash")
                added = store.add_from_jsonl(args.jsonl, embedder)
            except Exception as e2:
                print(f"❌ 索引失败: {e2}", file=sys.stderr)
                return 1
        else:
            print(f"❌ 索引失败: {e}", file=sys.stderr)
            return 1
    print(f"✅ 索引完成: 新增 {added} 块，索引共 {store.count()} 块（引擎: {embedder.name()}）")
    print(f"   索引目录: {Path(args.index_dir).resolve()}")
    return 0


def cmd_search(args) -> int:
    """向量检索（API 引擎失败自动降级本地哈希）"""
    embedder = _resolve_embedder(args.engine, args.api_key)
    store = VectorStore(args.index_dir)
    try:
        results = store.search(
            args.query, embedder, top_k=args.top_k, filter_source=args.source
        )
    except Exception as e:
        if _is_api_engine(args.engine):
            print(f"⚠️ {args.engine} 引擎调用失败（{e}），降级为本地哈希引擎重试", file=sys.stderr)
            try:
                embedder = get_embedder(engine="hash")
                results = store.search(
                    args.query, embedder, top_k=args.top_k, filter_source=args.source
                )
            except Exception as e2:
                print(f"❌ 检索失败: {e2}", file=sys.stderr)
                return 1
        else:
            print(f"❌ 检索失败: {e}", file=sys.stderr)
            return 1

    if not results:
        print("（无结果：索引为空或未匹配）")
        return 0

    print(f"🔍 查询: {args.query}（引擎: {embedder.name()}）")
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] 相似度 {r.score:.4f}")
        print(f"    来源: {r.source}")
        print(f"    章节: {r.title} > {r.section}" if r.section else f"    章节: {r.title}")
        preview = r.text[:150].replace("\n", " ")
        print(f"    内容: {preview}{'...' if len(r.text) > 150 else ''}")
    return 0


def cmd_ingest(args) -> int:
    """投递素材：优先 LLM Wiki 项目，其次 Obsidian vault"""
    vault_dir = args.vault or detect_llmwiki_project() or detect_obsidian_vault()
    if not vault_dir:
        print("❌ 未检测到 LLM Wiki 项目或 Obsidian vault，请用 --vault 指定路径", file=sys.stderr)
        return 1
    vault_dir = os.path.expanduser(vault_dir)
    if not os.path.isdir(vault_dir):
        print(f"❌ 目标路径不存在: {vault_dir}", file=sys.stderr)
        return 1

    # 智能目标：LLM Wiki 项目 → 自动分类投递；普通 vault → 按结构选择
    if (Path(vault_dir) / ".llm-wiki").exists():
        try:
            pipeline = KnowledgeBasePipeline()
            if args.dest:
                result = pipeline.ingest_to_vault(
                    args.source, vault_dir, dest_subdir=args.dest, use_markitdown=args.markitdown
                )
                dest_desc = args.dest
            else:
                result = pipeline.ingest_auto(args.source, vault_dir, use_markitdown=args.markitdown)
                dest_desc = "自动分类 → " + ", ".join(result.get("dest_dirs", []))
        except Exception as e:
            print(f"❌ 投递失败: {e}", file=sys.stderr)
            return 1
    else:
        dest = args.dest or default_vault_dest(vault_dir)
        try:
            pipeline = KnowledgeBasePipeline()
            result = pipeline.ingest_to_vault(
                args.source, vault_dir, dest_subdir=dest, use_markitdown=args.markitdown
            )
            dest_desc = dest
        except Exception as e:
            print(f"❌ 投递失败: {e}", file=sys.stderr)
            return 1

    print(f"✅ 投递完成: {len(result['converted'])}/{result['total_files']} 个文件")
    print(f"   目标: {result['output_dir']} ({dest_desc})")
    if result["failed"]:
        print(f"   ⚠️ {len(result['failed'])} 个文件失败:")
        for f in result["failed"]:
            print(f"      - {f['file']}: {f['error']}")
    if (Path(vault_dir) / ".llm-wiki").exists():
        print("   下一步：LLM Wiki 将自动检测并处理这些素材（可在 Activity 面板查看）")
    else:
        print("   下一步：在 Obsidian 中查看素材目录")
    return 0


def cmd_watch(args) -> int:
    """桌面投递箱：监听文件夹，新文件自动投递到知识库"""
    import shutil
    import time

    box = Path(os.path.expanduser(args.box))
    box.mkdir(parents=True, exist_ok=True)
    processed_dir = box / "_processed"
    failed_dir = box / "_failed"
    processed_dir.mkdir(exist_ok=True)
    failed_dir.mkdir(exist_ok=True)

    vault_dir = args.vault or detect_llmwiki_project() or detect_obsidian_vault()
    if not vault_dir:
        print("❌ 未检测到 LLM Wiki 项目或 Obsidian vault（--vault 可指定）", file=sys.stderr)
        return 1
    is_llmwiki = (Path(vault_dir) / ".llm-wiki").exists()

    # 初始化：把投递箱里已有的文件先处理一轮（避免积压）
    print(f"📥 投递箱: {box}")
    print(f"🎯 目标: {vault_dir}（{'LLM Wiki 自动分类' if is_llmwiki else 'Obsidian'}）")
    print(f"⏱️  扫描间隔: {args.interval} 秒（Ctrl+C 退出）\n")

    pipeline = KnowledgeBasePipeline()
    while True:
        try:
            pending = [
                p for p in box.iterdir()
                if p.is_file() and p.suffix.lower() in {".pdf", ".docx", ".xlsx", ".md", ".txt", ".html", ".htm"}
            ]
            for src in pending:
                try:
                    if is_llmwiki and not args.dest:
                        result = pipeline.ingest_auto(str(src), vault_dir, use_markitdown=args.markitdown)
                        dest_desc = "自动分类"
                    else:
                        dest = args.dest or (llmwiki_ingest_target(vault_dir) if is_llmwiki else default_vault_dest(vault_dir))
                        result = pipeline.ingest_to_vault(str(src), vault_dir, dest_subdir=dest, use_markitdown=args.markitdown)
                        dest_desc = dest
                    if result["failed"]:
                        raise RuntimeError(result["failed"][0]["error"])
                    stamp = time.strftime("%H:%M:%S")
                    print(f"[{stamp}] ✓ {src.name} → {dest_desc}")
                    shutil.move(str(src), str(processed_dir / src.name))
                except Exception as e:
                    stamp = time.strftime("%H:%M:%S")
                    print(f"[{stamp}] ✗ {src.name}: {e}")
                    try:
                        shutil.move(str(src), str(failed_dir / src.name))
                    except OSError:
                        pass
        except KeyboardInterrupt:
            print("\n👋 投递箱已停止")
            return 0
        except Exception as e:
            print(f"⚠️ 扫描出错: {e}")

        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n👋 投递箱已停止")
            return 0


def cmd_status(args) -> int:
    """查看知识库与 LLM Wiki 处理状态"""
    try:
        import json
        from collections import Counter

        project = args.project or detect_llmwiki_project()
        if not project or not os.path.isdir(project):
            print("❌ 未检测到 LLM Wiki 项目（--project 可指定）", file=sys.stderr)
            return 1
        project = os.path.expanduser(project)
        llm_dir = Path(project) / ".llm-wiki"

        print(f"📂 LLM Wiki 项目: {project}")
        if not llm_dir.is_dir():
            print("   （缺少 .llm-wiki 目录，项目状态未知）")
            return 0

        # 素材统计
        sources = Path(project) / "raw" / "sources"
        if sources.is_dir():
            n_files = sum(1 for p in sources.rglob("*") if p.is_file())
            print(f"📄 素材文件: {n_files} 个")

        # 队列状态
        queue_path = llm_dir / "ingest-queue.json"
        if queue_path.exists():
            q = json.loads(queue_path.read_text(encoding="utf-8"))
            dist = dict(Counter(x.get("status", "unknown") for x in q))
            pending = dist.get("pending", 0) + dist.get("processing", 0)
            failed = dist.get("failed", 0)
            print(f"⏳ ingest 队列: 待处理 {pending} | 成功 {dist.get('success', 0)} | 失败 {failed} | 其他 {dist.get('unknown', 0)}")
            failed_items = [x for x in q if x.get("status") == "failed"][:5]
            for x in failed_items:
                print(f"      ✗ {x.get('sourcePath','')}: {str(x.get('error',''))[:60]}")

        # 快照时间
        snap_path = llm_dir / "file-snapshot.json"
        if snap_path.exists():
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
            ts = snap.get("updatedAt", 0)
            from datetime import datetime
            print(f"🕐 watch 快照: {datetime.fromtimestamp(ts/1000):%Y-%m-%d %H:%M:%S}")

        # wiki 页面统计
        wiki = Path(project) / "wiki"
        if wiki.is_dir():
            for sub in ["sources", "entities", "concepts"]:
                d = wiki / sub
                if d.is_dir():
                    print(f"📖 wiki/{sub}: {sum(1 for p in d.glob('*.md'))} 页")
    except Exception as e:
        print(f"❌ 状态查询失败: {e}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DocuFlow 知识库管道")
    sub = parser.add_subparsers(dest="command", required=True)

    p_process = sub.add_parser("process", help="文档集 → 干净 Markdown + 分块 JSONL")
    p_process.add_argument("source", help="源文档文件或目录")
    p_process.add_argument("output", help="输出目录（生成 md/ 与 chunks.jsonl）")
    p_process.add_argument("--markitdown", action="store_true", help="优先使用 MarkItDown 转换")
    p_process.add_argument("--chunk-size", type=int, default=1500, help="每块目标字符数（默认 1500）")
    p_process.add_argument("--overlap", type=int, default=150, help="相邻块重叠字符数（默认 150）")
    p_process.set_defaults(func=cmd_process)

    p_chunk = sub.add_parser("chunk", help="仅对 Markdown 目录分块")
    p_chunk.add_argument("md_dir", help="包含 .md 文件的目录")
    p_chunk.add_argument("output", help="输出 chunks.jsonl 路径")
    p_chunk.add_argument("--chunk-size", type=int, default=1500)
    p_chunk.add_argument("--overlap", type=int, default=150)
    p_chunk.set_defaults(func=cmd_chunk)

    p_ingest = sub.add_parser("ingest", help="投递素材（自动检测 LLM Wiki 项目 / Obsidian vault）")
    p_ingest.add_argument("source", help="源文档文件或目录")
    p_ingest.add_argument("--vault", help="目标项目/vault 路径（缺省自动检测 LLM Wiki 项目，其次 Obsidian）")
    p_ingest.add_argument("--dest", help="目标子目录（缺省 LLM Wiki: raw/sources/inbox）")
    p_ingest.add_argument("--markitdown", action="store_true", help="优先使用 MarkItDown 转换")
    p_ingest.set_defaults(func=cmd_ingest)

    p_status = sub.add_parser("status", help="查看 LLM Wiki 项目状态（队列/快照/wiki 页面）")
    p_status.add_argument("--project", help="LLM Wiki 项目路径（缺省自动检测）")
    p_status.set_defaults(func=cmd_status)

    p_watch = sub.add_parser("watch", help="桌面投递箱：监听文件夹，新文件自动投递入库")
    p_watch.add_argument("--box", default="~/Documents/素材投递箱", help="投递箱目录（默认 ~/Documents/素材投递箱）")
    p_watch.add_argument("--vault", help="目标项目/vault 路径（缺省自动检测）")
    p_watch.add_argument("--dest", help="固定目标子目录（缺省 LLM Wiki 自动分类）")
    p_watch.add_argument("--interval", type=int, default=30, help="扫描间隔秒数（默认 30）")
    p_watch.add_argument("--markitdown", action="store_true", help="优先使用 MarkItDown 转换")
    p_watch.set_defaults(func=cmd_watch)

    p_index = sub.add_parser("index", help="从 chunks.jsonl 构建向量索引")
    p_index.add_argument("jsonl", help="chunks.jsonl 路径")
    p_index.add_argument("index_dir", help="向量索引目录（如 ~/kb_out/.vector）")
    p_index.add_argument("--engine", choices=["auto", "hash", "openai"], default="auto",
                         help="Embedding 引擎（默认 auto：有 API key 用 OpenAI 兼容，否则本地哈希）")
    p_index.add_argument("--api-key", help="OpenAI 兼容 API key（缺省读环境变量）")
    p_index.set_defaults(func=cmd_index)

    p_search = sub.add_parser("search", help="语义检索")
    p_search.add_argument("query", help="查询文本")
    p_search.add_argument("index_dir", help="向量索引目录")
    p_search.add_argument("--top-k", type=int, default=5)
    p_search.add_argument("--source", help="按来源文件路径子串过滤")
    p_search.add_argument("--engine", choices=["auto", "hash", "openai"], default="auto")
    p_search.add_argument("--api-key", help="OpenAI 兼容 API key")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
