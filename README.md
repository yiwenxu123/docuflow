# DocuFlow 文档转换工具 🎯

## 📌 定位：知识库素材预处理工具（Obsidian 的"原料车间"）

DocuFlow 把**任意格式的文档**（PDF/DOCX/XLSX/网页/Gist 导出）转换为**干净的、LLM 友好的 Markdown**，投递到你的 Obsidian 知识库原始素材层，由你现有的 LLM Wiki / AI 工作流自动接管生成 wiki。

```
任意文档 → DocuFlow（拖拽/批量/深度清洗）→ 01-raw/markitdown-output/
    → Obsidian + LLM Wiki（lancedb 检索 + wiki 自动生成）接管
```

> 💡 **与 LLM Wiki 的分工**：LLM Wiki 负责"知识编译"（raw → wiki 页面的自动生成与语义检索）；DocuFlow 负责"素材预处理"（把 PDF/DOCX/网页变成干净 Markdown 送进 raw 层）。两者互补，不重复。

## ✅ 双击即用

### 🚀 推荐启动方式
**双击 `DocuFlow-极速启动器.command`** - 自动检测环境、安装依赖并启动

### 🎯 特性
- ✅ **全自动安装**：Homebrew + pandoc + Python依赖
- ✅ **智能检测**：自动识别系统环境
- ✅ **国内镜像**：使用清华镜像源，安装更快
- ✅ **拖拽/批量转换**：支持文件夹批量处理
- ✅ **深度清洗**：自动去除 Gist/HTML 页面结构残留（`gist.github.com`、CSS 类名、文件路径引用等）
- ✅ **MarkItDown 引擎**：高质量 LLM 友好输出

### 📋 支持的格式转换
| 输入格式 | 可转输出格式 |
|----------|-------------|
| **PDF** → | Markdown, TXT, HTML, DOCX |
| **DOCX** → | PDF, HTML, Markdown, EPUB |
| **Excel** → | HTML, DOCX, Markdown |
| **PPTX** → | PDF, HTML, Markdown |
| **Markdown** → | PDF, DOCX, HTML, EPUB |
| **HTML** → | PDF, DOCX, Markdown |

## 🖥️ 使用方式

#### 1. ⚡ 极速启动器（强烈推荐）
```bash
双击：DocuFlow-极速启动器.command
```
**特点**：首次安装后，后续启动仅需2-3秒，智能缓存，一键桌面

#### 2. 🎯 创建桌面快捷方式
```bash
双击：创建桌面快捷方式.command
```
**特点**：创建美观桌面图标，支持启动台和Dock栏

#### 3. 💻 命令行工具
```bash
# 转换单个文件
./venv/bin/python3 cli.py input.pdf -o output.md

# 批量转换
./venv/bin/python3 cli.py *.pdf -f md -o output_dir/

# 查看帮助
./venv/bin/python3 cli.py --help
```

#### 4. 🌐 Web界面
```bash
./venv/bin/python3 main_web.py
# 访问 http://localhost:5003
```

#### 5. 📥 投递素材到 Obsidian（核心用法）
把任意格式的文档集转换为干净 Markdown，直接投递到 Obsidian vault 的原始素材层：

```bash
# 一键投递：自动检测当前打开的 Obsidian vault，输出到 01-raw/markitdown-output/
./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理

# 指定 vault 与目标子目录
./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 \
    --vault ~/Documents/我的123 --dest 01-raw/inbox

# 优先用 MarkItDown（高质量 LLM 输出）
./venv/bin/python3 kb_cli.py ingest ~/Downloads/待整理 --markitdown
```

**行为**：
- 自动从 Obsidian 配置检测当前打开的 vault（`--vault` 可覆盖）
- 目标目录自动选择：`01-raw/markitdown-output` → `01-raw/inbox` → `01-raw` → `raw/sources` → `Inbox`（`--dest` 可覆盖）
- 转换时自动去除 Gist/HTML 页面结构残留，非 Markdown 源文件带格式后缀命名避免冲突
- 投递完成后，在 Obsidian 中由你的 LLM Wiki / AI 工作流自动接管生成 wiki

