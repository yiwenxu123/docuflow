#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pandoc 处理器 Mixin

负责 pandoc 命令执行、格式路由与错误信息翻译。
"""

import os
import subprocess
from typing import Any, Optional

from exceptions import ConversionError


class PandocProcessorMixin:
    """pandoc 执行与格式路由逻辑"""

    def _convert_with_markitdown(self, input_path: str, output_path: str) -> str:
        """使用MarkItDown进行文件转换

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径

        Returns:
            str: 输出文件路径

        Raises:
            ConversionError: 转换失败时
        """
        try:
            self.logger.debug(f"使用MarkItDown转换文件: {input_path} -> {output_path}")
            self.last_engine = "markitdown"

            # 调用MarkItDown进行转换
            result_path = self.markitdown_integration.convert_file(
                input_file=input_path,
                output_file=output_path,
                use_plugins=True,
                keep_data_uris=False
            )

            # 验证输出文件是否生成
            if not os.path.exists(result_path):
                raise ConversionError(
                    "MarkItDown转换完成但输出文件未生成",
                    error_code="MARKITDOWN_OUTPUT_NOT_CREATED",
                    details={'expected_output_file': result_path}
                )

            # 应用清理和过滤
            # 读取转换后的内容
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 清理内容
            cleaned_content = self._clean_content(
                content=content,
                content_type='markdown',
                filter_images=self.filter_images,
                clean_content=self.clean_content
            )

            # 写回清理后的内容
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)

            return result_path

        except Exception as e:
            # 清理临时文件
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass

            if isinstance(e, ConversionError):
                raise
            else:
                raise ConversionError(
                    f"MarkItDown转换失败: {str(e)}",
                    error_code="MARKITDOWN_CONVERSION_FAILED",
                    details={'error': str(e), 'error_type': type(e).__name__}
                )

    def _convert_with_pandoc(self, input_path: str, output_path: str, input_format: str, output_format: str) -> str:
        """使用pandoc执行转换

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            input_format: 输入格式
            output_format: 输出格式

        Returns:
            str: 输出文件路径

        Raises:
            ConversionError: 转换失败
        """
        # PDF转换使用专门的处理方法
        if input_format.lower() == ".pdf" and output_format.lower() == ".md":
            self.last_engine = "pdfplumber"
            return self._convert_pdf_to_markdown(input_path, output_path)

        # PDF转HTML使用专门的处理方法
        if input_format.lower() == ".pdf" and output_format.lower() in [".html", ".htm"]:
            self.last_engine = "pdfplumber"
            return self._convert_pdf_to_html(input_path, output_path)

        # PDF转TXT使用专门的处理方法
        if input_format.lower() == ".pdf" and output_format.lower() == ".txt":
            self.last_engine = "pdfplumber"
            return self._convert_pdf_to_txt(input_path, output_path)

        # Excel转Markdown使用专门的处理方法
        if input_format.lower() in [".xlsx", ".xls"] and output_format.lower() == ".md":
            self.last_engine = "openpyxl"
            return self._convert_excel_to_markdown(input_path, output_path)

        # Excel转TXT使用专门的处理方法
        if input_format.lower() in [".xlsx", ".xls"] and output_format.lower() == ".txt":
            self.last_engine = "openpyxl"
            return self._convert_excel_to_txt(input_path, output_path)

        # Excel转HTML使用专门的处理方法
        if input_format.lower() in [".xlsx", ".xls"] and output_format.lower() in [".html", ".htm"]:
            self.last_engine = "openpyxl"
            return self._convert_excel_to_html(input_path, output_path)

        # HTML转Markdown使用专门的处理方法（正文抽取）
        if input_format.lower() in [".html", ".htm"] and output_format.lower() == ".md":
            self.last_engine = "pandoc"
            return self._convert_html_to_clean_markdown(input_path, output_path)

        self.last_engine = "pandoc"

        # 准备pandoc命令
        cmd = ["pandoc", input_path, "-o", output_path]

        # 添加格式参数（移除点号前缀并转换格式名称）
        from_format = input_format[1:] if input_format.startswith('.') else input_format
        to_format = output_format[1:] if output_format.startswith('.') else output_format

        # 格式名称映射（Pandoc使用的标准格式名称）
        format_mapping = {
            'md': 'markdown',
            'htm': 'html',
            'txt': 'markdown'  # 纯文本文件使用markdown格式处理
        }

        # 转换格式名称
        from_format = format_mapping.get(from_format.lower(), from_format)
        to_format = format_mapping.get(to_format.lower(), to_format)

        # 对于某些格式，不使用+smart参数
        if from_format.lower() in ['docx', 'xlsx', 'xls', 'pdf']:
            cmd.extend(["--from", from_format])
        else:
            cmd.extend(["--from", f"{from_format}+smart"])

        if to_format.lower() in ['docx', 'xlsx', 'xls', 'pdf']:
            cmd.extend(["--to", to_format])
        else:
            cmd.extend(["--to", f"{to_format}+smart"])

        # 为HTML输出添加UTF-8编码声明
        if output_format.lower() in [".html", ".htm"]:
            cmd.extend(["--metadata", "charset=utf-8", "--standalone"])

        # 添加特定格式的参数
        if input_format.lower() == ".pdf" and output_format.lower() in [".docx", ".html"]:
            cmd.extend(["--extract-media=."])

        # Word转HTML特殊处理（确保中文编码正确）
        if input_format.lower() == ".docx" and output_format.lower() in [".html", ".htm"]:
            cmd.extend(["--wrap=none"])

        # 添加额外的pandoc参数
        conversion_config = getattr(self.config, 'conversion', None)
        if conversion_config and hasattr(conversion_config, 'pandoc_extra_args') and conversion_config.pandoc_extra_args:
            cmd.extend(conversion_config.pandoc_extra_args)

        try:
            # 记录执行的命令
            self.logger.debug(f"执行pandoc命令: {' '.join(cmd)}")

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.COMMAND_TIMEOUT
            )

            # 记录命令执行结果
            self.logger.debug(f"pandoc返回码: {result.returncode}")
            if result.stdout:
                self.logger.debug(f"pandoc stdout: {result.stdout}")
            if result.stderr:
                self.logger.debug(f"pandoc stderr: {result.stderr}")

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "未知错误"
                # 将技术性错误转换为用户友好的提示
                user_friendly_msg = self._translate_error_message(error_msg, input_format, output_format)

                # 记录详细错误信息
                self.logger.error(f"pandoc转换失败: {error_msg}")

                raise ConversionError(
                    user_friendly_msg,
                    error_code="PANDOC_CONVERSION_FAILED",
                    details={
                        'command': ' '.join(cmd),
                        'return_code': result.returncode,
                        'stderr': result.stderr,
                        'stdout': result.stdout,
                        'original_error': error_msg
                    }
                )

            # 验证输出文件是否生成
            if not os.path.exists(output_path):
                raise ConversionError(
                    "转换完成但输出文件未生成",
                    error_code="OUTPUT_FILE_NOT_CREATED",
                    details={'expected_output': output_path}
                )

            return output_path

        except subprocess.TimeoutExpired:
            raise ConversionError(
                f"转换超时（超过{self.config.COMMAND_TIMEOUT}秒）",
                error_code="CONVERSION_TIMEOUT",
                details={'timeout': self.config.COMMAND_TIMEOUT, 'command': ' '.join(cmd)}
            )

    def _translate_error_message(self, error_msg: str, input_format: str, output_format: str) -> str:
        """将技术性错误信息转换为用户友好的提示

        Args:
            error_msg: 原始错误信息
            input_format: 输入格式
            output_format: 输出格式

        Returns:
            str: 用户友好的错误提示
        """
        error_msg_lower = error_msg.lower()

        # DOCX文件相关错误
        if "couldn't unpack docx container" in error_msg_lower or "docx container" in error_msg_lower:
            return "DOCX文件可能已损坏或格式不正确，请检查文件是否能正常打开"

        if "zip" in error_msg_lower and input_format.lower() == ".docx":
            return "DOCX文件内部结构异常，可能是文件损坏或不是标准的DOCX格式"

        # PDF文件相关错误
        if "pdf" in error_msg_lower and "parse" in error_msg_lower:
            return "PDF文件解析失败，可能是加密PDF或文件损坏"

        if "pdf" in error_msg_lower and "extract" in error_msg_lower:
            return "无法从PDF中提取文本内容，可能是扫描版PDF或图片PDF"

        # 权限相关错误
        if "permission denied" in error_msg_lower or "access denied" in error_msg_lower:
            return "文件访问权限不足，请检查文件是否被其他程序占用或权限设置"

        # 文件不存在或路径错误
        if "no such file" in error_msg_lower or "file not found" in error_msg_lower:
            return "找不到指定的文件，请检查文件路径是否正确"

        # 内存不足
        if "out of memory" in error_msg_lower or "memory" in error_msg_lower:
            return "内存不足，请尝试转换较小的文件或关闭其他程序释放内存"

        # 编码相关错误
        if "encoding" in error_msg_lower or "utf" in error_msg_lower:
            return "文件编码格式不支持，请尝试将文件保存为UTF-8编码"

        # 格式不支持
        if "format not supported" in error_msg_lower or "unknown format" in error_msg_lower:
            return f"不支持从{input_format}格式转换为{output_format}格式"

        # 网络相关错误（如果有远程资源）
        if "network" in error_msg_lower or "connection" in error_msg_lower:
            return "网络连接问题，无法下载文件中的远程资源"

        # Pandoc未安装或版本问题
        if "pandoc" in error_msg_lower and ("not found" in error_msg_lower or "command not found" in error_msg_lower):
            return "Pandoc工具未安装或未正确配置，请安装Pandoc后重试"

        # 文件格式损坏
        if "corrupt" in error_msg_lower or "invalid" in error_msg_lower:
            return "文件格式损坏或不完整，请检查原文件是否正常"

        # 默认情况：提供通用的友好提示
        if len(error_msg) > 100:  # 如果错误信息太长，提供简化版本
            return f"文件转换失败，可能是文件格式问题或文件损坏。建议检查原文件是否正常打开"
        else:
            return f"转换失败：{error_msg}。请检查文件格式和完整性"
