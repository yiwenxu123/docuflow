# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [Unreleased] - Phase 3 content quality

### 新增
- HTML 正文抽取：用 trafilatura 提取文章主体并输出 Markdown，失败时回退 pandoc
- 图片附件：本地图片复制到 `attachments/<文档键>/` 并重写链接；远程图片保留原 URL
- 扫描 PDF 检测：抽样判断文字量；安装 `ocrmypdf` 时自动 OCR，否则给出明确失败提示
- `ingest --ocr auto|off` 控制 OCR 策略
- Frontmatter 的 `engine` 记录实际引擎：`trafilatura`、`markitdown`、`pdfplumber`、`openpyxl`、`pandoc`、`ocrmypdf+...`

### 变更
- 删除 Gist 专用的全局删词与 CSS 清洗；正常词（`Code`、`Share`、`Star`、`Fork`）不再被删除
- Markdown 清理只做安全规范化，保留列表/代码块缩进和自动链接
- 图片附件只允许来源目录内的本地文件，避免把任意绝对路径复制进 vault
- 测试增加到 91 个，全部通过

### 质量结论
- 真实 PDF 对比：现有 pdfplumber 解析字数更多，但存在表格重复和页内噪声；MarkItDown 输出更干净
- 本轮不引入 Docling：当前文本型 PDF 用 MarkItDown/现有解析足够；复杂版面或表格需求出现后再评估
- OCR 执行路径未在本机验证（未安装 ocrmypdf）；扫描检测与失败提示已验证

### 已知限制
- PDF/DOCX 内嵌图片尚未提取；仅 Markdown/HTML 中的本地图片会落盘
- 远程图片不会下载，只保留 URL
- PPTX、EPUB 仍不支持

## [2.0.0-phase2] - 2026-10-24

### 新增
- SQLite 状态库：记录来源/输出/哈希/结果，默认 `~/Library/Application Support/DocuFlow/state.db`，可用 `DOCUFLOW_STATE_DB` 覆盖
- Frontmatter：`title` / `source` / `source_type` / `captured_at` / `converted_at` / `converter` / `engine` / `source_hash` / `content_hash` / `language` / `pages` / `attachments`
- 去重：同一来源文件跳过；不同格式但内容相同也跳过
- 写入安全：原子写入；同名文件追加内容哈希后缀，绝不覆盖
- CLI：`ingest --dry-run --json --allow-duplicate`、`status`、`doctor`
- 每次运行生成 `runs/<id>.json` 报告；`--json` 输出稳定结构
- 测试：新增状态库、frontmatter、去重、不覆盖、dry-run、CLI JSON 与 20 文件 Gate 2

### 变更
- `ingest` 返回 `converted` / `skipped` / `planned` / `failed`，GUI 显示跳过数量
- Markdown/TXT 源文件改为轻量规范化，不再删除 `Code`、`Share` 等正常词，保留图片链接
- 已有 frontmatter 的 Markdown 完整保留原字段，投递元数据写入 `docuflow` 子块
- GUI 多文件投递合并为一次 run，不再拆成多条状态记录
- MarkItDown 可用性探测增加缓存与超时，避免启动慢导致 `--markitdown` 时好时坏
- 测试从 56 个增加到 77 个，全部通过

### 已知限制
- MarkItDown 仍使用本机 `~/markitdown-env` 路径；Phase 3 改为标准安装
- HTML 的 Gist 专用清洗仍在；Phase 3 替换为正文抽取
- 尚未实现图片附件落盘、OCR、PPTX/EPUB

## [2.0.0-phase1] - 2026-10-24

### 移除
- RAG 全家桶：分块、向量索引、语义检索、`/kb` 问答、`llm_qa`、`vector_store` 及相关测试
- Web 界面：`main_web.py`、Flask 上传/下载/统计页面、`templates/`、`static/`
- LLM Wiki 遗留：项目检测、`raw/sources` 自动分类、旧 `status` 命令、桌面投递箱 watcher
- 兼容壳与历史包袱：`main_cli.py`、交互式 CLI、`clean_filtered_file.py`、桌面快捷方式脚本
- 过度设计：统计面板、性能监控、缓存、重试框架、`utils/logger.py`、`utils/performance.py`、`utils/error_handler.py`
- 虚假格式承诺：PPTX、EPUB、PDF 导出从支持矩阵和文档中移除
- `legacy_tests/` 与一次性产物（日志、测试大文件、旧输出）归档到本地 `archive/`

### 变更
- 项目定位收缩为**知识库收件箱网关**：只做“转 Markdown + 投递到 Obsidian 收件箱”
- 默认投递目录改为 `01-raw/inbox`，不再根据 `markitdown-output` 是否存在隐式切换
- `kb_cli.py` 只保留 `ingest`；配置文件与 `utils/file_utils.py` 收敛为单一事实来源
- 启动器不再静默安装 Homebrew/依赖；缺失环境时给出明确提示
- CI 移除已删除入口的引用，改为安装 `requirements-dev.txt`
- 测试从 110 个收缩到 56 个，全部通过

### 当时的已知限制（去重/覆盖/契约已在 Phase 2 修复）
- 尚未实现内容哈希去重、原子写入、frontmatter、manifest、`--dry-run`/`--json`
- 尚未实现扫描版 PDF 的 OCR
- 同名文件仍可能覆盖

## [1.3.0] - 2026-08-04

### 新增
- `kb_cli.py ingest`：投递素材到 Obsidian vault（自动检测当前打开的 vault，默认输出到 `01-raw/markitdown-output/`），与 Obsidian + LLM Wiki 工作流衔接
- `converter/kb_pipeline.py`：`detect_obsidian_vault` / `default_vault_dest` / `ingest_to_vault`

### 变更
- 项目定位调整：**知识库素材预处理工具**（Obsidian 的"原料车间"），分块/向量检索/问答降级为可选通用能力
- README 重构：ingest 为核心用法，明确与 LLM Wiki 的分工

### 新增测试
- `tests/test_ingest.py`：vault 检测、目标目录选择、投递逻辑（10 用例）

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