#### 6. 🧠 通用能力（可选）：分块 / 向量检索 / 问答
> ⚠️ 如果你使用 Obsidian + LLM Wiki（自带 lancedb 语义检索），以下功能可跳过。
> 保留它们是为了让 DocuFlow 在不依赖 Obsidian 的场景下也能构建独立知识库。

```bash
# 构建独立知识库管道：转换 → 语义分块（JSONL）
./venv/bin/python3 kb_cli.py process ~/Documents/sources ~/kb_out

# 向量索引 + 语义检索（无 API key 时自动用本地离线引擎，失败自动降级）
./venv/bin/python3 kb_cli.py index ~/kb_out/chunks.jsonl ~/kb_out/.vector
./venv/bin/python3 kb_cli.py search "知识库的核心理念" ~/kb_out/.vector --top-k 5

# Web 问答页（RAG）：启动 Web 后访问 http://localhost:5003/kb
./venv/bin/python3 main_web.py
```

- Embedding 引擎：检测到 `OPENAI_API_KEY`/`DASHSCOPE_API_KEY` 时用 API，否则本地哈希引擎（离线）
- API 调用失败（欠费/网络）时**自动降级**为本地引擎
- DashScope 默认模型 `text-embedding-v3`，OpenAI 默认 `text-embedding-3-small`

#### 7. 🍎 打包 .app（GUI 独立应用）
```bash
./venv/bin/pip install pyinstaller
./venv/bin/pyinstaller DocuFlow.spec --noconfirm
# 产物: dist/DocuFlow.app（双击即用，需系统已安装 pandoc）
```

## 📦 系统要求（自动安装）
- ✅ **macOS 10.15+**（自动检测）
- ✅ **Homebrew**（自动安装）
- ✅ **Python 3.8+**（自动配置）
- ✅ **Pandoc**（自动安装）
- ✅ **所有Python依赖**（自动安装）

## 🎯 首次使用（1-3分钟）
### 方式1：极速启动（推荐）
1. **双击启动**：`DocuFlow-极速启动器.command`
2. **等待安装**：首次使用自动安装依赖（1-2分钟）
3. **开始使用**：安装完成后自动启动

### 方式2：创建桌面图标
1. **双击创建**：`创建桌面快捷方式.command`
2. **桌面图标**：在桌面找到DocuFlow图标
3. **一键启动**：双击桌面图标即可启动

## ⚡ 性能优化
- **首次启动**：1-2分钟（安装依赖）
- **后续启动**：2-3秒（极速启动）
- **智能缓存**：自动跳过已安装的依赖

## 🔍 故障排除

#### 📋 日志文件
- **详细日志**：`~/Desktop/DocuFlow_启动日志.txt`
- **命令行日志**：`~/Documents/DocuFlow.log`

#### 🛠️ 常见问题
| 问题 | 解决方案 |
|------|----------|
| 网络超时 | 使用国内镜像源 |
| 权限问题 | 使用`极速启动器` |
| 依赖冲突 | 自动清理重装 |
| 启动失败 | 查看详细日志 |

#### 📞 技术支持
1. **查看日志**：打开`~/Desktop/DocuFlow_启动日志.txt`
2. **手动安装**：按日志提示操作
3. **命令行测试**：`./venv/bin/python3 main_pyside.py`

## 🎨 特色功能
- 📁 **拖拽支持**：直接拖拽文件到界面
- ⚙️ **批量处理**：支持文件夹批量转换
- 🎯 **智能识别**：自动检测文件格式
- 📊 **进度显示**：实时转换进度
- 💾 **记忆功能**：记住上次使用的设置

## 🔄 更新说明
- **v1.3.0**：Obsidian 素材投递（ingest）、定位调整、通用能力标注
- **v1.2.0**：Web 问答、RAG 模块、CI、.app 打包
- **v1.1.0**：模块化重构、批量转换、测试套件（78 用例）
- **v1.0**：基础文档转换功能（GUI/Web/CLI 三端）