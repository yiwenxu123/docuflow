#!/usr/bin/env python3
"""
测试HTML到DOCX转换
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from converter.document_converter import DocumentConverter
from utils.config_manager import ConfigManager

def test_html_to_docx():
    """测试HTML到DOCX转换"""
    print("测试HTML到DOCX转换...")
    
    # 创建测试HTML文件
    test_html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>测试文档</title>
    </head>
    <body>
        <h1>这是一个测试标题</h1>
        <p>这是一个测试段落，包含一些<strong>粗体文本</strong>和<em>斜体文本</em>。</p>
        <ul>
            <li>列表项1</li>
            <li>列表项2</li>
            <li>列表项3</li>
        </ul>
        <p>这是另一个段落。</p>
    </body>
    </html>
    """
    
    test_html_file = "test_conversion.html"
    with open(test_html_file, 'w', encoding='utf-8') as f:
        f.write(test_html_content)
    
    try:
        # 初始化转换器
        config_manager = ConfigManager()
        converter = DocumentConverter(config_manager)
        
        # 检查转换支持
        print(f"HTML到DOCX转换支持: {converter.can_convert('.html', '.docx')}")
        
        # 执行转换
        output_file = converter.convert_file(test_html_file, '.docx')
        print(f"✅ 转换成功: {output_file}")
        
        # 检查输出文件
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"输出文件大小: {file_size} 字节")
        else:
            print("❌ 输出文件不存在")
            
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        if os.path.exists(test_html_file):
            os.remove(test_html_file)
        
        output_docx = "test_conversion.docx"
        if os.path.exists(output_docx):
            print(f"清理输出文件: {output_docx}")
            os.remove(output_docx)

if __name__ == "__main__":
    test_html_to_docx()