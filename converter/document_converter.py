#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 文档转换核心

组合各处理器 Mixin：
- PdfProcessorMixin: PDF 文本提取
- ExcelProcessorMixin: Excel 表格提取
- MarkdownProcessorMixin: Markdown/HTML 转换与清理
- PandocProcessorMixin: pandoc 执行与格式路由
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from config import config
from exceptions import (
    ConversionError,
    DocuFlowException,
    FileAccessError,
    FileSizeError,
    UnsupportedFormatError,
)

from converter.markitdown_integration import get_markitdown_integration
from converter.pdf_processor import PdfProcessorMixin
from converter.excel_processor import ExcelProcessorMixin
from converter.markdown_processor import MarkdownProcessorMixin
from converter.pandoc_processor import PandocProcessorMixin


class DocumentConverter(
    PandocProcessorMixin,
    PdfProcessorMixin,
    ExcelProcessorMixin,
    MarkdownProcessorMixin,
):
    """文档转换器"""

    def __init__(self, config_obj=None):
        self.config = config_obj or config
        self.logger = logging.getLogger(__name__)
        self._check_dependencies()

        self.conversion_map = self.config.SUPPORTED_CONVERSIONS
        self.filter_images = True
        self.clean_content = True
        self.markitdown_integration = get_markitdown_integration()
        self.use_markitdown = False
        self.last_engine = ""

    def _check_dependencies(self) -> None:
        """检查 pandoc 是否可用"""
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.COMMAND_TIMEOUT,
            )
            if result.returncode != 0:
                raise ConversionError(
                    "Pandoc 未安装或无法运行",
                    error_code="PANDOC_NOT_AVAILABLE",
                    details={"stderr": result.stderr},
                )
        except FileNotFoundError:
            raise ConversionError(
                "Pandoc 未安装，请先安装: https://pandoc.org/installing.html",
                error_code="PANDOC_NOT_INSTALLED",
            )
        except subprocess.TimeoutExpired:
            raise ConversionError(
                "Pandoc 检查超时",
                error_code="PANDOC_CHECK_TIMEOUT",
            )

    def can_convert(self, source_format: str, target_format: str) -> bool:
        source_format = source_format.lower()
        target_format = target_format.lower()
        if source_format not in self.conversion_map:
            return False
        return target_format in self.conversion_map[source_format]

    def can_convert_format(self, file_format: str) -> bool:
        file_format = file_format.lower()
        if not file_format.startswith("."):
            file_format = "." + file_format
        if file_format in self.conversion_map:
            return True
        return any(file_format in targets for targets in self.conversion_map.values())

    def convert_file(
        self,
        file_path: str,
        output_format: str,
        output_dir: Optional[str] = None,
        keep_original_name: bool = True,
        filter_images: bool = True,
        clean_content: bool = True,
        use_markitdown: bool = False,
    ) -> str:
        """转换文件

        Args:
            file_path: 源文件路径
            output_format: 目标格式（如 .md）或完整输出路径
            output_dir: 输出目录；为空时使用源文件目录
            keep_original_name: 是否保留原文件名
            filter_images: 是否过滤图片
            clean_content: 是否清理内容
            use_markitdown: 是否优先使用 MarkItDown

        Returns:
            str: 输出文件路径
        """
        self.filter_images = filter_images
        self.clean_content = clean_content
        self.use_markitdown = use_markitdown

        try:
            is_output_path = (
                os.path.sep in output_format
                or "/" in output_format
                or "\\" in output_format
            )

            if is_output_path:
                output_path_obj = Path(output_format).resolve()
                actual_output_format = output_path_obj.suffix
                if not actual_output_format:
                    raise UnsupportedFormatError(
                        f"无法从输出路径中确定文件格式: {output_format}",
                        error_code="INVALID_OUTPUT_PATH",
                    )
                output_path = output_path_obj
                output_dir = str(output_path.parent)
            else:
                actual_output_format = (
                    output_format
                    if output_format.startswith(".")
                    else "." + output_format
                )
                output_path = None

            self._validate_conversion_input(file_path, actual_output_format)

            file_path_obj = Path(file_path).resolve()
            file_dir = file_path_obj.parent
            file_base = file_path_obj.stem
            file_ext = file_path_obj.suffix

            if not self.can_convert(file_ext.lower(), actual_output_format.lower()):
                raise UnsupportedFormatError(
                    f"不支持从 {file_ext} 转换到 {actual_output_format}",
                    error_code="UNSUPPORTED_CONVERSION",
                    details={
                        "source_format": file_ext,
                        "target_format": actual_output_format,
                    },
                )

            if output_path is None:
                target_dir = Path(output_dir).resolve() if output_dir else file_dir
                output_name = (
                    f"{file_base}{actual_output_format}"
                    if keep_original_name
                    else f"{file_base}_converted{actual_output_format}"
                )
                output_path = target_dir / output_name

            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise FileAccessError(
                    f"无法创建输出目录: {output_path.parent}",
                    error_code="CREATE_DIRECTORY_FAILED",
                    details={"error": str(e)},
                )

            if (
                self.use_markitdown
                and self.markitdown_integration.is_available()
                and actual_output_format == ".md"
            ):
                return self._convert_with_markitdown(
                    str(file_path_obj), str(output_path)
                )

            return self._convert_with_pandoc(
                str(file_path_obj), str(output_path), file_ext, actual_output_format
            )

        except DocuFlowException:
            raise
        except Exception as e:
            self.logger.exception("转换失败: %s -> %s", file_path, output_format)
            raise ConversionError(
                f"转换失败: {file_path} -> {output_format}",
                error_code="CONVERSION_FAILED",
                details={"original_error": str(e), "error_type": type(e).__name__},
            )

    def _validate_conversion_input(self, file_path: str, output_format: str) -> None:
        """验证输入文件与输出格式"""
        if not os.path.exists(file_path):
            raise FileAccessError(
                f"源文件不存在: {file_path}",
                error_code="FILE_NOT_FOUND",
                details={"file_path": file_path},
            )

        if not os.access(file_path, os.R_OK):
            raise FileAccessError(
                f"无法读取文件: {file_path}",
                error_code="FILE_NOT_READABLE",
                details={"file_path": file_path},
            )

        file_size = os.path.getsize(file_path)
        max_size = self.config.conversion.max_file_size
        if file_size > max_size:
            raise FileSizeError(
                f"文件大小超过限制: {file_size} bytes > {max_size} bytes",
                error_code="FILE_TOO_LARGE",
                details={"file_size": file_size, "max_size": max_size},
            )

        if not output_format.startswith("."):
            output_format = "." + output_format
        if output_format.lower() not in self.config.files.all_output_extensions:
            raise UnsupportedFormatError(
                f"不支持的输出格式: {output_format}",
                error_code="UNSUPPORTED_OUTPUT_FORMAT",
                details={
                    "output_format": output_format,
                    "supported_formats": sorted(
                        self.config.files.all_output_extensions
                    ),
                },
            )
