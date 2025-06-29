# DocuFlow

## 📝 项目简介

DocuFlow 是一款专为 macOS 设计的文档格式转换工具，提供简洁直观的图形界面，帮助用户高效完成常见办公和学习文档格式的转换任务，特别是在 Markdown 与传统格式之间的双向流转。

## ✨ 主要特性

- **多格式支持**：支持 `.docx`, `.md`, `.html`, `.epub` 等常用格式的相互转换
- **批量处理**：支持多文件和文件夹批量转换
- **拖拽操作**：支持文件拖拽，操作更便捷
- **自定义输出**：可自定义输出目录和文件命名方式
- **实时反馈**：转换过程中提供实时状态和进度反馈

## 🔧 支持的转换格式

| 来源格式 | 可转换为 | 用途说明 |
|---------|---------|--------|
| `.docx` | `.md`, `.html`, `.epub` | 报告、技术文档发布 |
| `.md` | `.docx`, `.html`, `.epub` | 技术写作、博客、发布 |
| `.html` | `.md` | 从网页提取内容 |
| `.epub` | `.md` | 笔记提取，归档打印 |

**注意**: PDF转换功能已移除以节省系统空间和依赖。

## 🚀 安装与使用

### 系统要求

- macOS 10.14 或更高版本
- Python 3.7 或更高版本
- [Pandoc](https://pandoc.org/installing.html) (用于文档转换)

### 安装步骤

1. 克隆或下载本仓库

```bash
git clone https://github.com/yiwenxu123/docuflow.git
cd docuflow
```

2. 安装依赖包

```bash
pip install -r requirements.txt
```

3. 安装 Pandoc

```bash
brew install pandoc
```

### 运行应用

```bash
python main.py
```

## 📖 使用指南

1. 启动应用后，可以通过以下方式添加文件：
   - 点击「选择文件」按钮
   - 点击「选择文件夹」按钮
   - 直接将文件拖拽到应用窗口

2. 从下拉菜单中选择目标格式

3. 可选：设置输出目录和文件命名选项

4. 点击「开始转换」按钮

5. 转换完成后，可以查看结果并打开输出文件夹

## 🛠️ 技术依赖

- **Pandoc**：强大的文档转换工具
- **Python + PyQt5**：提供跨平台GUI支持
- **可选**：`ebook-convert`（Calibre 工具，用于增强 epub 支持）

## 🔧 故障排除

### GUI启动问题

如果遇到 "Could not find the Qt platform plugin 'cocoa'" 错误：

1. 使用提供的启动脚本：`./run_docuflow.sh`
2. 或手动设置环境变量后运行

### 转换问题

- 确保已安装 Pandoc
- 检查输入文件格式是否受支持
- 查看应用内的错误提示信息

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题或建议，请通过 GitHub Issues 联系。