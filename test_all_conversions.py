#!/usr/bin/env python3
"""
全面的文档转换测试脚本
测试各种文件格式的转换功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from converter.document_converter import DocumentConverter
from utils.config_manager import ConfigManager

def create_test_files(test_dir):
    """创建各种格式的测试文件"""
    test_files = {}
    
    # 创建TXT文件
    txt_file = test_dir / "test.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文档。\n\n包含多行内容。\n\n# 标题\n\n- 列表项1\n- 列表项2\n")
    test_files['txt'] = txt_file
    
    # 创建Markdown文件
    md_file = test_dir / "test.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 测试文档\n\n这是一个**Markdown**文档。\n\n## 子标题\n\n- 列表项1\n- 列表项2\n\n```python\nprint('Hello World')\n```\n")
    test_files['md'] = md_file
    
    # 创建HTML文件
    html_file = test_dir / "test.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>测试文档</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>测试文档</h1>
    <p>这是一个<strong>HTML</strong>文档。</p>
    <h2>子标题</h2>
    <ul>
        <li>列表项1</li>
        <li>列表项2</li>
    </ul>
    <pre><code>print('Hello World')</code></pre>
</body>
</html>""")
    test_files['html'] = html_file
    
    return test_files

def test_conversion(converter, input_file, output_format, test_name):
    """测试单个转换"""
    try:
        print(f"   测试 {test_name}...")
        output_path = converter.convert_file(str(input_file), output_format)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"   ✓ 转换成功: {output_path} (大小: {file_size} bytes)")
            
            # 显示内容预览
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"   内容预览: {preview}")
            
            return True
        else:
            print(f"   ✗ 转换失败: 输出文件不存在")
            return False
            
    except Exception as e:
        print(f"   ✗ 转换失败: {str(e)}")
        return False

def main():
    print("=== DocuFlow 全面转换测试 ===\n")
    
    # 初始化转换器
    try:
        config_manager = ConfigManager()
        converter = DocumentConverter(config_manager)
        print("1. ✓ 转换器初始化成功")
    except Exception as e:
        print(f"1. ✗ 转换器初始化失败: {e}")
        return
    
    # 创建临时测试目录
    test_dir = Path("test_conversion_files")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    try:
        print("2. ✓ 创建测试目录成功")
        
        # 创建测试文件
        test_files = create_test_files(test_dir)
        print("3. ✓ 创建测试文件成功")
        
        # 定义转换测试
        conversions = [
            # 基本文本转换
            (test_files['txt'], '.md', 'TXT -> Markdown'),
            (test_files['txt'], '.html', 'TXT -> HTML'),
            
            # Markdown转换
            (test_files['md'], '.html', 'Markdown -> HTML'),
            (test_files['md'], '.txt', 'Markdown -> TXT'),
            
            # HTML转换
            (test_files['html'], '.md', 'HTML -> Markdown'),
            (test_files['html'], '.txt', 'HTML -> TXT'),
        ]
        
        print("\n4. 开始转换测试:")
        success_count = 0
        total_count = len(conversions)
        
        for input_file, output_format, test_name in conversions:
            if test_conversion(converter, input_file, output_format, test_name):
                success_count += 1
            print()  # 空行分隔
        
        # 显示测试结果
        print(f"=== 测试结果 ===")
        print(f"总测试数: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        
        if success_count == total_count:
            print("\n🎉 所有转换测试通过！")
        else:
            print(f"\n⚠️  有 {total_count - success_count} 个测试失败")
            
    finally:
        # 清理测试文件
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"\n5. ✓ 清理测试文件完成")

if __name__ == "__main__":
    main()