#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 文档转换器核心逻辑
"""

import os
import subprocess
import tempfile
import shutil
from utils.file_utils import get_file_extension, get_supported_formats

class DocumentConverter:
    """文档转换器类"""
    
    def __init__(self):
        """初始化转换器"""
        # 检查pandoc是否安装
        self.check_dependencies()
        
        # 支持的转换格式映射（已移除PDF转换功能）
        self.conversion_map = {
            ".docx": [".md", ".html", ".epub"],
            ".md": [".docx", ".html", ".epub"],
            ".html": [".md", ".docx", ".epub"],
            ".epub": [".md", ".docx", ".html"]
        }
    
    def check_dependencies(self):
        """检查依赖是否安装"""
        try:
            result = subprocess.run(["pandoc", "--version"], 
                                   capture_output=True, 
                                   text=True, 
                                   check=False)
            if result.returncode != 0:
                raise Exception("Pandoc未安装或无法运行")
        except FileNotFoundError:
            raise Exception("Pandoc未安装，请先安装Pandoc: https://pandoc.org/installing.html")
    
    def can_convert(self, source_format, target_format):
        """检查是否支持从源格式转换到目标格式"""
        if source_format not in self.conversion_map:
            return False
        return target_format in self.conversion_map[source_format]
    
    def convert_file(self, file_path, output_format, output_dir=None, keep_original_name=True):
        """转换文件
        
        Args:
            file_path: 源文件路径
            output_format: 输出格式 (如 .html, .md)
            output_dir: 输出目录，如果为None则使用源文件目录
            keep_original_name: 是否保留原文件名
            
        Returns:
            str: 输出文件路径，如果转换失败则返回None
        """
        # 获取文件信息
        file_dir, file_name = os.path.split(file_path)
        file_base, file_ext = os.path.splitext(file_name)
        
        # 检查格式支持
        if not self.can_convert(file_ext.lower(), output_format.lower()):
            raise Exception(f"不支持从{file_ext}转换到{output_format}")
        
        # 确定输出目录
        if not output_dir:
            output_dir = file_dir if file_dir else os.getcwd()
        
        # 确保输出目录存在
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 确定输出文件名
        if keep_original_name:
            output_name = f"{file_base}{output_format}"
        else:
            output_name = f"{file_base}_converted{output_format}"
        
        output_path = os.path.join(output_dir, output_name)
        
        # 执行转换
        try:
            return self._convert_with_pandoc(file_path, output_path, file_ext, output_format)
        except Exception as e:
            raise Exception(f"转换失败: {str(e)}")
    
    def _convert_with_pandoc(self, input_path, output_path, input_format, output_format):
        """使用pandoc执行转换"""
        # 准备pandoc命令
        cmd = ["pandoc", input_path, "-o", output_path]
        
        # 添加特定格式的参数
        if output_format.lower() == ".html":
            cmd.extend(["--standalone", "--self-contained"])
        elif output_format.lower() == ".epub":
            cmd.extend(["--epub-cover-image=", "--epub-metadata="])
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or "未知错误"
            raise Exception(error_msg)
        
        return output_path
    
    def batch_convert(self, file_paths, output_format, output_dir=None, keep_original_name=True):
        """批量转换文件
        
        Args:
            file_paths: 源文件路径列表
            output_format: 输出格式
            output_dir: 输出目录
            keep_original_name: 是否保留原文件名
            
        Returns:
            list: 成功转换的文件路径列表
        """
        converted_files = []
        
        for file_path in file_paths:
            try:
                output_path = self.convert_file(
                    file_path, output_format, output_dir, keep_original_name
                )
                if output_path:
                    converted_files.append(output_path)
            except Exception:
                # 单个文件转换失败不影响其他文件
                continue
        
        return converted_files