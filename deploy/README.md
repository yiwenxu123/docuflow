# DocuFlow 轻量化版本

## 🚀 快速开始

### 1. 一键安装
```bash
python install.py
```

### 2. 启动应用

#### macOS/Linux:
```bash
# Web界面（推荐）
./start_docuflow.sh web

# 图形界面
./start_docuflow.sh gui

# 命令行
./start_docuflow.sh cli input.docx output.md
```

#### Windows:
```cmd
# Web界面（推荐）
start_docuflow.bat web

# 图形界面
start_docuflow.bat gui

# 命令行
start_docuflow.bat cli input.docx output.md
```

## 📱 访问地址

Web界面: http://localhost:5003

## 🔧 系统要求

- Python 3.8+
- 50MB 可用空间
- 网络连接（首次安装依赖）

## 📋 支持格式

- Word (.docx) ↔ Markdown
- HTML (.html, .htm) ↔ Markdown, DOCX
- PDF (.pdf) → Markdown
- Excel (.xlsx, .xls) → Markdown

## 🆘 故障排除

### 依赖问题
```bash
pip install -r requirements.txt --user --upgrade
```

### 权限问题
```bash
chmod +x start_docuflow.sh
```

### 端口占用
修改 main_web.py 中的端口号，或关闭占用端口的程序。
