#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 测试框架模块
提供统一的测试工具、模拟对象和测试数据生成功能
"""

import os
import tempfile
import shutil
import unittest
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
import time
import random
import string


@dataclass
class TestFile:
    """测试文件数据类"""
    name: str
    content: str
    extension: str
    size_bytes: int = 0
    
    def __post_init__(self):
        if self.size_bytes == 0:
            self.size_bytes = len(self.content.encode('utf-8'))


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self):
        self.random = random.Random(42)  # 固定种子确保可重现性
    
    def generate_text_content(self, length: int = 1000, 
                            language: str = 'mixed') -> str:
        """生成文本内容
        
        Args:
            length: 文本长度
            language: 语言类型 ('english', 'chinese', 'mixed')
            
        Returns:
            str: 生成的文本内容
        """
        if language == 'english':
            words = [
                'document', 'conversion', 'file', 'format', 'text', 'content',
                'processing', 'analysis', 'data', 'information', 'system',
                'application', 'software', 'technology', 'digital', 'electronic'
            ]
            content = ' '.join(self.random.choices(words, k=length // 8))
        elif language == 'chinese':
            chars = '文档转换格式处理分析数据信息系统应用软件技术数字电子内容文件'
            content = ''.join(self.random.choices(chars, k=length // 3))
        else:  # mixed
            english_part = self.generate_text_content(length // 2, 'english')
            chinese_part = self.generate_text_content(length // 2, 'chinese')
            content = f"{english_part}\n\n{chinese_part}"
        
        return content[:length]
    
    def generate_markdown_content(self, sections: int = 5) -> str:
        """生成Markdown内容
        
        Args:
            sections: 章节数量
            
        Returns:
            str: Markdown内容
        """
        content = "# 测试文档\n\n"
        content += "这是一个用于测试的Markdown文档。\n\n"
        
        for i in range(1, sections + 1):
            content += f"## 第{i}章节\n\n"
            content += self.generate_text_content(200, 'mixed') + "\n\n"
            
            # 添加列表
            content += "### 要点列表\n\n"
            for j in range(3):
                content += f"- 要点 {j + 1}: {self.generate_text_content(50, 'chinese')}\n"
            content += "\n"
            
            # 添加代码块
            if i % 2 == 0:
                content += "### 代码示例\n\n"
                content += "```python\n"
                content += "def example_function():\n"
                content += "    return 'Hello, World!'\n"
                content += "```\n\n"
        
        return content
    
    def generate_html_content(self, title: str = "测试页面") -> str:
        """生成HTML内容
        
        Args:
            title: 页面标题
            
        Returns:
            str: HTML内容
        """
        content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .content {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="content">
        <h2>简介</h2>
        <p>{self.generate_text_content(300, 'mixed')}</p>
        
        <h2>详细内容</h2>
        <p>{self.generate_text_content(500, 'mixed')}</p>
        
        <h3>列表示例</h3>
        <ul>
            <li>项目 1: {self.generate_text_content(50, 'chinese')}</li>
            <li>项目 2: {self.generate_text_content(50, 'chinese')}</li>
            <li>项目 3: {self.generate_text_content(50, 'chinese')}</li>
        </ul>
        
        <h3>表格示例</h3>
        <table border="1">
            <tr>
                <th>列1</th>
                <th>列2</th>
                <th>列3</th>
            </tr>
            <tr>
                <td>数据1</td>
                <td>数据2</td>
                <td>数据3</td>
            </tr>
        </table>
    </div>
</body>
</html>"""
        return content
    
    def generate_test_files(self, count: int = 10, 
                          formats: Optional[List[str]] = None) -> List[TestFile]:
        """生成测试文件列表
        
        Args:
            count: 文件数量
            formats: 文件格式列表
            
        Returns:
            List[TestFile]: 测试文件列表
        """
        if formats is None:
            formats = ['.txt', '.md', '.html']
        
        test_files = []
        
        for i in range(count):
            ext = self.random.choice(formats)
            name = f"test_file_{i:03d}{ext}"
            
            if ext == '.txt':
                content = self.generate_text_content(500 + i * 100)
            elif ext == '.md':
                content = self.generate_markdown_content(3 + i % 3)
            elif ext == '.html':
                content = self.generate_html_content(f"测试页面 {i + 1}")
            else:
                content = self.generate_text_content(300)
            
            test_files.append(TestFile(name, content, ext))
        
        return test_files
    
    def generate_large_file_content(self, size_mb: float) -> str:
        """生成大文件内容
        
        Args:
            size_mb: 文件大小（MB）
            
        Returns:
            str: 文件内容
        """
        target_size = int(size_mb * 1024 * 1024)
        chunk_size = 1024
        content = ""
        
        base_text = self.generate_text_content(chunk_size)
        
        while len(content.encode('utf-8')) < target_size:
            content += base_text + "\n"
        
        # 截断到目标大小
        while len(content.encode('utf-8')) > target_size:
            content = content[:-1]
        
        return content


