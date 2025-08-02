# DocuFlow 1.0 安装指南

## 系统要求
- Python 3.7 或更高版本
- 操作系统: Windows/macOS/Linux

## 安装步骤

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 安装系统依赖
- **macOS**: `brew install pandoc`
- **Ubuntu/Debian**: `sudo apt-get install pandoc`
- **Windows**: 从 https://pandoc.org/installing.html 下载安装

### 3. 运行程序

#### Web界面
```bash
python main_web.py
```
然后访问 http://localhost:5003

#### 命令行工具
```bash
python main_cli.py
```

#### 图形界面
```bash
python main_pyside.py
```

## 功能特性
- ✅ 多格式文档转换
- ✅ 批量处理
- ✅ 自定义参数
- ✅ 三种使用方式 (Web/CLI/GUI)
- ✅ 下载文件名自动修正

## 技术支持
如有问题，请查看README.md或提交Issue。
