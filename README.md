# DocuFlow 文档转换工具 🎯

## ✅ 终极解决方案 - 双击即用

### 🚀 推荐启动方式
**双击 `DocuFlow-极速启动器.command`** - 自动检测环境、安装依赖并启动

### 🎯 新功能特性
- ✅ **全自动安装**：Homebrew + pandoc + Python依赖
- ✅ **智能检测**：自动识别系统环境
- ✅ **国内镜像**：使用清华镜像源，安装更快
- ✅ **详细日志**：完整安装过程记录
- ✅ **错误恢复**：提供多种备选方案

### 📋 支持的格式转换
| 输入格式 | 可转输出格式 |
|----------|-------------|
| **PDF** → | Markdown, TXT, HTML, DOCX |
| **DOCX** → | PDF, HTML, Markdown, EPUB |
| **Excel** → | HTML, DOCX, Markdown |
| **PPTX** → | PDF, HTML, Markdown |
| **Markdown** → | PDF, DOCX, HTML, EPUB |
| **HTML** → | PDF, DOCX, Markdown |

## 🖥️ 三种使用方式

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

#### 5. 🧠 知识库管道（LLM/RAG 友好）
把文档集一键转换为**干净 Markdown + 结构化分块（JSONL）**，可直接喂给 LLM/RAG 知识库：

```bash
# 处理文件夹（递归扫描 pdf/docx/xlsx/html/md）
./venv/bin/python3 kb_cli.py process ~/Documents/sources ~/kb_out

# 优先使用 MarkItDown（高质量 LLM 输出）
./venv/bin/python3 kb_cli.py process ~/sources ~/kb_out --markitdown

# 仅对已有 Markdown 目录分块
./venv/bin/python3 kb_cli.py chunk ~/kb_out/md ~/kb_out/chunks.jsonl

# 自定义块大小与重叠
./venv/bin/python3 kb_cli.py process ~/sources ~/kb_out --chunk-size 800 --overlap 100
```

**输出**：
- `md/`：转换后的干净 Markdown（按标题清理 Gist/HTML 残留）
- `chunks.jsonl`：语义分块（按标题层级切分，保留"父标题 > 子标题"上下文与相邻块重叠），每条含 `id/source/title/section/chunk_index/text` 元数据
- `manifest.json`：处理统计与失败清单

#### 6. 🔍 向量检索（本地语义搜索）
对知识库构建向量索引并语义检索（零依赖，本地隐私）：

```bash
# 构建向量索引（默认 auto：有 API key 用高质量 Embedding，否则本地离线引擎）
./venv/bin/python3 kb_cli.py index ~/kb_out/chunks.jsonl ~/kb_out/.vector

# 语义检索
./venv/bin/python3 kb_cli.py search "知识库的核心理念" ~/kb_out/.vector --top-k 5

# 按来源文件过滤
./venv/bin/python3 kb_cli.py search "查询" ~/kb_out/.vector --source llm-wiki

# 使用 OpenAI 兼容 API（OpenAI / DashScope 通义）获得高质量检索
export DASHSCOPE_API_KEY=sk-xxx        # 或 OPENAI_API_KEY
./venv/bin/python3 kb_cli.py index ~/kb_out/chunks.jsonl ~/kb_out/.vector --engine openai
./venv/bin/python3 kb_cli.py search "..." ~/kb_out/.vector --engine openai

# 强制本地离线引擎（不调用任何 API）
./venv/bin/python3 kb_cli.py index ~/kb_out/chunks.jsonl ~/kb_out/.vector --engine hash
```

**说明**：
- `--engine auto`（默认）：检测到 `OPENAI_API_KEY`/`DASHSCOPE_API_KEY` 时用 API Embedding，否则用本地哈希引擎（离线可用）
- API 调用失败（欠费/网络）时**自动降级**为本地引擎，索引不中断
- DashScope 默认模型 `text-embedding-v3`，OpenAI 默认 `text-embedding-3-small`，可用 `OPENAI_EMBEDDING_MODEL` 或 `OPENAI_BASE_URL` 覆盖

#### 7. 🌐 Web 知识库问答（RAG）
启动 Web 版后访问 `http://localhost:5003/kb`：

```bash
./venv/bin/python3 main_web.py
# 打开 http://localhost:5003/kb
```

- **入库处理**：填写源文档目录，自动完成 转换 → 分块 → 向量索引（知识库默认存 `~/DocuFlow_KB`，`DOCUFLOW_KB_DIR` 可覆盖）
- **向知识库提问**：检索相关块 + LLM 生成回答（配置 `DASHSCOPE_API_KEY`/`OPENAI_API_KEY` 后自动启用，默认模型 qwen-plus）；无 key 或调用失败时自动降级为检索结果

#### 8. 🍎 打包 .app（GUI 独立应用）
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
- **v1.2.0**：知识库管道 + 向量检索（分块/索引/语义搜索）
- **v1.1.0**：模块化重构、批量转换、测试套件（78 用例）
- **v1.0**：基础文档转换功能（GUI/Web/CLI 三端）