# DocuFlow GUI 问题解决方案

## 问题描述

在 macOS 系统上运行 DocuFlow 时遇到 Qt 平台插件错误：

```
qt.qpa.plugin: Could not find the Qt platform plugin "cocoa" in ""
This application failed to start because no Qt platform plugin could be initialized.
```

## 问题原因

1. **Qt 库兼容性问题**：PySide6/PyQt5 在某些 macOS 版本上存在平台插件加载问题
2. **Python 版本兼容性**：Python 3.13 与某些 Qt 版本存在兼容性问题
3. **系统依赖缺失**：macOS 缺少必要的图形界面支持库
4. **环境变量配置**：Qt 插件路径未正确设置

## 已尝试的解决方案

### 1. 环境变量设置
- 设置 `QT_PLUGIN_PATH`
- 设置 `QT_QPA_PLATFORM_PLUGIN_PATH`
- 设置 `DYLD_LIBRARY_PATH`
- 设置 `QT_QPA_PLATFORM="cocoa"`

### 2. Qt 库版本切换
- 从 PyQt5 切换到 PySide6
- 尝试不同版本的 PySide6 (6.9.1 → 6.8.0.2)
- 卸载冲突的 Qt 库

### 3. 插件路径验证
- 确认 `libqcocoa.dylib` 文件存在
- 检查插件依赖关系
- 验证文件权限

### 4. 替代 GUI 框架
- 尝试使用 tkinter（但系统未安装 `_tkinter` 模块）

## 当前解决方案：命令行版本

由于 GUI 问题难以在当前环境下解决，我们创建了一个功能完整的命令行版本：

### 使用命令行版本

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行命令行版本
python main_cli.py
```

### 命令行版本功能

1. **查看支持的格式**：显示所有支持的输入和输出格式
2. **单文件转换**：转换单个文档文件
3. **批量转换**：批量转换目录中的所有支持文件
4. **交互式操作**：友好的用户界面和错误提示

### 命令行版本优势

- ✅ **稳定可靠**：避免 GUI 相关的兼容性问题
- ✅ **功能完整**：包含所有核心转换功能
- ✅ **易于使用**：清晰的菜单和提示
- ✅ **跨平台**：在任何支持 Python 的系统上运行
- ✅ **资源占用低**：无需加载 GUI 框架

## 未来 GUI 解决方案

### 方案 1：系统级解决

```bash
# 安装 tkinter 支持（需要重新编译 Python）
brew install python-tk

# 或者使用系统 Python
/usr/bin/python3 -m pip install --user -r requirements.txt
```

### 方案 2：Docker 容器

创建包含完整 GUI 支持的 Docker 容器：

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    python3-tk \
    libqt5gui5 \
    libqt5widgets5 \
    libqt5core5a
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

### 方案 3：Web 界面

使用 Flask/FastAPI 创建 Web 界面：

```python
from flask import Flask, render_template, request, send_file
from converter.document_converter import DocumentConverter

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/convert', methods=['POST'])
def convert():
    # 处理文件上传和转换
    pass
```

### 方案 4：原生应用

使用 PyInstaller 打包为原生应用：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main_cli.py
```

## 推荐使用方式

### 当前推荐：命令行版本

对于日常使用，推荐使用命令行版本 `main_cli.py`：

1. **稳定可靠**：无 GUI 兼容性问题
2. **功能完整**：支持所有转换功能
3. **易于自动化**：可集成到脚本中

### 脚本化使用

也可以直接使用转换器类：

```python
from converter.document_converter import DocumentConverter

converter = DocumentConverter()
success, output_file, error = converter.convert_file(
    'input.pdf', 'markdown', 'output_dir'
)
```

## 总结

DocuFlow 的核心转换功能完全正常，PDF 转 Markdown 等功能已经过充分测试。GUI 问题是环境特定的，不影响程序的核心功能。命令行版本提供了完整的功能访问，是当前最佳的使用方式。