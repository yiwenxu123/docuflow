#!/usr/bin/env python3
"""
命令行版本的DocuFlow，避免GUI问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from converter.document_converter import DocumentConverter
import config

def main():
    print("DocuFlow v2.0.0 - 命令行版本")
    print("由于GUI问题，暂时使用命令行版本")
    
    # 初始化配置
    config_instance = config.Config()
    
    # 创建转换器
    converter = DocumentConverter(config_instance)
    
    # 示例：转换test_sample.html到markdown
    test_file = project_root / "test_sample.html"
    if test_file.exists():
        print(f"\n正在转换: {test_file}")
        try:
            result = converter.convert_file(
                str(test_file),
                output_dir=None,  # 使用源文件目录
                output_format=".md"
            )
            print(f"转换成功: {result}")
        except Exception as e:
            print(f"转换失败: {e}")
    else:
        print(f"测试文件不存在: {test_file}")
    
    print("\n命令行版本运行完成")
    print("要使用完整功能，请解决GUI问题后运行: python run_app.py")

if __name__ == "__main__":
    main()