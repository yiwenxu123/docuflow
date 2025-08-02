#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速功能验证脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def quick_test():
    """快速测试核心功能"""
    print("DocuFlow 快速功能验证")
    print("=" * 40)
    
    try:
        # 测试配置管理器
        from utils.config_manager import ConfigManager
        config = ConfigManager()
        print("✓ ConfigManager 初始化成功")
        
        # 测试COMMAND_TIMEOUT属性
        timeout = config.COMMAND_TIMEOUT
        print(f"✓ COMMAND_TIMEOUT: {timeout}")
        
        # 测试SUPPORTED_CONVERSIONS属性
        conversions = config.SUPPORTED_CONVERSIONS
        print(f"✓ 支持的转换格式: {len(conversions)} 种")
        
        # 检查Excel支持
        if '.xlsx' in conversions:
            print(f"✓ Excel支持: {conversions['.xlsx']}")
        else:
            print("✗ Excel转换不支持")
            
        # 测试文档转换器
        from converter.document_converter import DocumentConverter
        converter = DocumentConverter(config)
        print("✓ DocumentConverter 初始化成功")
        
        # 测试转换支持检查
        can_excel = converter.can_convert('.xlsx', '.md')
        print(f"✓ Excel到Markdown转换支持: {can_excel}")
        
        # 测试文件工具
        from utils.file_utils import get_file_extension, is_supported_file
        ext = get_file_extension("test.xlsx")
        supported = is_supported_file("test.xlsx")
        print(f"✓ 文件工具: 扩展名={ext}, 支持={supported}")
        
        print("\n🎉 所有核心功能验证通过！")
        return True
        
    except Exception as e:
        print(f"\n✗ 功能验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)