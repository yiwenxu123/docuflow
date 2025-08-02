#!/usr/bin/env python3
"""
DocuFlow 最终功能测试
测试所有核心功能是否正常工作
"""

import os
import sys
import time
import requests
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from converter.document_converter import DocumentConverter

def test_converter_initialization():
    """测试转换器初始化"""
    print("🔧 测试转换器初始化...")
    try:
        converter = DocumentConverter()
        print("✅ 转换器初始化成功")
        return converter
    except Exception as e:
        print(f"❌ 转换器初始化失败: {e}")
        return None

def test_supported_formats(converter):
    """测试支持的格式"""
    print("\n📋 测试支持的格式...")
    try:
        formats = converter.get_supported_conversions()
        print(f"✅ 支持的转换格式: {len(formats)} 种")
        for fmt in list(formats.keys())[:5]:  # 显示前5种
            print(f"   {fmt} -> {formats[fmt]}")
        if len(formats) > 5:
            print(f"   ... 还有 {len(formats) - 5} 种格式")
        return True
    except Exception as e:
        print(f"❌ 获取支持格式失败: {e}")
        return False

def test_file_conversion(converter):
    """测试文件转换"""
    print("\n🔄 测试文件转换...")
    
    # 创建测试文件
    test_md = "test_final.md"
    test_html = "test_final.html"
    
    with open(test_md, 'w', encoding='utf-8') as f:
        f.write("""# 最终测试文档

这是一个测试文档，用于验证转换功能。

## 功能列表

- [x] Markdown 转 HTML
- [x] 支持中文内容
- [x] 支持代码块

```python
def hello():
    print("Hello, DocuFlow!")
```

## 表格测试

| 功能 | 状态 |
|------|------|
| 转换 | ✅ |
| 测试 | ✅ |
""")
    
    try:
        result = converter.convert_file(test_md, test_html)
        if os.path.exists(test_html):
            print(f"✅ 文件转换成功: {result}")
            
            # 检查输出文件大小
            size = os.path.getsize(test_html)
            print(f"   输出文件大小: {size} 字节")
            
            # 清理测试文件
            os.remove(test_md)
            os.remove(test_html)
            return True
        else:
            print("❌ 输出文件未生成")
            return False
    except Exception as e:
        print(f"❌ 文件转换失败: {e}")
        return False

def test_web_service():
    """测试Web服务"""
    print("\n🌐 测试Web服务...")
    try:
        # 测试主页
        response = requests.get("http://localhost:5003", timeout=5)
        if response.status_code == 200:
            print("✅ Web服务主页访问正常")
        else:
            print(f"❌ Web服务主页访问失败: {response.status_code}")
            return False
        
        # 测试统计接口
        response = requests.get("http://localhost:5003/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 统计接口正常: {stats}")
        else:
            print(f"❌ 统计接口访问失败: {response.status_code}")
            return False
        
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Web服务连接失败 - 服务可能未启动")
        return False
    except Exception as e:
        print(f"❌ Web服务测试失败: {e}")
        return False

def test_cli_functionality():
    """测试CLI功能"""
    print("\n💻 测试CLI功能...")
    
    # 创建测试文件
    test_md = "test_cli_final.md"
    test_html = "test_cli_final.html"
    
    with open(test_md, 'w', encoding='utf-8') as f:
        f.write("# CLI测试\n\n这是CLI功能测试文档。")
    
    try:
        # 测试CLI转换
        import subprocess
        result = subprocess.run([
            sys.executable, "main_cli.py", test_md, test_html
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(test_html):
            print("✅ CLI转换功能正常")
            
            # 清理测试文件
            os.remove(test_md)
            os.remove(test_html)
            return True
        else:
            print(f"❌ CLI转换失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("🚀 DocuFlow 最终功能测试")
    print("=" * 50)
    
    # 测试结果
    results = []
    
    # 1. 测试转换器初始化
    converter = test_converter_initialization()
    results.append(converter is not None)
    
    if converter:
        # 2. 测试支持的格式
        results.append(test_supported_formats(converter))
        
        # 3. 测试文件转换
        results.append(test_file_conversion(converter))
    else:
        results.extend([False, False])
    
    # 4. 测试Web服务
    results.append(test_web_service())
    
    # 5. 测试CLI功能
    results.append(test_cli_functionality())
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    test_names = [
        "转换器初始化",
        "支持格式查询",
        "文件转换功能",
        "Web服务接口",
        "CLI命令行功能"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("🎉 所有功能测试通过！DocuFlow 已完全修复并正常工作。")
        return True
    else:
        print("⚠️  部分功能存在问题，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)