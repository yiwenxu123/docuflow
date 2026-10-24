# DocuFlow — 知识库收件箱工具

## 定位

DocuFlow 现在只做一件事：

> 把 PDF / Word / Excel / HTML / Markdown / 纯文本转成 Markdown，去重后投递到 Obsidian 知识库的收件箱（默认 `01-raw/inbox`）。

它是知识库的“收件箱网关”，不是文档转换全家桶，也不是 RAG 平台。

**明确不做：**

- 不做 RAG、向量检索、问答页面；
- 不做 Web 服务；
- 不做按文件名自动分类；
- 不做 md→pdf/docx 反向导出（PDF 导出需要 LaTeX，当前不声明支持）；
- 不绑定 LLM Wiki；只认 Obsidian vault。

## 当前能力

- 批量转换：PDF / DOCX / XLSX / HTML / Markdown / TXT → Markdown；
- HTML 正文抽取：用 trafilatura 去掉导航/页脚，保留文章主体；
- 图片附件：本地图片复制到 `attachments/<文档键>/` 并重写链接；
- 扫描 PDF：抽样检测文字量；安装 `ocrmypdf` 时自动 OCR，否则明确报错；
- 去重：同一来源文件跳过；不同格式但内容相同也跳过；
- 写入安全：原子写入；同名文件追加内容哈希后缀，绝不覆盖；
- Frontmatter：来源、时间、转换器、引擎、内容哈希、语言、页数、附件数；
- 报告：每次运行生成 `runs/<id>.json`，支持 `--json`；
- 状态：SQLite 记录在 `~/Library/Application Support/DocuFlow/state.db`；
- 自检：`doctor` 检查 pandoc、MarkItDown、OCR、vault 和收件箱；
- 桌面入口：简化 GUI、Finder 右键快捷动作、launchd 后台监听投递箱。

## 安装

```bash
brew install pandoc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

MarkItDown 是可选引擎；优先使用 `PATH` 中的 `markitdown`，同时兼容旧的 `~/markitdown-env/bin/markitdown` 安装。

扫描版 PDF 的 OCR 是可选项：

```bash
brew install ocrmypdf tesseract tesseract-lang
```

未安装时，扫描件会明确失败并提示，而不会静默输出空文件。

## 使用

### 1. 投递到知识库（核心用法）

```bash
# 自动检测当前打开的 Obsidian vault，投递到 01-raw/inbox
./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理

# 指定 vault 和目标子目录
./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 \
  --vault ~/Documents/我的123 \
  --dest 01-raw/inbox

# 优先使用 MarkItDown
./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 --markitdown

# 预演：只报告会做什么，不写文件、不写状态
./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 --dry-run

# 机器可读报告
./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 --json

# 扫描 PDF：默认 auto（有 ocrmypdf 就 OCR）；off 表示不 OCR
./venv/bin/python3 kb_cli.py ingest ~/Downloads/扫描件 --ocr off
```

投递规则：

- 目标目录缺省为 `01-raw/inbox`；
- 非 Markdown 源文件输出为 `<原名>_<格式>.md`；
- 已成功投递过的来源文件自动跳过；
- 不同格式但正文内容相同的文件也跳过；
- 同名但内容不同的文件会输出为 `<原名>-<哈希6位>.md`，不覆盖原文件；
- 需要强制重复投递时用 `--allow-duplicate`，仍然不会覆盖文件。

### 2. 查看状态与自检

```bash
./venv/bin/python3 kb_cli.py status
./venv/bin/python3 kb_cli.py doctor
./venv/bin/python3 kb_cli.py status --json
```

`status` 显示成功/失败数量、最近运行和失败原因；`doctor` 检查 pandoc、MarkItDown、vault、收件箱写权限。

### 3. GUI

```bash
./venv/bin/python3 main_pyside.py
```

或双击 `DocuFlow-极速启动器.command`。启动器只检查 pandoc 和 venv，不会静默安装 Homebrew 或依赖。

GUI 只有一个主按钮“转换并投递”：

- 选择目标 vault；
- 确认收件箱（默认 `01-raw/inbox`）；
- 选择 OCR 策略，可勾选 MarkItDown；
- 完成后可直接打开收件箱。

GUI 不再提供“仅转换”入口；需要只转换时使用下面的 CLI。

### 4. Finder 快捷动作

安装：

```bash
./scripts/install_finder_action.sh
```

安装后，在 Finder 中选中文件或文件夹，右键选择“用 DocuFlow 投递到知识库”。结果写入 `~/Library/Logs/DocuFlow-finder.log`，并通过系统通知反馈。

如果右键菜单没有出现，请在“系统设置 > 通用 > 登录项与扩展 > Finder 扩展/快捷动作”中启用，或重启 Finder。

可用环境变量：

- `DOCUFLOW_VAULT`：指定 vault；
- `DOCUFLOW_DEST`：指定收件箱；
- `DOCUFLOW_OCR=off`：关闭 OCR；
- `DOCUFLOW_MARKITDOWN=1`：优先 MarkItDown。

### 5. 后台监听投递箱（launchd）

```bash
# 先看将写入的 LaunchAgent，不实际加载
DOCUFLOW_BOX=~/Documents/素材投递箱 ./scripts/install_watch_service.sh --dry-run

