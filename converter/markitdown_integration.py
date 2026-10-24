#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarkItDown 集成模块

用于调用 MarkItDown 命令行工具进行文档转换
"""

import os
import shutil
import subprocess
from typing import Optional, Dict, Any


class MarkItDownIntegration:
    """MarkItDown 集成类

    用于调用 MarkItDown 命令行工具进行文档转换
    """

    def __init__(self):
        """初始化 MarkItDown 集成

        设置 MarkItDown 命令路径
        """
        # 优先使用 PATH 中的标准安装，其次兼容旧的本地环境
        self.markitdown_env = os.path.expanduser('~/markitdown-env')
        self.markitdown_cmd = shutil.which('markitdown') or os.path.join(
            self.markitdown_env, 'bin', 'markitdown'
        )
        self._checked = False
        self._available = False

    def is_available(self) -> bool:
        """检查 MarkItDown 是否可用（结果缓存，避免每次转换重复探测）"""
        if self._checked:
            return self._available

        self._checked = True
        try:
            if not os.path.exists(self.markitdown_cmd):
                return False

            # 启动较慢的机器上可能需要十几秒
            result = subprocess.run(
                [self.markitdown_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=30
            )
            self._available = result.returncode == 0
        except Exception:
            self._available = False
        return self._available

    def convert_file(self, input_file: str, output_file: Optional[str] = None,
                    use_plugins: bool = False, keep_data_uris: bool = False) -> str:
        """使用 MarkItDown 转换文件

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径（可选）
            use_plugins: 是否使用插件
            keep_data_uris: 是否保留数据 URI

        Returns:
            str: 转换后的内容或输出文件路径

        Raises:
            Exception: 转换失败时抛出异常
        """
        if not self.is_available():
            raise Exception("MarkItDown 不可用，请确保已正确安装")

        if not os.path.exists(input_file):
            raise Exception(f"输入文件不存在: {input_file}")

        # 构建命令
        cmd = [self.markitdown_cmd, input_file]

        # 添加参数
        if output_file:
            cmd.extend(['-o', output_file])

        if use_plugins:
            cmd.append('--use-plugins')

        if keep_data_uris:
            cmd.append('--keep-data-uris')

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 设置超时时间
            )

            if result.returncode != 0:
                raise Exception(f"MarkItDown 转换失败: {result.stderr}")

            # 如果指定了输出文件，返回文件路径
            if output_file:
                if os.path.exists(output_file):
                    return output_file
                else:
                    raise Exception(f"MarkItDown 转换后输出文件不存在: {output_file}")

            # 否则返回转换后的内容
            return result.stdout

        except subprocess.TimeoutExpired:
            raise Exception("MarkItDown 转换超时")
        except Exception as e:
            raise Exception(f"MarkItDown 转换失败: {str(e)}")

    def get_supported_formats(self) -> Dict[str, str]:
        """获取 MarkItDown 支持的文件格式

        Returns:
            Dict[str, str]: 支持的文件格式及其描述
        """
        # MarkItDown 支持的常见格式
        return {
            '.pdf': 'PDF 文档',
            '.docx': 'Word 文档',
            '.doc': 'Word 文档',
            '.xlsx': 'Excel 表格',
            '.xls': 'Excel 表格',
            '.pptx': 'PowerPoint 演示文稿',
            '.ppt': 'PowerPoint 演示文稿',
            '.eml': '邮件文件',
            '.txt': '文本文件',
            '.html': 'HTML 文件',
            '.htm': 'HTML 文件',
            '.jpg': '图片文件',
            '.jpeg': '图片文件',
            '.png': '图片文件',
            '.gif': '图片文件',
            '.bmp': '图片文件',
            '.wav': '音频文件',
            '.mp3': '音频文件'
        }


def get_markitdown_integration() -> MarkItDownIntegration:
    """获取 MarkItDown 集成实例

    Returns:
        MarkItDownIntegration: MarkItDown 集成实例
    """
    return MarkItDownIntegration()
