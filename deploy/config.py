#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 配置管理模块
集中管理所有配置项，支持环境变量和验证
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass
class AppInfo:
    """应用基本信息"""
    name: str = "DocuFlow"
    version: str = "1.0.0"
    author: str = "DocuFlow Team"
    description: str = "高效的文档格式转换工具"

@dataclass
class WindowSettings:
    """GUI窗口设置"""
    title: str = f"{AppInfo.name} - 文档转换器"
    width: int = 900
    height: int = 700
    min_width: int = 700
    min_height: int = 500

@dataclass
class FileFormat:
    """文件格式定义"""
    extension: str
    description: str

@dataclass
class FileSettings:
    """文件相关设置"""
    # 支持的输入格式
    supported_input_formats: Dict[str, FileFormat] = field(default_factory=lambda: {
        '.pdf': FileFormat('.pdf', 'PDF文档'),
        '.docx': FileFormat('.docx', 'Word文档'),
        '.xlsx': FileFormat('.xlsx', 'Excel表格'),
        '.pptx': FileFormat('.pptx', 'PowerPoint演示文稿'),
        '.md': FileFormat('.md', 'Markdown文档'),
        '.html': FileFormat('.html', 'HTML文档'),
        '.txt': FileFormat('.txt', '纯文本文档'),
    })

    # 支持的输出格式
    supported_output_formats: Dict[str, FileFormat] = field(default_factory=lambda: {
        '.md': FileFormat('.md', 'Markdown (.md)'),
        '.html': FileFormat('.html', 'HTML (.html)'),
        '.txt': FileFormat('.txt', '纯文本 (.txt)'),
        '.pdf': FileFormat('.pdf', 'PDF文档 (.pdf)'),
        '.docx': FileFormat('.docx', 'Word文档 (.docx)'),
    })

    # 转换矩阵
    conversion_matrix: Dict[str, List[str]] = field(default_factory=lambda: {
        '.pdf': ['.md', '.html', '.txt', '.docx'],
        '.docx': ['.md', '.html', '.txt', '.pdf'],
        '.xlsx': ['.html', '.docx', '.md', '.txt'],
        '.xls': ['.html', '.docx', '.md', '.txt'],
        '.pptx': ['.pdf', '.docx'],
        '.md': ['.html', '.pdf', '.docx', '.txt'],
        '.html': ['.md', '.txt', '.pdf', '.docx'],
        '.txt': ['.md', '.html', '.docx'],
    })

    @property
    def all_input_extensions(self) -> Set[str]:
        return set(self.supported_input_formats.keys())

    @property
    def all_output_extensions(self) -> Set[str]:
        return set(self.supported_output_formats.keys())

@dataclass
class ConversionSettings:
    """转换相关设置"""
    default_output_dir: Path = None  # None表示使用源文件所在目录
    default_output_format: str = os.getenv('DOCUFLOW_OUTPUT_FORMAT', '.md')
    max_file_size: int = int(os.getenv('DOCUFLOW_MAX_FILE_SIZE', 100 * 1024 * 1024))  # 100MB
    max_workers: int = int(os.getenv('DOCUFLOW_MAX_WORKERS', os.cpu_count() or 1))
    keep_original_name: bool = os.getenv('DOCUFLOW_KEEP_ORIGINAL_NAME', 'true').lower() == 'true'
    command_timeout: int = int(os.getenv('DOCUFLOW_COMMAND_TIMEOUT', 30))  # 30秒超时
    pandoc_extra_args: List[str] = field(default_factory=list)

@dataclass
class LoggingSettings:
    """日志设置"""
    level: str = os.getenv('DOCUFLOW_LOG_LEVEL', 'INFO').upper()
    file: Path = Path(os.getenv('DOCUFLOW_LOG_FILE', 'docuflow.log'))
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

