# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [Unreleased]

## [1.2.0] - 2026-08-04

### 新增
- Web 知识库问答页（`/kb`）：源文档入库 → 向量索引 → 检索 + LLM 生成回答（OpenAI 兼容 API），无 API key 或调用失败时自动降级为检索结果
- `converter/llm_qa.py`：RAG 问答模块（检索 → 上下文组装 → Chat API 生成）
- CHANGELOG 规范

### 变更
- `main_web.py` 新增 `/kb`、`/kb/process`、`/kb/ask` 路由，知识库目录默认 `~/DocuFlow_KB`（`DOCUFLOW_KB_DIR` 可覆盖）

## [1.1.0] - 2026-08-04

### 新增
- 知识库管道：`kb_cli.py process/chunk/index/search` 子命令
  - 文档集 → 干净 Markdown → 语义分块（标题层级 + 重叠）→ chunks.jsonl
  - 零依赖向量检索：本地哈希 Embedding（离线）+ OpenAI 兼容 API（DashScope/OpenAI），失败自动降级
- 正式 pytest 测试套件（78+ 用例，`tests/`）
- CLI 批量转换支持（`cli.py file1 file2 -f .md -o out/`）

### 修复
- PDF/Excel 转换崩溃（`PDF_SUPPORT` 未定义）
- README 与实现不一致（批量用法、缺失启动器引用）

### 变更
- 单文件 2174 行重构为 6 个处理器模块（mixin 模式）
- requirements.txt 精简：44 → 10 个运行时依赖
- 合并重复的 MarkItDown 集成类
- git 仓库清理（165 个遗留文件移除、.gitignore 完善）

## [1.0.0] - 2025-08-02

### 新增
- 首次稳定发布：GUI（PySide6）/ Web（Flask）/ CLI 三端文档转换
- 支持 PDF/DOCX/XLSX/PPTX/MD/HTML 互转（Pandoc + pdfplumber + openpyxl 等）
- MarkItDown 集成（LLM 友好 Markdown 输出）
- 内容清理（GitHub Gist 页面结构去除、图片过滤）
