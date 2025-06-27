# DocuFlow 示例文档

这是一个用于测试 DocuFlow 文档转换器的示例 Markdown 文档。

## 功能特性

DocuFlow 支持以下功能：

- **多格式转换**: 支持 `.docx`, `.md`, `.pdf`, `.html`, `.epub` 等格式
- **批量处理**: 可以同时转换多个文件
- **拖拽操作**: 支持文件拖拽到应用窗口
- **自定义输出**: 可设置输出目录和文件命名方式

## 支持的转换格式

| 来源格式 | 可转换为 | 用途说明 |
|---------|---------|--------|
| `.docx` | `.pdf`, `.md`, `.html` | 报告、技术文档发布 |
| `.md` | `.docx`, `.pdf`, `.html` | 技术写作、博客、发布 |
| `.pdf` | `.docx`, `.md` | 正式文件编辑或摘录 |
| `.html` | `.md` | 从网页提取内容 |
| `.epub` | `.md`, `.pdf` | 笔记提取，归档打印 |

## 代码示例

以下是一个简单的 Python 代码示例：

```python
from converter.document_converter import DocumentConverter

# 创建转换器实例
converter = DocumentConverter()

# 转换文件
output_file = converter.convert_file(
    'input.md', 
    '.pdf', 
    output_dir='/path/to/output'
)

print(f"转换完成: {output_file}")
```

## 安装说明

1. 确保已安装 Python 3.7+
2. 安装 Pandoc: `brew install pandoc`
3. 运行安装脚本: `./install.sh`
4. 启动应用: `./run_docuflow.sh`

## 使用方法

### 图形界面

1. 启动应用程序
2. 选择或拖拽文件到窗口
3. 选择输出格式
4. 点击"开始转换"

### 命令行

```bash
# 转换单个文件
python cli_converter.py sample.md -f .pdf

# 批量转换
python cli_converter.py *.md -f .html -o ./output

# 保留原文件名
python cli_converter.py document.docx -f .pdf --keep-name
```

## 技术架构

DocuFlow 基于以下技术构建：

- **核心转换**: Pandoc
- **GUI框架**: PyQt5
- **编程语言**: Python 3.7+
- **平台支持**: macOS

## 注意事项

> ⚠️ **重要提示**: PDF 转换为其他格式时可能存在格式限制，转换效果取决于原始 PDF 的结构复杂度。

## 联系我们

如果您在使用过程中遇到问题，请：

1. 查看 README.md 文档
2. 运行测试脚本: `python test_app.py`
3. 检查 Pandoc 是否正确安装

---

*感谢使用 DocuFlow 文档转换器！*