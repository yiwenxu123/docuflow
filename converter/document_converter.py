#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 文档转换器核心逻辑

DocumentConverter 主类，组合各处理器 Mixin：
- PdfProcessorMixin: PDF 提取与转换
- ExcelProcessorMixin: Excel 提取与转换
- MarkdownProcessorMixin: Markdown/HTML 转换与清理
- PandocProcessorMixin: pandoc 执行与格式路由
"""

import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Callable

from config import config
from exceptions import (
    ConversionError, FileAccessError, UnsupportedFormatError,
    FileSizeError, ErrorHandler, log_exception, retry_on_error
)
from utils.logger import StructuredLogger, PerformanceMonitor, get_logger

from converter.markitdown_integration import MarkItDownIntegration, get_markitdown_integration
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
    """文档转换器类"""

    def __init__(self, config_obj=None):
        """初始化文档转换器

        Args:
            config_obj: 配置对象，如果为None则使用默认配置
        """
        if config_obj is None:
            from utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            self.config = config_manager.get_config()
        else:
            self.config = config_obj
        self.logger = logging.getLogger(__name__)

        # 初始化结构化日志系统
        self.structured_logger = get_logger('document_converter')
        self.performance_monitor = PerformanceMonitor(self.structured_logger)

        # 记录系统信息
        self.structured_logger.log_system_info(
            converter_version='1.0.0',
            config_loaded=True
        )

        # 检查依赖
        self._check_dependencies()

        # 支持的转换格式映射
        self.conversion_map = self.config.SUPPORTED_CONVERSIONS

        # 统计信息
        self.stats = {
            'total_conversions': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'conversion_history': []
        }

        # 初始化过滤器设置
        self.filter_images = True
        self.clean_content = True

        # 初始化 MarkItDown 集成
        self.markitdown_integration = get_markitdown_integration()
        self.use_markitdown = False

    def _check_dependencies(self) -> None:
        """检查依赖是否安装

        Raises:
            ConversionError: 当Pandoc未安装或无法运行时
        """
        try:
            result = subprocess.run(["pandoc", "--version"],
                                   capture_output=True,
                                   text=True,
                                   check=False,
                                   timeout=self.config.COMMAND_TIMEOUT)
            if result.returncode != 0:
                raise ConversionError(
                    "Pandoc未安装或无法运行",
                    error_code="PANDOC_NOT_AVAILABLE",
                    details={'stderr': result.stderr}
                )
            self.logger.info("Pandoc依赖检查通过")
        except FileNotFoundError:
            raise ConversionError(
                "Pandoc未安装，请先安装Pandoc: https://pandoc.org/installing.html",
                error_code="PANDOC_NOT_INSTALLED"
            )
        except subprocess.TimeoutExpired:
            raise ConversionError(
                "Pandoc检查超时",
                error_code="PANDOC_CHECK_TIMEOUT"
            )

    def can_convert(self, source_format: str, target_format: str) -> bool:
        """检查是否支持从源格式转换到目标格式

        Args:
            source_format: 源文件格式（如 '.pdf'）
            target_format: 目标格式（如 '.md'）

        Returns:
            bool: 是否支持转换
        """
        source_format = source_format.lower()
        target_format = target_format.lower()

        if source_format not in self.conversion_map:
            return False
        return target_format in self.conversion_map[source_format]

    def can_convert_format(self, file_format: str) -> bool:
        """检查是否支持指定的文件格式

        Args:
            file_format: 文件格式（如 '.pdf', '.docx', '.md'）

        Returns:
            bool: 是否支持该格式
        """
        file_format = file_format.lower()
        if not file_format.startswith('.'):
            file_format = '.' + file_format

        # 检查是否作为源格式被支持
        if file_format in self.conversion_map:
            return True

        # 检查是否作为目标格式被支持
        for source_formats in self.conversion_map.values():
            if file_format in source_formats:
                return True

        return False

    @log_exception
    @retry_on_error(max_retries=2, delay=1.0, exceptions=(ConversionError,))
    def convert_file(self, file_path: str, output_format: str,
                    output_dir: Optional[str] = None,
                    keep_original_name: bool = True,
                    filter_images: bool = True,
                    clean_content: bool = True,
                    use_markitdown: bool = False) -> str:
        """转换文件

        Args:
            file_path: 源文件路径
            output_format: 输出格式 (如 .pdf, .md) 或输出文件路径
            output_dir: 输出目录，如果为None则使用源文件目录
            keep_original_name: 是否保留原文件名
            filter_images: 是否过滤图片
            clean_content: 是否清理内容（去除不必要的元素）
            use_markitdown: 是否使用MarkItDown进行转换

        Returns:
            str: 输出文件路径

        Raises:
            FileAccessError: 文件访问错误
            UnsupportedFormatError: 不支持的格式
            FileSizeError: 文件大小超限
            ConversionError: 转换失败
        """
        self.filter_images = filter_images
        self.clean_content = clean_content
        self.use_markitdown = use_markitdown
        self.stats['total_conversions'] += 1
        start_time = time.time()

        try:
            # 处理输出格式：如果是文件路径，提取扩展名和路径；如果是格式，确保以.开头
            is_output_path = os.path.sep in output_format or '/' in output_format or '\\' in output_format

            if is_output_path:
                # 这是一个文件路径，提取扩展名和目录
                output_path_obj = Path(output_format).resolve()
                actual_output_format = output_path_obj.suffix
                if not actual_output_format:
                    raise UnsupportedFormatError(
                        f"无法从输出路径中确定文件格式: {output_format}",
                        error_code="INVALID_OUTPUT_PATH",
                        details={'output_path': output_format}
                    )
                # 当提供完整路径时，直接使用该路径
                output_path = output_path_obj
                output_dir = output_path.parent
            else:
                # 这是一个格式字符串
                actual_output_format = output_format if output_format.startswith('.') else '.' + output_format
                output_path = None  # 稍后构建

            # 验证输入
            self._validate_conversion_input(file_path, actual_output_format)

            # 获取文件信息
            file_path = Path(file_path).resolve()
            file_dir = file_path.parent
            file_base = file_path.stem
            file_ext = file_path.suffix

            # 记录转换开始
            self.structured_logger.log_conversion_start(
                file_path=str(file_path),
                target_format=actual_output_format,
                input_format=file_ext,
                keep_original_name=keep_original_name
            )

            # 检查格式支持
            if not self.can_convert(file_ext.lower(), actual_output_format.lower()):
                raise UnsupportedFormatError(
                    f"不支持从{file_ext}转换到{actual_output_format}",
                    error_code="UNSUPPORTED_CONVERSION",
                    details={'source_format': file_ext, 'target_format': actual_output_format}
                )

            # 如果没有提供完整输出路径，则构建输出路径
            if output_path is None:
                # 确定输出目录
                if not output_dir:
                    output_dir = file_dir
                else:
                    output_dir = Path(output_dir).resolve()

                # 确定输出文件名
                if keep_original_name:
                    output_name = f"{file_base}{actual_output_format}"
                else:
                    output_name = f"{file_base}_converted{actual_output_format}"

                output_path = output_dir / output_name

            # 确保输出目录存在
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ErrorHandler.handle_file_error(str(output_path.parent), "create_directory", e)

            # 执行转换
            if self.use_markitdown and self.markitdown_integration.is_available() and actual_output_format == '.md':
                # 使用 MarkItDown 进行转换
                result_path = self._convert_with_markitdown(str(file_path), str(output_path))
            else:
                # 使用默认的 Pandoc 转换
                result_path = self._convert_with_pandoc(str(file_path), str(output_path), file_ext, actual_output_format)

            # 记录成功
            self.stats['successful_conversions'] += 1
            processing_time = time.time() - start_time
            conversion_record = {
                'source_file': str(file_path),
                'output_file': result_path,
                'source_format': file_ext,
                'target_format': actual_output_format,
                'timestamp': start_time,
                'duration': processing_time,
                'status': 'success'
            }
            self.stats['conversion_history'].append(conversion_record)

            # 记录转换成功
            self.structured_logger.log_conversion_complete(
                file_path=str(file_path),
                output_path=result_path,
                duration=processing_time,
                success=True,
                input_format=file_ext,
                output_format=actual_output_format,
                file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
            )

            self.logger.info(f"转换成功: {file_path} -> {result_path}")
            return result_path

        except Exception as e:
            # 记录失败
            self.stats['failed_conversions'] += 1
            processing_time = time.time() - start_time
            conversion_record = {
                'source_file': str(file_path),
                'source_format': getattr(Path(file_path), 'suffix', 'unknown'),
                'target_format': output_format,
                'timestamp': start_time,
                'duration': processing_time,
                'status': 'failed',
                'error': str(e)
            }
            self.stats['conversion_history'].append(conversion_record)

            # 记录转换错误
            self.structured_logger.log_conversion_error(
                file_path=str(file_path),
                error_type=type(e).__name__,
                error_message=str(e),
                input_format=getattr(Path(file_path), 'suffix', 'unknown'),
                output_format=output_format,
                duration=processing_time,
                original_error=str(e)
            )

            if isinstance(e, (ConversionError, FileAccessError, UnsupportedFormatError, FileSizeError)):
                raise
            else:
                # 记录原始错误信息
                self.logger.error(f"转换过程中发生未预期的错误: {str(e)}")
                raise ErrorHandler.handle_conversion_error(str(file_path), output_format, e)

    def _validate_conversion_input(self, file_path: str, output_format: str) -> None:
        """验证转换输入参数

        Args:
            file_path: 源文件路径
            output_format: 输出格式

        Raises:
            FileAccessError: 文件访问错误
            FileSizeError: 文件大小超限
            UnsupportedFormatError: 不支持的格式
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileAccessError(
                f"源文件不存在: {file_path}",
                error_code="FILE_NOT_FOUND",
                details={'file_path': file_path}
            )

        # 检查文件是否可读
        if not os.access(file_path, os.R_OK):
            raise FileAccessError(
                f"无法读取文件: {file_path}",
                error_code="FILE_NOT_READABLE",
                details={'file_path': file_path}
            )

        # 检查文件大小
        file_size = os.path.getsize(file_path)
        max_file_size = getattr(self.config, 'conversion', None)
        if max_file_size and hasattr(max_file_size, 'max_file_size'):
            max_size = max_file_size.max_file_size
        else:
            # 兼容性处理：直接从config获取或使用默认值
            max_size = getattr(self.config, 'max_file_size', 100 * 1024 * 1024)  # 默认100MB

        if file_size > max_size:
            raise FileSizeError(
                f"文件大小超过限制: {file_size} bytes > {max_size} bytes",
                error_code="FILE_TOO_LARGE",
                details={'file_path': file_path, 'file_size': file_size, 'max_size': max_size}
            )

        # 验证输出格式
        if not output_format.startswith('.'):
            output_format = '.' + output_format

        # 检查输出格式是否支持
        supported_formats = getattr(self.config, 'conversion', None)
        if supported_formats and hasattr(supported_formats, 'supported_output_formats'):
            if output_format.lower() not in supported_formats.supported_output_formats:
                raise UnsupportedFormatError(
                    f"不支持的输出格式: {output_format}",
                    error_code="UNSUPPORTED_OUTPUT_FORMAT",
                    details={'output_format': output_format, 'supported_formats': list(supported_formats.supported_output_formats)}
                )
        else:
            # 使用默认支持的格式列表
            default_formats = ['.md', '.html', '.txt', '.pdf', '.docx']
            if output_format.lower() not in default_formats:
                raise UnsupportedFormatError(
                    f"不支持的输出格式: {output_format}",
                    error_code="UNSUPPORTED_OUTPUT_FORMAT",
                    details={'output_format': output_format, 'supported_formats': default_formats}
                )

    def batch_convert(self, file_paths: List[str], output_format: str,
                     output_dir: Optional[str] = None, keep_original_name: bool = True,
                     progress_callback: Optional[Callable] = None) -> List[str]:
        """批量转换文件

        Args:
            file_paths: 源文件路径列表
            output_format: 输出格式
            output_dir: 输出目录
            keep_original_name: 是否保留原文件名
            progress_callback: 进度回调函数，接收参数(current, total, file_path, status)

        Returns:
            list: 成功转换的文件路径列表
        """
        converted_files = []
        failed_files = []
        total_files = len(file_paths)
        start_time = time.time()

        # 记录批量操作开始
        self.structured_logger.info(
            'batch_conversion_started',
            total_files=total_files,
            output_format=output_format,
            output_dir=output_dir
        )

        for index, file_path in enumerate(file_paths):
            current = index + 1

            # 更新进度（开始处理）
            if progress_callback:
                progress_callback(current, total_files, file_path, 'processing')

            try:
                output_path = self.convert_file(
                    file_path, output_format, output_dir, keep_original_name
                )

                if output_path:
                    converted_files.append(output_path)

                    # 更新进度（成功）
                    if progress_callback:
                        progress_callback(current, total_files, file_path, 'success')

            except Exception as e:
                failed_files.append(file_path)
                self.logger.error(f"批量转换中的文件失败: {file_path}, 错误: {str(e)}")

                # 更新进度（失败）
                if progress_callback:
                    progress_callback(current, total_files, file_path, 'failed', error=str(e))

                # 单个文件转换失败不影响其他文件
                continue

        # 记录批量操作完成
        duration = time.time() - start_time
        self.structured_logger.log_batch_operation(
            operation='batch_convert',
            total_files=total_files,
            successful=len(converted_files),
            failed=len(failed_files),
            duration=duration,
            output_format=output_format
        )

        # 记录批量转换结果
        self.logger.info(f"批量转换完成: 总计 {total_files} 个文件, 成功 {len(converted_files)} 个")
        return converted_files

    def async_batch_convert(self, file_paths: List[str], output_format: str,
                           output_dir: Optional[str] = None, keep_original_name: bool = True,
                           max_workers: int = 4, progress_callback: Optional[Callable] = None,
                           filter_images: bool = True, clean_content: bool = True,
                           use_markitdown: bool = False) -> List[str]:
        """异步批量转换文件

        使用线程池并行处理多个文件转换任务

        Args:
            file_paths: 源文件路径列表
            output_format: 输出格式
            output_dir: 输出目录
            keep_original_name: 是否保留原文件名
            max_workers: 最大工作线程数
            progress_callback: 进度回调函数
            filter_images: 是否过滤图片
            clean_content: 是否清理内容（去除不必要的元素）
            use_markitdown: 是否使用MarkItDown进行转换

        Returns:
            list: 成功转换的文件路径列表
        """
        self.filter_images = filter_images
        self.clean_content = clean_content
        self.use_markitdown = use_markitdown
        import concurrent.futures
        from functools import partial

        converted_files = []
        total_files = len(file_paths)
        completed = 0

        # 定义单个文件转换的包装函数
        def convert_single_file(file_path, index):
            nonlocal completed

            # 更新进度（开始处理）
            if progress_callback:
                progress_callback(index + 1, total_files, file_path, 'processing')

            try:
                output_path = self.convert_file(
                    file_path, output_format, output_dir, keep_original_name,
                    filter_images, clean_content, use_markitdown
                )

                completed += 1

                # 更新进度（成功）
                if progress_callback:
                    progress_callback(index + 1, total_files, file_path, 'success')

                return output_path

            except Exception as e:
                self.logger.error(f"异步批量转换中的文件失败: {file_path}, 错误: {str(e)}")

                completed += 1

                # 更新进度（失败）
                if progress_callback:
                    progress_callback(index + 1, total_files, file_path, 'failed', error=str(e))

                return None

        # 使用线程池执行转换任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {executor.submit(convert_single_file, file_path, i): file_path
                             for i, file_path in enumerate(file_paths)}

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_file):
                result = future.result()
                if result:
                    converted_files.append(result)

        # 记录批量转换结果
        self.logger.info(f"异步批量转换完成: 总计 {total_files} 个文件, 成功 {len(converted_files)} 个")
        return converted_files

    def get_stats(self) -> Dict[str, Any]:
        """获取转换统计信息

        Returns:
            dict: 包含转换统计信息的字典
        """
        return {
            'total_conversions': self.stats['total_conversions'],
            'successful_conversions': self.stats['successful_conversions'],
            'failed_conversions': self.stats['failed_conversions'],
            'success_rate': (self.stats['successful_conversions'] / max(self.stats['total_conversions'], 1)) * 100,
            'recent_conversions': self.stats['conversion_history'][-10:] if self.stats['conversion_history'] else []
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            'total_conversions': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'conversion_history': []
        }
        self.logger.info("转换统计信息已重置")

    def get_supported_conversions(self) -> Dict[str, List[str]]:
        """获取支持的转换格式映射

        Returns:
            dict: 格式转换映射字典
        """
        return self.conversion_map.copy()

    def validate_file_batch(self, file_paths: List[str]) -> Dict[str, Union[List[str], int]]:
        """验证文件批次

        Args:
            file_paths: 文件路径列表

        Returns:
            dict: 包含有效和无效文件列表的字典
        """
        valid_files = []
        invalid_files = []

        for file_path in file_paths:
            try:
                # 基本验证（不包括输出格式）
                if not os.path.exists(file_path):
                    reason = "文件不存在"
                    invalid_files.append(f"{file_path}: {reason}")
                    self.structured_logger.log_file_validation(
                        file_path=file_path,
                        valid=False,
                        reason=reason
                    )
                    continue

                if not os.access(file_path, os.R_OK):
                    reason = "无法读取"
                    invalid_files.append(f"{file_path}: {reason}")
                    self.structured_logger.log_file_validation(
                        file_path=file_path,
                        valid=False,
                        reason=reason
                    )
                    continue

                file_size = os.path.getsize(file_path)
                max_file_size = getattr(self.config, 'conversion', None)
                if max_file_size and hasattr(max_file_size, 'max_file_size'):
                    max_size = max_file_size.max_file_size
                else:
                    # 兼容性处理：直接从config获取或使用默认值
                    max_size = getattr(self.config, 'max_file_size', 100 * 1024 * 1024)  # 默认100MB

                if file_size > max_size:
                    reason = f"文件过大 ({file_size} bytes)"
                    invalid_files.append(f"{file_path}: {reason}")
                    self.structured_logger.log_file_validation(
                        file_path=file_path,
                        valid=False,
                        reason=reason,
                        file_size=file_size,
                        max_allowed_size=max_size
                    )
                    continue

                # 检查文件格式是否支持
                file_ext = Path(file_path).suffix.lower()
                if file_ext not in self.conversion_map:
                    reason = f"不支持的输入格式 ({file_ext})"
                    invalid_files.append(f"{file_path}: {reason}")
                    self.structured_logger.log_file_validation(
                        file_path=file_path,
                        valid=False,
                        reason=reason,
                        file_extension=file_ext
                    )
                    continue

                # 文件验证通过
                valid_files.append(file_path)
                self.structured_logger.log_file_validation(
                    file_path=file_path,
                    valid=True,
                    file_size=file_size,
                    file_extension=file_ext
                )

            except Exception as e:
                reason = f"验证错误 - {str(e)}"
                invalid_files.append(f"{file_path}: {reason}")
                self.structured_logger.log_file_validation(
                    file_path=file_path,
                    valid=False,
                    reason=reason,
                    error_type=type(e).__name__
                )

        # 记录批量验证结果
        self.structured_logger.info(
            'batch_validation_completed',
            total_files=len(file_paths),
            valid_files=len(valid_files),
            invalid_files=len(invalid_files),
            validation_rate=round((len(valid_files) / max(len(file_paths), 1)) * 100, 2)
        )

        return {
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_files': len(file_paths),
            'valid_count': len(valid_files),
            'invalid_count': len(invalid_files)
        }

    def cleanup_temp_files(self) -> int:
        """清理临时文件

        Returns:
            int: 清理的文件数量
        """
        try:
            temp_dir = tempfile.gettempdir()
            docuflow_temp_pattern = os.path.join(temp_dir, 'docuflow_*')

            import glob
            temp_files = glob.glob(docuflow_temp_pattern)

            cleaned_count = 0
            for temp_file in temp_files:
                try:
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                        cleaned_count += 1
                    elif os.path.isdir(temp_file):
                        shutil.rmtree(temp_file)
                        cleaned_count += 1
                except OSError:
                    continue

            self.logger.info(f"清理了 {cleaned_count} 个临时文件")
            return cleaned_count

        except Exception as e:
            self.logger.warning(f"清理临时文件时出错: {str(e)}")
            return 0

    def __enter__(self) -> 'DocumentConverter':
        """上下文管理器入口

        Returns:
            DocumentConverter: 转换器实例
        """
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> bool:
        """上下文管理器出口，自动清理资源

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪

        Returns:
            bool: 是否抑制异常
        """
        self.cleanup_temp_files()

        if exc_type:
            self.logger.error(f"转换器退出时发生异常: {exc_type.__name__}: {exc_val}")

        return False  # 不抑制异常
