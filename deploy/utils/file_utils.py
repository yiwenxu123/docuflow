#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 文件处理工具函数
"""

import os
import mimetypes

# 支持的文件格式
SUPPORTED_FORMATS = {
    '.docx': 'Microsoft Word文档',
    '.md': 'Markdown文档',
    '.pdf': 'PDF文档',
    '.html': 'HTML文档',
    '.htm': 'HTML文档',
    '.epub': 'EPUB电子书',
    '.xlsx': 'Excel表格',
    '.xls': 'Excel表格'
}

# 格式转换支持矩阵
CONVERSION_MATRIX = {
    '.docx': ['.pdf', '.md', '.html', '.epub'],
    '.md': ['.docx', '.pdf', '.html', '.epub'],
    '.pdf': ['.docx', '.md', '.html'],
    '.html': ['.md', '.docx', '.pdf', '.epub'],
    '.htm': ['.md', '.docx', '.pdf', '.epub'],
    '.epub': ['.md', '.pdf', '.docx', '.html'],
    '.xlsx': ['.md', '.html', '.pdf'],
    '.xls': ['.md', '.html', '.pdf']
}

def get_file_extension(file_path):
    """获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 小写的文件扩展名
    """
    return os.path.splitext(file_path)[1].lower()

def is_supported_file(filename):
    """检查文件名是否为支持的格式
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否支持
    """
    ext = get_file_extension(filename)
    return ext in SUPPORTED_FORMATS

def get_supported_formats():
    """获取支持的文件格式列表
    
    Returns:
        dict: 格式字典 {扩展名: 描述}
    """
    return SUPPORTED_FORMATS.copy()

def get_conversion_targets(source_format):
    """获取指定源格式可以转换的目标格式
    
    Args:
        source_format: 源格式扩展名
        
    Returns:
        list: 可转换的目标格式列表
    """
    return CONVERSION_MATRIX.get(source_format.lower(), [])

def can_convert_to(source_format, target_format):
    """检查是否可以从源格式转换到目标格式
    
    Args:
        source_format: 源格式扩展名
        target_format: 目标格式扩展名
        
    Returns:
        bool: 是否可以转换
    """
    targets = get_conversion_targets(source_format)
    return target_format.lower() in targets

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
        'path': file_path,
        'name': os.path.basename(file_path),
        'size': stat.st_size,
        'extension': ext,
        'format_name': SUPPORTED_FORMATS.get(ext, '未知格式'),
        'is_supported': is_supported_file(file_path),
        'conversion_targets': get_conversion_targets(ext)
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

def ensure_directory(directory):
    """确保目录存在
    
    Args:
        directory: 目录路径
    """
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def get_unique_filename(file_path):
    """获取唯一的文件名（如果文件已存在则添加数字后缀）
    
    Args:
        file_path: 原始文件路径
        
    Returns:
        str: 唯一的文件路径
    """
    if not os.path.exists(file_path):
        return file_path
    
    directory, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    
    counter = 1
    while True:
        new_name = f"{name}_{counter}{ext}"
        new_path = os.path.join(directory, new_name)
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def scan_directory_for_documents(directory, recursive=True):
    """扫描目录中的文档文件
    
    Args:
        directory: 目录路径
        recursive: 是否递归扫描子目录
        
    Returns:
        list: 文档文件路径列表
    """
    documents = []
    
    if not os.path.isdir(directory):
        return documents
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if is_supported_file(file_path):
                    documents.append(file_path)
    else:
        for item in os.listdir(directory):
            file_path = os.path.join(directory, item)
            if os.path.isfile(file_path) and is_supported_file(file_path):
                documents.append(file_path)
    
    return sorted(documents)

def validate_output_path(output_path):
    """验证输出路径是否有效
    
    Args:
        output_path: 输出路径
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    try:
        # 检查目录是否可写
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 尝试创建临时文件测试写权限
        test_file = output_path + ".tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        return True, None
        
    except PermissionError:
        return False, "没有写入权限"
    except Exception as e:
        return False, f"路径无效: {str(e)}"