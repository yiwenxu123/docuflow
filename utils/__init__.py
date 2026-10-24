#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 工具模块
"""

from .file_utils import (
    get_file_extension,
    is_supported_file,
    get_supported_formats,
    get_conversion_targets,
    can_convert_to,
    get_file_info,
    format_file_size,
    ensure_directory,
    get_unique_filename,
    scan_directory_for_documents,
    validate_output_path,
)

__version__ = "1.0.0"
__author__ = "DocuFlow Team"

__all__ = [
    "get_file_extension",
    "is_supported_file",
    "get_supported_formats",
    "get_conversion_targets",
    "can_convert_to",
    "get_file_info",
    "format_file_size",
    "ensure_directory",
    "get_unique_filename",
    "scan_directory_for_documents",
    "validate_output_path",
]