class TestFileManager:
    """测试文件管理器"""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.mkdtemp())
        self.created_files: List[Path] = []
        self.created_dirs: List[Path] = []
        self.data_generator = TestDataGenerator()
    
    def create_test_file(self, test_file: TestFile, 
                        subdir: Optional[str] = None) -> Path:
        """创建测试文件
        
        Args:
            test_file: 测试文件对象
            subdir: 子目录
            
        Returns:
            Path: 创建的文件路径
        """
        if subdir:
            file_dir = self.base_dir / subdir
            file_dir.mkdir(parents=True, exist_ok=True)
            if file_dir not in self.created_dirs:
                self.created_dirs.append(file_dir)
        else:
            file_dir = self.base_dir
        
        file_path = file_dir / test_file.name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(test_file.content)
        
        self.created_files.append(file_path)
        return file_path
    
    def create_test_files_batch(self, test_files: List[TestFile], 
                               subdir: Optional[str] = None) -> List[Path]:
        """批量创建测试文件
        
        Args:
            test_files: 测试文件列表
            subdir: 子目录
            
        Returns:
            List[Path]: 创建的文件路径列表
        """
        return [self.create_test_file(tf, subdir) for tf in test_files]
    
    def create_directory_structure(self, structure: Dict[str, Any]) -> Dict[str, Path]:
        """创建目录结构
        
        Args:
            structure: 目录结构字典
            
        Returns:
            Dict[str, Path]: 创建的路径映射
        """
        paths = {}
        
        def create_recursive(current_structure: Dict[str, Any], 
                           current_path: Path) -> None:
            for name, content in current_structure.items():
                if isinstance(content, dict):
                    # 目录
                    dir_path = current_path / name
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.created_dirs.append(dir_path)
                    paths[name] = dir_path
                    create_recursive(content, dir_path)
                elif isinstance(content, str):
                    # 文件
                    file_path = current_path / name
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.created_files.append(file_path)
                    paths[name] = file_path
                elif isinstance(content, TestFile):
                    # TestFile对象
                    file_path = current_path / content.name
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content.content)
                    self.created_files.append(file_path)
                    paths[name] = file_path
        
        create_recursive(structure, self.base_dir)
        return paths
    
    def cleanup(self) -> None:
        """清理创建的文件和目录"""
        # 删除文件
        for file_path in self.created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass
        
        # 删除目录（从最深层开始）
        for dir_path in sorted(self.created_dirs, key=lambda x: len(x.parts), reverse=True):
            try:
                if dir_path.exists() and dir_path.is_dir():
                    dir_path.rmdir()
            except Exception:
                pass
        
        # 删除基础目录
        try:
            if self.base_dir.exists() and self.base_dir != Path.cwd():
                shutil.rmtree(self.base_dir)
        except Exception:
            pass
        
        self.created_files.clear()
        self.created_dirs.clear()
    
    def __enter__(self) -> 'TestFileManager':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class MockConverter:
    """模拟转换器"""
    
    def __init__(self, success_rate: float = 1.0, 
                 processing_delay: float = 0.1):
        self.success_rate = success_rate
        self.processing_delay = processing_delay
        self.conversion_history: List[Dict[str, Any]] = []
        self.stats = {
            'total_conversions': 0,
            'successful_conversions': 0,
            'failed_conversions': 0
        }
    
    def convert_file(self, file_path: str, output_format: str, 
                    output_dir: Optional[str] = None, 
                    keep_original_name: bool = True) -> str:
        """模拟文件转换
        
        Args:
            file_path: 源文件路径
            output_format: 输出格式
            output_dir: 输出目录
            keep_original_name: 是否保留原文件名
            
        Returns:
            str: 输出文件路径
            
        Raises:
            Exception: 模拟转换失败
        """
        # 模拟处理延迟
        time.sleep(self.processing_delay)
        
        self.stats['total_conversions'] += 1
        
        # 根据成功率决定是否成功
        if random.random() > self.success_rate:
            self.stats['failed_conversions'] += 1
            raise Exception(f"模拟转换失败: {file_path}")
        
        # 生成输出路径
        input_path = Path(file_path)
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = input_path.parent
        
        if keep_original_name:
            output_file = output_path / f"{input_path.stem}{output_format}"
        else:
            output_file = output_path / f"converted_{int(time.time())}{output_format}"
        
        # 创建输出文件
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"转换后的内容: {input_path.name} -> {output_format}")
        
        self.stats['successful_conversions'] += 1
        
        # 记录转换历史
        self.conversion_history.append({
            'input_file': str(input_path),
            'output_file': str(output_file),
            'output_format': output_format,
            'timestamp': time.time(),
            'success': True
        })
        
        return str(output_file)
    
    def batch_convert(self, file_paths: List[str], output_format: str,
                     output_dir: Optional[str] = None,
                     keep_original_name: bool = True,
                     progress_callback: Optional[Callable] = None) -> List[str]:
        """模拟批量转换
        
        Args:
            file_paths: 文件路径列表
            output_format: 输出格式
            output_dir: 输出目录
            keep_original_name: 是否保留原文件名
            progress_callback: 进度回调函数
            
        Returns:
            List[str]: 成功转换的文件路径列表
        """
        successful_conversions = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                if progress_callback:
                    progress_callback(i + 1, total_files, file_path, 'processing')
                
                output_path = self.convert_file(
                    file_path, output_format, output_dir, keep_original_name
                )
                successful_conversions.append(output_path)
                
                if progress_callback:
                    progress_callback(i + 1, total_files, file_path, 'completed')
                    
            except Exception:
                if progress_callback:
                    progress_callback(i + 1, total_files, file_path, 'failed')
                continue
        
        return successful_conversions
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


