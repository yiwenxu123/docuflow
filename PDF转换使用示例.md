# DocuFlow PDF转Markdown功能使用指南

## 功能概述

DocuFlow支持将PDF文档转换为Markdown格式，保持文档的基本结构和内容。该功能使用PyPDF2和pdfplumber库进行文本提取，并通过智能文本清理算法优化转换质量。

## 主要特性

- ✅ 支持单个PDF文件转换
- ✅ 支持批量PDF文件转换
- ✅ 自动文本清理和格式优化
- ✅ 多页文档支持
- ✅ 中英文混合文档支持
- ✅ 自动生成Markdown标题和页面分割

## 使用方法

### 1. 单个文件转换

```python
from converter.document_converter import DocumentConverter

# 初始化转换器
converter = DocumentConverter()

# 转换单个PDF文件
result = converter.convert_file('input.pdf', 'output.md')
if result:
    print("转换成功！")
else:
    print("转换失败")
```

### 2. 批量文件转换

```python
from converter.document_converter import DocumentConverter

# 初始化转换器
converter = DocumentConverter()

# 批量转换目录中的所有PDF文件
results = converter.batch_convert_directory('/path/to/pdf/files')
print(f"成功转换 {len(results)} 个文件")
```

### 3. 使用命令行工具

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python3 test_pdf_converter.py
```

## 转换质量优化

### 文本清理功能

转换器包含智能文本清理功能，可以：

- 移除PDF特有的CID字符
- 修复常见的字符分割问题
- 处理编码问题和乱码
- 优化空白字符和换行符
- 过滤无意义的短行

### 支持的文档类型

- 标准PDF文档
- 扫描PDF（需要包含可提取的文本层）
- 多页PDF文档
- 中英文混合文档

## 输出格式

转换后的Markdown文件包含：

```markdown
# 文档标题

> 本文档由DocuFlow从PDF自动转换生成

## 第 1 页

[页面内容]

## 第 2 页

[页面内容]
```

## 依赖库

- PyPDF2: PDF文本提取
- pdfplumber: 高级PDF处理
- python-docx: Word文档支持
- beautifulsoup4: HTML处理
- lxml: XML解析
- reportlab: PDF生成（用于测试）

## 安装依赖

```bash
pip install PyPDF2 pdfplumber python-docx beautifulsoup4 lxml reportlab
```

## 测试文件

项目包含以下测试文件：

- `test_pdf_converter.py`: 主要测试脚本
- `create_test_pdf.py`: 创建测试PDF文件
- `create_test_pdf2.py`: 创建第二个测试PDF文件
- `test_document.pdf`: 测试PDF文件1
- `test_document2.pdf`: 测试PDF文件2

## 注意事项

1. **文本质量**: 转换质量取决于原PDF的文本层质量
2. **图像内容**: 目前不支持图像和表格的转换
3. **复杂格式**: 复杂的PDF格式可能需要手动调整
4. **文件大小**: 建议处理中小型PDF文件以获得最佳性能

## 故障排除

### 常见问题

1. **无法提取文本**: 检查PDF是否包含可提取的文本层
2. **乱码问题**: 确保PDF使用标准编码
3. **依赖库错误**: 确保在虚拟环境中安装了所有依赖

### 调试方法

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 测试PDF内容
import pdfplumber
with pdfplumber.open('test.pdf') as pdf:
    for page in pdf.pages:
        print(page.extract_text())
```

## 更新日志

- v1.0: 基础PDF转Markdown功能
- v1.1: 改进文本清理算法
- v1.2: 添加批量转换支持
- v1.3: 优化中英文混合文档处理