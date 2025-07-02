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
    """应用信息"""
    name: str = "DocuFlow"
    version: str = "2.0.0"
    description: str = "智能文档转换工具"
    author: str = "DocuFlow Team"
    license: str = "MIT"

@dataclass
class WindowSettings:
    """窗口设置"""
    width: int = int(os.getenv('DOCUFLOW_WINDOW_WIDTH', 900))
    height: int = int(os.getenv('DOCUFLOW_WINDOW_HEIGHT', 700))
    resizable: bool = os.getenv('DOCUFLOW_RESIZABLE', 'true').lower() == 'true'
    center_on_screen: bool = os.getenv('DOCUFLOW_CENTER', 'true').lower() == 'true'

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
        '.pdf': FileFormat('.pdf', 'PDF文档 (.pdf)'),
        '.docx': FileFormat('.docx', 'Word文档 (.docx)'),
        '.xlsx': FileFormat('.xlsx', 'Excel表格 (.xlsx)'),
        '.pptx': FileFormat('.pptx', 'PowerPoint演示文稿 (.pptx)'),
        '.md': FileFormat('.md', 'Markdown文档 (.md)'),
        '.txt': FileFormat('.txt', '纯文本文件 (.txt)'),
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
        '.xlsx': ['.html', '.docx'],
        '.pptx': ['.pdf', '.docx'],
        '.md': ['.html', '.pdf', '.docx'],
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
        """初始化后处理"""
        self._validate()
        self.setup_logging()
    
    def _validate(self):
        """验证配置"""
        # 验证窗口尺寸
        if self.window.width < 400:
            self.window.width = 400
        if self.window.height < 300:
            self.window.height = 300
            
        # 验证文件大小限制
        if self.conversion.max_file_size <= 0:
            self.conversion.max_file_size = 100 * 1024 * 1024  # 100MB
            
        # 验证工作线程数
        if self.conversion.max_workers <= 0:
            self.conversion.max_workers = 1
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=getattr(logging, self.logging.level),
            format=self.logging.format,
            handlers=[
                logging.FileHandler(self.logging.file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def get_file_dialog_filter(self, format_type: str = 'input') -> str:
        """获取文件对话框过滤器"""
        if format_type == 'input':
            formats = self.files.supported_input_formats
        else:
            formats = self.files.supported_output_formats
            
        filter_parts = []
        for ext, fmt in formats.items():
            filter_parts.append(f"{fmt.description} (*{ext})")
        
        return ";;" .join(filter_parts)

# 全局配置实例
config = Config()

# 支持的转换类型
SUPPORTED_CONVERSIONS = config.files.conversion_matrix

# 命令超时时间
COMMAND_TIMEOUT = config.conversion.command_timeout