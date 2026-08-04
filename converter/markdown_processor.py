#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown/HTML 处理器 Mixin

负责 Markdown/HTML 内容转换、清理（Gist 结构去除等）与图片过滤逻辑。
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Any, Union

from exceptions import ConversionError


class MarkdownProcessorMixin:
    """Markdown/HTML 转换与清理逻辑"""

    def _convert_table_to_markdown(self, table: List[List[Any]]) -> str:
        """将表格转换为Markdown格式

        Args:
            table: 表格数据，二维列表

        Returns:
            str: Markdown格式的表格
        """
        if not table or len(table) == 0:
            return ""

        markdown_rows = []

        # 处理表头
        if table[0]:
            header = "| " + " | ".join(str(cell) if cell else "" for cell in table[0]) + " |"
            separator = "| " + " | ".join("---" for _ in table[0]) + " |"
            markdown_rows.append(header)
            markdown_rows.append(separator)

        # 处理数据行
        for row in table[1:]:
            if row:
                row_text = "| " + " | ".join(str(cell) if cell else "" for cell in row) + " |"
                markdown_rows.append(row_text)

        return "\n".join(markdown_rows)

    def _convert_markdown_to_html(self, markdown_content: str) -> str:
        """将Markdown内容转换为HTML

        Args:
            markdown_content: Markdown格式的内容

        Returns:
            str: HTML内容
        """
        # 创建临时Markdown文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(markdown_content)
            temp_md_path = temp_md.name

        try:
            # 创建临时HTML文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
                temp_html_path = temp_html.name

            # 使用Pandoc将Markdown转换为HTML
            cmd = [
                "pandoc", temp_md_path, "-o", temp_html_path,
                "--from", "markdown+smart",
                "--to", "html+smart",
                "--standalone",
                "--metadata", "charset=utf-8"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.COMMAND_TIMEOUT
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "未知错误"
                self.logger.error(f"Pandoc Markdown转HTML失败: {error_msg}")
                raise ConversionError(
                    f"Markdown转HTML失败: {error_msg}",
                    error_code="MD_TO_HTML_CONVERSION_FAILED",
                    details={
                        'command': ' '.join(cmd),
                        'stderr': result.stderr,
                        'stdout': result.stdout
                    }
                )

            # 读取生成的HTML内容
            with open(temp_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 清理临时文件
            os.unlink(temp_html_path)

            return html_content

        finally:
            # 清理临时Markdown文件
            if os.path.exists(temp_md_path):
                os.unlink(temp_md_path)

    def _convert_markdown_to_txt(self, markdown_content: str) -> str:
        """将Markdown内容转换为纯文本

        Args:
            markdown_content: Markdown格式的内容

        Returns:
            str: 纯文本内容
        """
        # 移除Markdown标记
        txt_content = markdown_content

        # 移除标题标记
        txt_content = re.sub(r'^#{1,6}\s+', '', txt_content, flags=re.MULTILINE)

        # 移除表格分隔符
        txt_content = re.sub(r'\|[-\s:]+\|', '', txt_content)

        # 移除表格边框，但保留内容
        txt_content = re.sub(r'^\|', '', txt_content, flags=re.MULTILINE)
        txt_content = re.sub(r'\|$', '', txt_content, flags=re.MULTILINE)
        txt_content = re.sub(r'\|', '\t', txt_content)  # 将表格分隔符转换为制表符

        # 移除粗体和斜体标记
        txt_content = re.sub(r'\*\*(.*?)\*\*', r'\1', txt_content)
        txt_content = re.sub(r'\*(.*?)\*', r'\1', txt_content)

        # 移除引用标记
        txt_content = re.sub(r'^>\s*', '', txt_content, flags=re.MULTILINE)

        # 移除链接标记，保留链接文本
        txt_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', txt_content)

        # 移除代码块标记
        txt_content = re.sub(r'```[^\n]*\n', '', txt_content)
        txt_content = re.sub(r'```', '', txt_content)
        txt_content = re.sub(r'`([^`]+)`', r'\1', txt_content)

        # 清理多余的空行
        txt_content = re.sub(r'\n\s*\n\s*\n', '\n\n', txt_content)

        # 清理行首行尾空白
        lines = [line.strip() for line in txt_content.split('\n')]
        txt_content = '\n'.join(lines)

        return txt_content.strip()

    def _convert_html_to_clean_markdown(self, html_path: Union[str, Path], output_path: Union[str, Path]) -> str:
        """将HTML转换为清理后的Markdown（去除多余标记）

        Args:
            html_path: HTML文件路径
            output_path: 输出文件路径

        Returns:
            str: 输出文件路径

        Raises:
            ConversionError: 当转换失败时
        """
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # 首先使用pandoc进行基本转换
        temp_md_path = str(output_path) + ".temp"

        # 添加UTF-8编码支持的pandoc命令
        cmd = [
            "pandoc", str(html_path), "-o", temp_md_path,
            "--wrap=none",
            "--from", "html+smart",
            "--to", "markdown+smart"
        ]

        try:
            self.logger.debug(f"执行HTML转Markdown命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.COMMAND_TIMEOUT
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "未知错误"
                self.logger.error(f"Pandoc HTML转Markdown失败: {error_msg}")
                raise ConversionError(
                    f"HTML转Markdown失败: {error_msg}",
                    error_code="HTML_TO_MD_CONVERSION_FAILED",
                    details={
                        'command': ' '.join(cmd),
                        'stderr': result.stderr,
                        'stdout': result.stdout
                    }
                )

            # 验证临时文件是否生成
            if not os.path.exists(temp_md_path):
                raise ConversionError(
                    "Pandoc转换完成但临时文件未生成",
                    error_code="TEMP_FILE_NOT_CREATED",
                    details={'expected_temp_file': temp_md_path}
                )

            # 读取转换后的Markdown内容
            try:
                with open(temp_md_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
            except UnicodeDecodeError:
                # 如果UTF-8读取失败，尝试其他编码
                with open(temp_md_path, 'r', encoding='utf-8', errors='replace') as f:
                    markdown_content = f.read()
                self.logger.warning("HTML转Markdown时遇到编码问题，已使用替换模式处理")

            # 使用通用清理方法处理内容
            cleaned_content = self._clean_content(
                content=markdown_content,
                content_type='markdown',
                filter_images=self.filter_images,
                clean_content=self.clean_content
            )

            # 确保输出内容不为空
            if not cleaned_content.strip():
                self.logger.warning("清理后的Markdown内容为空，使用原始内容")
                cleaned_content = markdown_content

            # 写入最终输出文件
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)

                # 验证输出文件是否成功创建
                if not os.path.exists(output_path):
                    raise ConversionError(
                        "输出文件写入失败",
                        error_code="OUTPUT_FILE_WRITE_FAILED",
                        details={'output_path': output_path}
                    )

                # 验证文件大小
                file_size = os.path.getsize(output_path)
                if file_size == 0:
                    self.logger.warning(f"输出文件大小为0: {output_path}")

                self.logger.debug(f"HTML转Markdown成功，输出文件: {output_path}, 大小: {file_size} 字节")

            except (IOError, OSError) as e:
                raise ConversionError(
                    f"无法写入输出文件: {str(e)}",
                    error_code="OUTPUT_FILE_WRITE_ERROR",
                    details={'output_path': output_path, 'error': str(e)}
                )

            # 删除临时文件
            try:
                if os.path.exists(temp_md_path):
                    os.remove(temp_md_path)
            except OSError:
                self.logger.warning(f"无法删除临时文件: {temp_md_path}")

            return str(output_path)

        except subprocess.TimeoutExpired:
            # 清理临时文件
            if os.path.exists(temp_md_path):
                try:
                    os.remove(temp_md_path)
                except OSError:
                    pass

            raise ConversionError(
                f"HTML转Markdown转换超时（超过{self.config.COMMAND_TIMEOUT}秒）",
                error_code="HTML_TO_MD_TIMEOUT",
                details={'timeout': self.config.COMMAND_TIMEOUT}
            )
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_md_path):
                try:
                    os.remove(temp_md_path)
                except OSError:
                    pass

            if isinstance(e, ConversionError):
                raise
            else:
                raise ConversionError(
                    f"HTML转Markdown转换过程中发生错误: {str(e)}",
                    error_code="HTML_TO_MD_UNEXPECTED_ERROR",
                    details={'error': str(e), 'error_type': type(e).__name__}
                )

    def _clean_markdown_content(self, content: str) -> str:
        """清理Markdown内容，去除多余的HTML标记和格式

        Args:
            content: 原始Markdown内容

        Returns:
            str: 清理后的Markdown内容
        """
        # 去除HTML注释
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # 转换HTML标签为Markdown格式
        # 处理段落标签
        content = re.sub(r'</?p[^>]*>', '', content, flags=re.IGNORECASE)

        # 处理标题标签
        content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<h5[^>]*>(.*?)</h5>', r'##### \1', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<h6[^>]*>(.*?)</h6>', r'###### \1', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理粗体和斜体
        content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理代码块
        content = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'```\n\1\n```', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理链接
        content = re.sub(r'<a[^>]*href=["\']([^"\'>]*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理列表
        content = re.sub(r'<ul[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</ul>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<ol[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</ol>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理表格（简化处理）
        content = re.sub(r'<table[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</table>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<thead[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</thead>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<tbody[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</tbody>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<tr[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</tr>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<th[^>]*>(.*?)</th>', r'| \1 ', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<td[^>]*>(.*?)</td>', r'| \1 ', content, flags=re.IGNORECASE | re.DOTALL)

        # 去除所有剩余的HTML标签
        content = re.sub(r'<[^>]+>', '', content)

        # 处理HTML实体
        content = content.replace('&quot;', '"')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        content = content.replace('&nbsp;', ' ')

        # 移除文件路径引用（如 /path/to/file.md#L1-224）
        content = re.sub(r'/[^\s]+\.md#L\d+-\d+', '', content)

        # 清理GitHub Gist页面结构，但保留评论内容
        # 1. 去除GitHub Gist特定的页面结构标记
        content = re.sub(r'::+\s*\{[^\}]*\}', '', content)

        # 2. 去除所有的:::标记（GitHub Gist的div标记）
        content = re.sub(r':::+', '', content)

        # 3. 去除GitHub Gist特定的属性标记（保留Markdown链接和图片）
        # 只去除{...}标记，但不影响Markdown语法
        content = re.sub(r'(?<!\[)(?<!\!\[)\{[^}]*\}', '', content)

        # 4. 去除GitHub Gist特定的组件标记（只去除特定模式）
        # 去除 [{.class}] 模式但保留 [text](url) 和 ![alt](url) 模式
        content = re.sub(r'\[\{[^\}]*\}\]', '', content)

        # 5. 去除GitHub Gist页面结构元素（不使用单词边界，因为它们可能在链接或其他上下文中）
        gist_elements = [
            'gist.github.com',
            'Created by',
            'Star',
            'Fork',
            'Share',
            'Copy link',
            'Embed',
            'Report abuse',
            'Subscribe',
            'Download ZIP',
            'Unstar',
            'Clone via HTTPS',
            'Clone via SSH',
            'Learn more about clone URLs',
            'Save to your computer',
            'Code',
            'Revisions',
            'stargazers',
            'forks',
            'No results found',
            'Select an option'
        ]
        for element in gist_elements:
            content = content.replace(element, '')

        # 6. 去除GitHub Gist特定的HTML结构
        content = re.sub(r'\[\{[^\}]*\}\]\([^\)]*\)\{[^\}]*\}', '', content)
        content = re.sub(r'\{#[^\}]*\}', '', content)

        # 7. 去除所有的CSS类名（但保留Markdown链接中的URL）
        css_classes = [
            r'\.octicon[^\s]*',
            r'\.Button[^\s]*',
            r'\.ActionListItem[^\s]*',
            r'\.FormControl[^\s]*',
            r'\.Overlay[^\s]*',
            r'\.Counter[^\s]*',
            r'\.UnderlineNav[^\s]*',
            r'\.color-fg[^\s]*',
            r'\.d-flex[^\s]*',
            r'\.sr-only[^\s]*',
            r'\.mr-2[^\s]*',
            r'\.flex-shrink-0[^\s]*'
        ]
        for pattern in css_classes:
            content = re.sub(pattern, '', content)

        # 8. 查找评论部分的开始（通常以 [](#comments) 或类似标记开始）
        comments_start = re.search(r'^\[\]{#comments}', content, re.MULTILINE)
        if comments_start:
            # 保留评论内容，只去除页面结构
            pass
        else:
            # 尝试查找其他评论标记
            comments_start = re.search(r'^\[\]{#comments\s*}', content, re.MULTILINE)
            if comments_start:
                # 同样保留评论内容
                pass

        # 清理多余的空行（超过2个连续空行压缩为2个）
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 清理行首行尾的空白字符
        lines = content.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        content = '\n'.join(cleaned_lines)

        # 移除多余的转义字符
        content = re.sub(r'\\([^\\])', r'\1', content)

        # 清理多余的标记符号
        content = re.sub(r'\*{3,}', '**', content)  # 多个星号压缩为两个
        content = re.sub(r'_{3,}', '__', content)   # 多个下划线压缩为两个

        # 移除空的标题
        content = re.sub(r'^#+\s*$', '', content, flags=re.MULTILINE)

        # 清理表格分隔符
        content = re.sub(r'\|\s*\|', '|', content)
        content = re.sub(r'^\|\s*$', '', content, flags=re.MULTILINE)

        # 最终清理：移除开头和结尾的空行
        content = content.strip()

        return content

    def _filter_images_from_html(self, html_content: str) -> str:
        """从HTML内容中过滤图片

        Args:
            html_content: HTML内容

        Returns:
            str: 过滤图片后的HTML内容
        """
        # 移除img标签
        html_content = re.sub(r'<img[^>]*>', '', html_content, flags=re.IGNORECASE)
        # 移除picture标签
        html_content = re.sub(r'<picture[^>]*>.*?</picture>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        # 移除figure标签（通常包含图片）
        html_content = re.sub(r'<figure[^>]*>.*?</figure>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        return html_content

    def _filter_images_from_markdown(self, markdown_content: str) -> str:
        """从Markdown内容中过滤图片

        Args:
            markdown_content: Markdown内容

        Returns:
            str: 过滤图片后的Markdown内容
        """
        # 移除Markdown图片引用
        # 格式：![alt text](image URL)
        markdown_content = re.sub(r'!\[(.*?)\]\([^)]*\)', '', markdown_content)
        return markdown_content

    def _filter_images_from_word(self, content: str) -> str:
        """从Word文档转换的内容中过滤图片

        Args:
            content: Word文档转换的内容

        Returns:
            str: 过滤图片后的内容
        """
        # Word文档通过pandoc转换时，图片通常会被转换为Markdown图片引用
        # 因此使用Markdown图片过滤方法
        return self._filter_images_from_markdown(content)

    def _clean_content(self, content: str, content_type: str = 'markdown', filter_images: bool = True, clean_content: bool = True) -> str:
        """通用内容清理方法

        Args:
            content: 原始内容
            content_type: 内容类型 ('markdown', 'html', 'text', 'pdf')
            filter_images: 是否过滤图片
            clean_content: 是否清理内容

        Returns:
            str: 清理后的内容
        """
        if not clean_content:
            return content

        try:
            # 根据内容类型进行不同的处理
            if content_type == 'markdown':
                # 清理Markdown内容
                cleaned_content = self._clean_markdown_content(content)
                # 过滤图片
                if filter_images:
                    cleaned_content = self._filter_images_from_markdown(cleaned_content)
            elif content_type == 'html':
                # 过滤图片
                if filter_images:
                    content = self._filter_images_from_html(content)
                # 这里可以添加HTML特定的清理
                cleaned_content = content
            elif content_type == 'pdf':
                # 过滤图片相关内容
                if filter_images:
                    content = self._filter_images_from_pdf(content)
                cleaned_content = content
            elif content_type == 'text':
                # 纯文本内容，主要是清理空白和格式
                cleaned_content = content
                # 清理多余的空行
                cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
                # 清理行首行尾的空白字符
                lines = cleaned_content.split('\n')
                cleaned_lines = [line.strip() for line in lines]
                cleaned_content = '\n'.join(cleaned_lines)
                cleaned_content = cleaned_content.strip()
            else:
                # 默认处理
                cleaned_content = content

            # 通用清理：移除文件路径引用
            cleaned_content = re.sub(r'/[^\s]+\.md#L\d+-\d+', '', cleaned_content)

            # 最终清理
            cleaned_content = cleaned_content.strip()

            return cleaned_content
        except Exception as e:
            self.logger.error(f"内容清理失败: {e}")
            # 发生错误时返回原始内容，确保转换过程不会失败
            return content