# 安装并启动
DOCUFLOW_BOX=~/Documents/素材投递箱 ./scripts/install_watch_service.sh

# 卸载
./scripts/uninstall_watch_service.sh
```

监听行为：

- 投递箱顶层的文件和文件夹都会被处理；
- 文件稳定一轮后才处理，避免复制到一半被读取；
- 成功后移入 `_processed/`，失败移入 `_failed/`，不支持的文件移入 `_unsupported/`；
- 加 `--keep-originals` 可保留原文件；
- `--once` 只处理一轮，便于调试；
- 日志：`~/Library/Logs/DocuFlow-watch.log`。

### 6. 仅转换，不投递

```bash
./venv/bin/python3 cli.py input.docx -f .md
./venv/bin/python3 cli.py a.pdf b.docx -f .md -o output_dir/
```

## 输出契约

每个 Markdown 文件以 frontmatter 开头：

```yaml
---
title: "报告标题"
source: "/Users/me/Downloads/report.pdf"
source_type: "pdf"
captured_at: "2026-10-24T11:20:00+08:00"
converted_at: "2026-10-24T11:21:03+08:00"
converter: "docuflow 2.0.0-dev"
engine: "markitdown"
source_hash: "sha256:..."
content_hash: "sha256:..."
language: "zh"
pages: 12
attachments: 0
---
```

- `source_hash` 用于识别同一来源文件；
- `content_hash` 用于识别不同格式但内容相同的文件；
- `engine` 记录实际使用的抽取引擎（如 `trafilatura`、`markitdown`、`pdfplumber`、`ocrmypdf+pdfplumber`）；
- `attachments` 是本次落盘的本地图片数量。

如果源 Markdown 已有 frontmatter，DocuFlow 会完整保留原有字段（包括 `tags`、`aliases` 及其缩进），并把本次投递元数据放在 `docuflow:` 子块下，避免覆盖你的笔记属性。

## 当前实际支持

| 输入 | 可用输出 | 说明 |
|---|---|---|
| PDF | Markdown / HTML / TXT | 文本型 PDF；扫描件安装 ocrmypdf 后自动 OCR |
| DOCX | Markdown / HTML / TXT | 依赖 pandoc |
| XLSX | Markdown / HTML / TXT | 依赖 openpyxl/pandas |
| Markdown | HTML / TXT / DOCX | 本地图片会落盘为附件 |
| HTML / HTM | Markdown / TXT / DOCX | trafilatura 正文抽取；本地图片落盘 |
| TXT | Markdown / HTML / DOCX | 依赖 pandoc |

**暂不支持：** PPTX、EPUB、PDF 导出、PDF/DOCX 内嵌图片提取、远程图片下载。

## 目录约定

```text
<vault>/
  01-raw/
    inbox/          # DocuFlow 默认投递位置
```

如果你的 vault 没有 `01-raw/inbox`，可以用 `--dest` 明确指定，DocuFlow 会创建目录。

状态库默认位置：

```text
~/Library/Application Support/DocuFlow/state.db
~/Library/Application Support/DocuFlow/runs/<id>.json
```

可用 `DOCUFLOW_STATE_DB=/path/to/state.db` 覆盖。

## 开发与测试

```bash
pip install -r requirements-dev.txt
pytest -q
```

当前测试覆盖：核心转换、CLI、错误处理、HTML 正文抽取、MarkItDown、Obsidian 检测、frontmatter、状态库、去重、不覆盖、dry-run、图片附件、OCR 检测、watch 命令、20 文件二次投递。

真实语料验证：

```bash
./venv/bin/python3 scripts/validate_corpus.py \
  --manifest archive/phase5/manifest.txt \
  --output archive/phase5/report
```

脚本使用临时 vault，不会写入真实知识库；报告输出到被忽略的 `archive/phase5/`。

## 下一步

1. Phase 5：用 50 个真实文件验证可用率，再决定是否继续投入；
2. 后续按需评估：PPTX、PDF/DOCX 内嵌图片、Docling（复杂版面/表格）。

## 历史

- v1.x 曾包含 Web 界面、RAG 问答、LLM Wiki 自动分类、桌面投递箱等；这些功能已在 v2.0 收缩中移除。
- 变更记录见 [CHANGELOG.md](CHANGELOG.md)。
