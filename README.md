# DocuFlow — 知识库收件箱工具

## 定位

DocuFlow 现在只做一件事：

> 把 PDF / Word / Excel / HTML / Markdown / 纯文本转成 Markdown，投递到 Obsidian 知识库的收件箱（默认 `01-raw/inbox`）。

它是知识库的“收件箱网关”，不是文档转换全家桶，也不是 RAG 平台。

**明确不做：**

- 不做 RAG、向量检索、问答页面；
- 不做 Web 服务；
- 不做按文件名自动分类；
- 不做 md→pdf/docx 反向导出（PDF 导出需要 LaTeX，当前不声明支持）；
- 不绑定 LLM Wiki；只认 Obsidian vault。

当前是 v2.0 收缩后的过渡版本：RAG/Web/LLM Wiki 遗留已删除，去重、frontmatter、原子写入、OCR 会在下一阶段补上。**在下一阶段完成前，同名文件仍可能被覆盖，请先备份或使用独立目录试投。**

## 安装

```bash
brew install pandoc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

MarkItDown 是可选引擎；当前沿用本机 `~/markitdown-env/bin/markitdown`，下一阶段会改为标准安装。

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
```

投递规则：

- 目标目录缺省为 `01-raw/inbox`，不再根据 `markitdown-output` 是否存在自动切换；
- 非 Markdown 源文件输出为 `<原名>_<格式>.md`，避免同名覆盖；
- 当前阶段没有内容哈希去重，重复投递会生成同名文件（可能覆盖）。

### 2. GUI

```bash
./venv/bin/python3 main_pyside.py
```

或双击 `DocuFlow-极速启动器.command`。启动器只检查 pandoc 和 venv，不会静默安装 Homebrew 或依赖。

GUI 有两个动作：

- **开始转换**：只转换到指定目录；
- **投递到知识库**：转换并投递到 Obsidian 收件箱。

下一阶段会把两个动作合并成一个“转换并投递”。

### 3. 仅转换，不投递

```bash
./venv/bin/python3 cli.py input.docx -f .md
./venv/bin/python3 cli.py a.pdf b.docx -f .md -o output_dir/
```

## 当前实际支持

| 输入 | 可用输出 | 说明 |
|---|---|---|
| PDF | Markdown / HTML / TXT | 仅文本型 PDF；扫描件没有 OCR |
| DOCX | Markdown / HTML / TXT | 依赖 pandoc |
| XLSX | Markdown / HTML / TXT | 依赖 openpyxl/pandas |
| Markdown | HTML / TXT / DOCX | 依赖 pandoc |
| HTML / HTM | Markdown / TXT / DOCX | 会做正文清理 |
| TXT | Markdown / HTML / DOCX | 依赖 pandoc |

**暂不支持：** PPTX、EPUB、扫描版 PDF 的 OCR、PDF 导出。

## 目录约定

```text
<vault>/
  01-raw/
    inbox/          # DocuFlow 默认投递位置
```

如果你的 vault 没有 `01-raw/inbox`，可以用 `--dest` 明确指定，DocuFlow 会创建目录。

## 开发与测试

```bash
pip install -r requirements-dev.txt
pytest -q
```

当前测试覆盖：核心转换、CLI、错误处理、HTML 清理、MarkItDown 集成、Obsidian vault 检测与投递。

## 下一步

1. 新 `ingest` 契约：frontmatter、内容哈希去重、原子写入、manifest、`--dry-run`、`--json`；
2. 引擎：MarkItDown 扶正，复杂 PDF 用 Docling，扫描件检测 + OCR；
3. 体验：GUI 合并动作、Finder 快捷动作、launchd watcher；
4. 用 50 个真实文件验证可用率，再决定是否继续投入。

## 历史

- v1.x 曾包含 Web 界面、RAG 问答、LLM Wiki 自动分类、桌面投递箱等；这些功能已在 v2.0 收缩中移除。
- 变更记录见 [CHANGELOG.md](CHANGELOG.md)。
