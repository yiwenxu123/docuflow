#!/usr/bin/env python3
"""
DocuFlow 修复验证测试脚本
验证所有已修复的问题是否正常工作
"""

import os
import sys
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有模块导入"""
    print("🔍 测试模块导入...")
    try:
        from converter.document_converter import DocumentConverter
        from utils.config_manager import ConfigManager
        from utils.error_handler import ErrorHandler
        from utils.logger import get_logger
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        traceback.print_exc()
        return False

def test_config_manager():
    """测试配置管理器"""
    print("\n🔍 测试配置管理器...")
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # 测试COMMAND_TIMEOUT属性
        timeout = config.COMMAND_TIMEOUT
        print(f"✅ COMMAND_TIMEOUT: {timeout}")
        
        # 测试SUPPORTED_CONVERSIONS属性
        conversions = config.SUPPORTED_CONVERSIONS
        print(f"✅ 支持的转换格式: {len(conversions)} 种")
        
        # 验证Excel支持
        if '.xlsx' in conversions and '.md' in conversions['.xlsx']:
            print("✅ Excel到Markdown转换支持正常")
        else:
            print("❌ Excel到Markdown转换支持缺失")
            return False
            
        return True
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        traceback.print_exc()
        return False

def test_document_converter():
    """测试文档转换器初始化"""
    print("\n🔍 测试文档转换器...")
    try:
        converter = DocumentConverter()
        print("✅ DocumentConverter初始化成功")
        
        # 测试格式支持检查
        can_convert_excel = converter.can_convert('.xlsx', '.md')
        print(f"✅ Excel到Markdown转换支持: {can_convert_excel}")
        
        can_convert_pdf = converter.can_convert('.pdf', '.md')
        print(f"✅ PDF到Markdown转换支持: {can_convert_pdf}")
        
        return can_convert_excel and can_convert_pdf
    except Exception as e:
        print(f"❌ 文档转换器测试失败: {e}")
        traceback.print_exc()
        return False

def test_excel_conversion():
    """测试Excel转换功能"""
    print("\n🔍 测试Excel转换功能...")
    try:
        # 确保测试文件存在
        test_file = project_root / "test_fix.xlsx"
        if not test_file.exists():
            print(f"❌ 测试文件不存在: {test_file}")
            return False
        
        # 创建输出目录
        output_dir = project_root / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        # 执行转换
        converter = DocumentConverter()
        output_path = converter.convert_file(
            str(test_file),
            'md',
            str(output_dir)
        )
        
        # 验证输出文件
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Excel转换成功: {output_path}")
            print(f"📝 内容长度: {len(content)} 字符")
            return True
        else:
            print(f"❌ 输出文件不存在: {output_path}")
            return False
            
    except Exception as e:
        print(f"❌ Excel转换测试失败: {e}")
        traceback.print_exc()
        return False

def test_pdf_conversion():
    """测试PDF转换功能"""
    print("\n🔍 测试PDF转换功能...")
    try:
        # 确保测试文件存在
        test_file = project_root / "test_fix.pdf"
        if not test_file.exists():
            print(f"❌ 测试文件不存在: {test_file}")
            return False
        
        # 创建输出目录
        output_dir = project_root / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        # 执行转换
        converter = DocumentConverter()
        output_path = converter.convert_file(
            str(test_file),
            'md',
            str(output_dir)
        )
        
        # 验证输出文件
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ PDF转换成功: {output_path}")
            print(f"📝 内容长度: {len(content)} 字符")
            return True
        else:
            print(f"❌ 输出文件不存在: {output_path}")
            return False
            
    except Exception as e:
        print(f"❌ PDF转换测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 DocuFlow 修复验证测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置管理器", test_config_manager),
        ("文档转换器", test_document_converter),
        ("Excel转换", test_excel_conversion),
        ("PDF转换", test_pdf_conversion),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！DocuFlow修复成功！")
        return 0
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())