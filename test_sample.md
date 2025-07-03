# DocuFlow HTML转换测试

## 功能介绍

这是一个用于测试DocuFlow HTML输入格式支持的示例文档。

## 主要特性

- **多格式支持**：支持PDF、Word、Excel、PowerPoint、Markdown、HTML等格式
- **批量转换**：可以同时处理多个文件
- **智能输出**：默认输出到源文件所在目录
- **现代界面**：基于PySide6的现代化GUI

## 代码示例

::: highlight
以下是一个简单的Python代码示例：

    def convert_document(input_file, output_format):
        """转换文档格式"""
        converter = DocumentConverter()
        return converter.convert_file(input_file, output_format)
:::

## 支持的转换

HTML文档可以转换为以下格式：

1.  Markdown (.md)
2.  纯文本 (.txt)
3.  PDF文档 (.pdf)
4.  Word文档 (.docx)

## 注意事项

转换过程中会保持原有的文档结构和格式，但某些CSS样式可能无法完全保留。

*测试文档 - DocuFlow v2.0.0*
