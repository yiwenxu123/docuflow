#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 文件处理工具函数
"""

import os
import mimetypes

# 支持的文件格式（已移除PDF支持）
SUPPORTED_FORMATS = {
    '.docx': 'Microsoft Word文档',
    '.md': 'Markdown文档',
    '.html': 'HTML文档',
    '.htm': 'HTML文档',
    '.epub': 'EPUB电子书'
}

# 格式转换支持矩阵（已移除PDF转换）
CONVERSION_MATRIX = {
    '.docx': ['.md', '.html', '.epub'],
    '.md': ['.docx', '.html', '.epub'],
    '.html': ['.md', '.docx', '.epub'],
    '.htm': ['.md', '.docx', '.epub'],
    '.epub': ['.md', '.docx', '.html']
}

def get_file_extension(file_path):
    """获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 小写的文件扩展名
    """
    return os.path.splitext(file_path)[1].lower()

def is_supported_file(file_path):
    """检查文件是否为支持的格式
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否支持
    """
    if not os.path.isfile(file_path):
        return False
    
    ext = get_file_extension(file_path)
    return ext in SUPPORTED_FORMATS

def get_supported_formats():
    """获取支持的文件格式列表
    
    Returns:
        dict: 格式字典
    """
    return SUPPORTED_FORMATS.copy()

def get_conversion_options(source_format):
    """获取指定源格式的转换选项
    
    Args:
        source_format: 源文件格式
        
    Returns:
        list: 可转换的目标格式列表
    """
    return CONVERSION_MATRIX.get(source_format.lower(), [])

def validate_file_path(file_path):
    """验证文件路径
    
    Args:
        file_path: 文件路径
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if not file_path:
        return False, "文件路径不能为空"
    
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    if not os.path.isfile(file_path):
        return False, "路径不是文件"
    
    if not is_supported_file(file_path):
        return False, "不支持的文件格式"
    
    return True, ""

def get_file_info(file_path):
    """获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        dict: 文件信息字典
    """
    if not os.path.exists(file_path):
        return None
    
    stat = os.stat(file_path)
    ext = get_file_extension(file_path)
    
    return {
        'name': os.path.basename(file_path),
        'path': file_path,
        'size': stat.st_size,
        'extension': ext,
        'format_name': SUPPORTED_FORMATS.get(ext, '未知格式'),
        'is_supported': ext in SUPPORTED_FORMATS
    }

def format_file_size(size_bytes):
    """格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化的文件大小
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_files_from_directory(directory, recursive=False):
    """从目录获取支持的文件列表
    
    Args:
        directory: 目录路径
        recursive: 是否递归搜索子目录
        
    Returns:
        list: 支持的文件路径列表
    """
    files = []
    
    if not os.path.isdir(directory):
        return files
    
    if recursive:
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if is_supported_file(file_path):
                    files.append(file_path)
    else:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if is_supported_file(file_path):
                files.append(file_path)
    
    return sorted(files)