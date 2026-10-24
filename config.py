#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 配置

只保留运行时真正使用的配置项；Web/RAG 相关配置已移除。
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class AppInfo:
    name: str = "DocuFlow"
    version: str = "2.0.0-dev"
    author: str = "DocuFlow Team"
    description: str = "知识库收件箱工具"


@dataclass
class WindowSettings:
    title: str = f"{AppInfo.name} - 知识库收件箱"
    width: int = 900
    height: int = 700
    min_width: int = 700
    min_height: int = 500


@dataclass
class FileFormat:
    extension: str
    description: str


@dataclass
class FileSettings:
    supported_input_formats: Dict[str, FileFormat] = field(default_factory=lambda: {
        ".pdf": FileFormat(".pdf", "PDF文档"),
        ".docx": FileFormat(".docx", "Word文档"),
        ".xlsx": FileFormat(".xlsx", "Excel表格"),
        ".md": FileFormat(".md", "Markdown文档"),
        ".markdown": FileFormat(".markdown", "Markdown文档"),
        ".html": FileFormat(".html", "HTML文档"),
        ".htm": FileFormat(".htm", "HTML文档"),
        ".txt": FileFormat(".txt", "纯文本文档"),
    })

    supported_output_formats: Dict[str, FileFormat] = field(default_factory=lambda: {
        ".md": FileFormat(".md", "Markdown (.md)"),
        ".html": FileFormat(".html", "HTML (.html)"),
        ".txt": FileFormat(".txt", "纯文本 (.txt)"),
        ".docx": FileFormat(".docx", "Word文档 (.docx)"),
    })

    # 只保留当前环境实际可用的转换路径；PDF 导出需要 LaTeX，暂不声明。
    conversion_matrix: Dict[str, List[str]] = field(default_factory=lambda: {
        ".pdf": [".md", ".html", ".txt"],
        ".docx": [".md", ".html", ".txt"],
        ".xlsx": [".md", ".html", ".txt"],
        ".md": [".html", ".txt", ".docx"],
        ".markdown": [".html", ".txt", ".docx"],
        ".html": [".md", ".txt", ".docx"],
        ".htm": [".md", ".txt", ".docx"],
        ".txt": [".md", ".html", ".docx"],
    })

    @property
    def all_input_extensions(self) -> Set[str]:
        return set(self.supported_input_formats.keys())

    @property
    def all_output_extensions(self) -> Set[str]:
        return set(self.supported_output_formats.keys())


@dataclass
class ConversionSettings:
    default_output_dir: Path = None
    default_output_format: str = os.getenv("DOCUFLOW_OUTPUT_FORMAT", ".md")
    max_file_size: int = int(os.getenv("DOCUFLOW_MAX_FILE_SIZE", 100 * 1024 * 1024))
    max_workers: int = int(os.getenv("DOCUFLOW_MAX_WORKERS", os.cpu_count() or 1))
    keep_original_name: bool = os.getenv("DOCUFLOW_KEEP_ORIGINAL_NAME", "true").lower() == "true"
    command_timeout: int = int(os.getenv("DOCUFLOW_COMMAND_TIMEOUT", 30))
    pandoc_extra_args: List[str] = field(default_factory=list)


@dataclass
class LoggingSettings:
    level: str = os.getenv("DOCUFLOW_LOG_LEVEL", "INFO").upper()
    file: Path = Path(os.getenv(
        "DOCUFLOW_LOG_FILE",
        str(Path.home() / "Library" / "Logs" / "DocuFlow.log"),
    ))
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class Config:
    app: AppInfo = field(default_factory=AppInfo)
    window: WindowSettings = field(default_factory=WindowSettings)
    files: FileSettings = field(default_factory=FileSettings)
    conversion: ConversionSettings = field(default_factory=ConversionSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if self.conversion.default_output_format not in self.files.all_output_extensions:
            raise ValueError(f"无效的默认输出格式: {self.conversion.default_output_format}")
        if self.conversion.max_file_size <= 0:
            raise ValueError("文件大小限制必须大于0")
        if self.conversion.max_workers <= 0:
            raise ValueError("工作线程数必须大于0")
        if self.logging.level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"无效的日志级别: {self.logging.level}")

    def setup_logging(self):
        self.logging.file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=self.logging.level,
            format=self.logging.format,
            handlers=[
                logging.FileHandler(self.logging.file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("pdfplumber").setLevel(logging.WARNING)

    @property
    def SUPPORTED_CONVERSIONS(self) -> Dict[str, List[str]]:
        return self.files.conversion_matrix

    @property
    def COMMAND_TIMEOUT(self) -> int:
        return self.conversion.command_timeout


config = Config()
