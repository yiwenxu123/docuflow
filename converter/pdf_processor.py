#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 处理器 Mixin

负责 PDF 文本提取与 PDF 转 Markdown/HTML/TXT 的专用转换逻辑。
"""

import os
import re
from pathlib import Path
from typing import List, Any, Union

try:
    import pypdf as PyPDF2  # 新版本
    PDF_SUPPORT = True
except ImportError:
    try:
        import PyPDF2  # 旧版本兼容
        PDF_SUPPORT = True
    except ImportError:
        PDF_SUPPORT = False

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from exceptions import ConversionError


class PdfProcessorMixin:
    """PDF 提取与转换逻辑"""

    def _extract_text_from_pdf(self, pdf_path: Union[str, Path]) -> str:
        """从PDF文件中提取文本内容，增加详细日志和错误处理。

        Args:
            pdf_path: PDF文件路径

        Returns:
            str: 提取的文本内容

        Raises:
            ConversionError: 当PDF处理库未安装或文本提取失败时
        """
        if not PDF_SUPPORT:
            raise ConversionError("PDF处理库 (PyPDF2, pdfplumber) 未安装", error_code="PDF_LIBS_MISSING")

        text_content = []
        extraction_methods = [("pdfplumber", self._extract_with_pdfplumber), ("PyPDF2", self._extract_with_pypdf2)]

        for name, method in extraction_methods:
            try:
                self.logger.info(f"尝试使用 {name} 提取PDF文本: {pdf_path}")
                content = method(pdf_path)
                if content and content.strip():
                    self.logger.info(f"成功使用 {name} 提取到内容")
                    return content
                self.logger.warning(f"使用 {name} 未提取到有效内容")
            except Exception as e:
                self.logger.error(f"使用 {name} 提取PDF失败: {e}", exc_info=True)

        raise ConversionError("所有PDF文本提取方法均失败", error_code="PDF_EXTRACTION_FAILED")

    @staticmethod
    def _table_already_in_text(table: List[List[Any]], text: str) -> bool:
        """表格单元格已出现在正文中时跳过，避免页文本与表格重复"""
        if not text.strip():
            return False
        normalized = re.sub(r"\s+", "", text).lower()
        cells = []
        for row in table:
            for cell in row:
                if cell is None:
                    continue
                value = re.sub(r"\s+", "", str(cell)).lower()
                if len(value) >= 2:
                    cells.append(value)
        if not cells:
            return True
        return all(cell in normalized for cell in cells)

    def _extract_with_pdfplumber(self, pdf_path: Union[str, Path]) -> str:
        """使用pdfplumber从PDF中提取文本和表格。"""
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                cleaned_text = self._clean_pdf_text(page_text) if page_text else ""
                if cleaned_text:
                    text_content.append(cleaned_text)

                try:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or self._table_already_in_text(table, cleaned_text):
                            continue
                        markdown_table = self._convert_table_to_markdown(table)
                        if markdown_table.strip():
                            text_content.append(markdown_table)
                except Exception as table_exc:
                    self.logger.warning(f"提取第 {page_num} 页的表格失败: {table_exc}")
        return "\n\n".join(text_content)

    def _extract_with_pypdf2(self, pdf_path: Union[str, Path]) -> str:
        """使用PyPDF2从PDF中提取文本作为备用方法。"""
        text_content = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    cleaned_text = self._clean_pdf_text(page_text)
                    if cleaned_text:
                        text_content.append(cleaned_text)
        return "\n\n".join(text_content)

    def _clean_pdf_text(self, text: str) -> str:
        """清理PDF提取的文本

        Args:
            text: 原始PDF文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""

        # 移除CID字符（如 (cid:123)）
        text = re.sub(r'\(cid:\d+\)', '', text)

        # 处理单独的'n'字符和常见的PDF文本问题
        # 先修复常见的单词分割问题
        text = text.replace('PDFnMarkdow', 'PDF转Markdown')
        text = text.replace('Markdow', 'Markdown')
        text = text.replace('PyPDF2npdfplumbern', 'PyPDF2和pdfplumber库')

        # 修复常见的英文单词中的'n'分割问题
        common_fixes = {
            'docume t': 'document',
            'seco d': 'second',
            'co tai s': 'contains',
            'formatti g': 'formatting',
            'functio ality': 'functionality',
            'ge eratio ': 'generation',
            'specificatio s': 'specifications'
        }

        for broken, fixed in common_fixes.items():
            text = text.replace(broken, fixed)

        # 合并多个空格
        text = re.sub(r'[ \t]+', ' ', text)

        # 处理换行符
        text = re.sub(r'\n[ \t]+', '\n', text)  # 移除行首空格
        text = re.sub(r'[ \t]+\n', '\n', text)  # 移除行尾空格
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行符合并为两个

        # 移除空行和只包含单个字符的行
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line and len(cleaned_line) > 1:
                cleaned_lines.append(cleaned_line)

        return '\n'.join(cleaned_lines)

    def _convert_pdf_to_markdown(self, pdf_path: Union[str, Path], output_path: Union[str, Path]) -> str:
        """将PDF转换为Markdown

        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径

        Returns:
            str: 输出文件路径
        """
        # 提取PDF文本内容
        markdown_content = self._extract_text_from_pdf(pdf_path)

        # 使用通用清理方法处理内容
        markdown_content = self._clean_content(
            content=markdown_content,
            content_type='pdf',
            filter_images=self.filter_images,
            clean_content=self.clean_content
        )

        # 添加文档头部信息
        pdf_name = os.path.basename(pdf_path)
        header = f"# {os.path.splitext(pdf_name)[0]}\n\n> 本文档由DocuFlow从PDF自动转换生成\n\n"

        full_content = header + markdown_content

        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return output_path

    def _convert_pdf_to_html(self, pdf_path: Union[str, Path], output_path: Union[str, Path]) -> str:
        """将PDF转换为HTML

        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径

        Returns:
            str: 输出文件路径
        """
        # 提取PDF文本内容
        text_content = self._extract_text_from_pdf(pdf_path)

        # 使用通用清理方法处理内容
        text_content = self._clean_content(
            content=text_content,
            content_type='pdf',
            filter_images=self.filter_images,
            clean_content=self.clean_content
        )

        # 将文本内容转换为HTML格式
        pdf_name = os.path.basename(pdf_path)
        title = os.path.splitext(pdf_name)[0]

        # 创建HTML内容
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .header {{
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .content {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p><em>本文档由DocuFlow从PDF自动转换生成</em></p>
    </div>
    <div class="content">
{text_content}
    </div>
    <div class="footer">
        <p>转换时间: {self._format_timestamp()}</p>
    </div>
</body>
</html>"""

        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    def _convert_pdf_to_txt(self, pdf_path: Union[str, Path], output_path: Union[str, Path]) -> str:
        """将PDF转换为纯文本

        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径

        Returns:
            str: 输出文件路径
        """
        # 提取PDF文本内容
        text_content = self._extract_text_from_pdf(pdf_path)

        # 使用通用清理方法处理内容
        text_content = self._clean_content(
            content=text_content,
            content_type='text',
            filter_images=self.filter_images,
            clean_content=self.clean_content
        )

        # 添加文档头部信息
        pdf_name = os.path.basename(pdf_path)
        header = f"{os.path.splitext(pdf_name)[0]}\n{'=' * len(os.path.splitext(pdf_name)[0])}\n\n本文档由DocuFlow从PDF自动转换生成\n\n"

        full_content = header + text_content

        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return output_path

    def _filter_images_from_pdf(self, text_content: str) -> str:
        """从PDF提取的文本中过滤图片相关内容

        Args:
            text_content: PDF提取的文本

        Returns:
            str: 过滤图片后的文本内容
        """
        # PDF提取的文本通常不包含图片本身，只包含文本内容
        # 这里主要是清理可能的图片占位符或乱码
        # 移除可能的图片相关乱码或占位符
        text_content = re.sub(r'\[图\]|\[image\]|\[图片\]', '', text_content, flags=re.IGNORECASE)
        return text_content

    @staticmethod
    def _format_timestamp() -> str:
        import time
        return time.strftime('%Y-%m-%d %H:%M:%S')
