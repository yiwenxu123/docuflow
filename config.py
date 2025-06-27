#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 配置文件
"""

import os

# 应用信息
APP_NAME = "DocuFlow"
APP_VERSION = "1.0.0"
APP_AUTHOR = "DocuFlow Team"
APP_DESCRIPTION = "文档转换器 - 高效的文档格式转换工具"

# 窗口设置
WINDOW_TITLE = f"{APP_NAME} - 文档转换器"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
WINDOW_MIN_WIDTH = 600
WINDOW_MIN_HEIGHT = 500

# 支持的文件格式
SUPPORTED_INPUT_FORMATS = {
    '.docx': 'Microsoft Word文档',
    '.md': 'Markdown文档', 
    '.markdown': 'Markdown文档',
    '.pdf': 'PDF文档',
    '.html': 'HTML文档',
    '.htm': 'HTML文档',
    '.epub': 'EPUB电子书'
}

SUPPORTED_OUTPUT_FORMATS = {
    '.pdf': 'PDF (.pdf)',
    '.md': 'Markdown (.md)',
    '.docx': 'Word文档 (.docx)',
    '.html': 'HTML (.html)'
}

# 转换矩阵 - 定义哪些格式可以转换为哪些格式
CONVERSION_MATRIX = {
    '.docx': ['.pdf', '.md', '.html'],
    '.md': ['.docx', '.pdf', '.html'],
    '.markdown': ['.docx', '.pdf', '.html'],
    '.pdf': ['.docx', '.md'],  # PDF转换有限制
    '.html': ['.md'],
    '.htm': ['.md'],
    '.epub': ['.md', '.pdf']
}

# 文件过滤器（用于文件对话框）
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