@dataclass
class Config:
    """主配置类"""
    app: AppInfo = field(default_factory=AppInfo)
    window: WindowSettings = field(default_factory=WindowSettings)
    files: FileSettings = field(default_factory=FileSettings)
    conversion: ConversionSettings = field(default_factory=ConversionSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """验证配置"""
        if self.conversion.default_output_format not in self.files.all_output_extensions:
            raise ValueError(f"无效的默认输出格式: {self.conversion.default_output_format}")
        if self.conversion.max_file_size <= 0:
            raise ValueError("文件大小限制必须大于0")
        if self.conversion.max_workers <= 0:
            raise ValueError("工作线程数必须大于0")
        if self.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"无效的日志级别: {self.logging.level}")

    def setup_logging(self):
        """配置日志记录器"""
        logging.basicConfig(
            level=self.logging.level,
            format=self.logging.format,
            handlers=[
                logging.FileHandler(self.logging.file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('pdfplumber').setLevel(logging.WARNING)

    def get_file_dialog_filter(self) -> str:
        """生成文件对话框的过滤器字符串"""
        filters = []
        all_supported = ' '.join(f'*{ext}' for ext in self.files.all_input_extensions)
        filters.append(f"所有支持的格式 ({all_supported})")
        
        for ext, fmt in self.files.supported_input_formats.items():
            filters.append(f"{fmt.description} (*{ext})")
        
        return ';;'.join(filters)
    
    @property
    def SUPPORTED_CONVERSIONS(self) -> Dict[str, List[str]]:
        """获取支持的转换格式映射"""
        return self.files.conversion_matrix
    
    @property
    def COMMAND_TIMEOUT(self) -> int:
        """获取命令超时时间"""
        return self.conversion.command_timeout

# 创建全局配置实例
config = Config()
FILE_FILTERS = {
    'all_supported': "支持的文件 (*.docx *.md *.markdown *.pdf *.html *.htm *.epub)",
    'word': "Word文档 (*.docx)",
    'markdown': "Markdown文档 (*.md *.markdown)",
    'pdf': "PDF文档 (*.pdf)",
    'html': "HTML文档 (*.html *.htm)",
    'epub': "EPUB电子书 (*.epub)",
    'all_files': "所有文件 (*)"
}

# 默认设置
DEFAULT_SETTINGS = {
    'keep_original_name': True,
    'output_directory': '',  # 空字符串表示使用源文件目录
    'default_output_format': '.pdf',
    'show_conversion_details': True,
    'auto_open_output_folder': True
}

# UI样式
UI_STYLES = {
    'primary_color': '#3498db',
    'success_color': '#27ae60',
    'warning_color': '#f39c12',
    'danger_color': '#e74c3c',
    'secondary_color': '#95a5a6',
    'background_color': '#ecf0f1',
    'text_color': '#2c3e50'
}

# 错误消息
ERROR_MESSAGES = {
    'pandoc_not_found': "Pandoc未安装或无法运行。请访问 https://pandoc.org/installing.html 安装Pandoc。",
    'file_not_found': "文件不存在或无法访问。",
    'unsupported_format': "不支持的文件格式。",
    'conversion_failed': "文件转换失败。",
    'permission_denied': "没有文件访问权限。",
    'output_dir_invalid': "输出目录无效或无法创建。",
    'no_files_selected': "请先选择要转换的文件。"
}

# 成功消息
SUCCESS_MESSAGES = {
    'conversion_complete': "转换完成！",
    'files_added': "文件已添加到转换列表。",
    'settings_saved': "设置已保存。"
}

# 应用路径
APP_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(APP_DIR, 'resources')
TEMP_DIR = os.path.join(APP_DIR, 'temp')

# 确保临时目录存在
os.makedirs(TEMP_DIR, exist_ok=True)

# Pandoc相关设置
PANDOC_SETTINGS = {
    'pdf_engine': 'xelatex',  # PDF引擎
    'extract_media': True,    # 从PDF提取媒体文件
    'standalone': True,       # 生成独立文档
    'table_of_contents': False,  # 是否生成目录
    'number_sections': False,    # 是否编号章节
}

# 日志设置
LOG_SETTINGS = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.path.join(APP_DIR, 'docuflow.log'),
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 3
}