class DocuFlowTestCase(unittest.TestCase):
    """DocuFlow测试基类"""
    
    def setUp(self):
        """测试设置"""
        self.test_file_manager = TestFileManager()
        self.data_generator = TestDataGenerator()
        self.mock_converter = MockConverter()
        
        # 创建临时目录
        self.temp_dir = self.test_file_manager.base_dir
        self.input_dir = self.temp_dir / 'input'
        self.output_dir = self.temp_dir / 'output'
        
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """测试清理"""
        self.test_file_manager.cleanup()
    
    def create_test_files(self, count: int = 5, 
                         formats: Optional[List[str]] = None) -> List[Path]:
        """创建测试文件
        
        Args:
            count: 文件数量
            formats: 文件格式列表
            
        Returns:
            List[Path]: 创建的文件路径列表
        """
        test_files = self.data_generator.generate_test_files(count, formats)
        return self.test_file_manager.create_test_files_batch(
            test_files, 'input'
        )
    
    def assert_file_exists(self, file_path: Union[str, Path], 
                          msg: Optional[str] = None) -> None:
        """断言文件存在
        
        Args:
            file_path: 文件路径
            msg: 错误消息
        """
        file_path = Path(file_path)
        self.assertTrue(
            file_path.exists(),
            msg or f"文件不存在: {file_path}"
        )
    
    def assert_file_not_exists(self, file_path: Union[str, Path], 
                              msg: Optional[str] = None) -> None:
        """断言文件不存在
        
        Args:
            file_path: 文件路径
            msg: 错误消息
        """
        file_path = Path(file_path)
        self.assertFalse(
            file_path.exists(),
            msg or f"文件不应该存在: {file_path}"
        )
    
    def assert_file_content_contains(self, file_path: Union[str, Path], 
                                   expected_content: str,
                                   msg: Optional[str] = None) -> None:
        """断言文件内容包含指定文本
        
        Args:
            file_path: 文件路径
            expected_content: 期望的内容
            msg: 错误消息
        """
        file_path = Path(file_path)
        self.assert_file_exists(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn(
            expected_content,
            content,
            msg or f"文件内容不包含期望文本: {expected_content}"
        )
    
    def assert_conversion_successful(self, input_file: Union[str, Path],
                                   output_file: Union[str, Path],
                                   msg: Optional[str] = None) -> None:
        """断言转换成功
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            msg: 错误消息
        """
        self.assert_file_exists(input_file, "输入文件不存在")
        self.assert_file_exists(output_file, "输出文件不存在")
        
        # 检查输出文件不为空
        output_path = Path(output_file)
        self.assertGreater(
            output_path.stat().st_size,
            0,
            msg or "输出文件为空"
        )
    
    def measure_performance(self, func: Callable, *args, **kwargs) -> Dict[str, float]:
        """测量函数性能
        
        Args:
            func: 要测量的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Dict[str, float]: 性能指标
        """
        import psutil
        
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
        
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'duration': end_time - start_time,
            'memory_usage_mb': end_memory - start_memory,
            'success': success,
            'result': result
        }


def create_test_suite() -> unittest.TestSuite:
    """创建测试套件
    
    Returns:
        unittest.TestSuite: 测试套件
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 自动发现测试
    test_dir = Path(__file__).parent
    discovered_tests = loader.discover(str(test_dir), pattern='test_*.py')
    
    for test_group in discovered_tests:
        suite.addTest(test_group)
    
    return suite


def run_tests(verbosity: int = 2) -> unittest.TestResult:
    """运行测试
    
    Args:
        verbosity: 详细程度
        
    Returns:
        unittest.TestResult: 测试结果
    """
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


if __name__ == '__main__':
    # 运行测试
    result = run_tests()
    
    # 输出测试结果摘要
    print(f"\n测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("所有测试通过! ✅")
    else:
        print("部分测试失败! ❌")