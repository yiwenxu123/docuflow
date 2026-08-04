#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片过滤功能
"""

import os
import sys
import tempfile
from converter.document_converter import DocumentConverter
from config import Config

# 创建测试文件
def create_test_files():
    """创建测试文件"""
    # 创建包含图片的HTML文件
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>测试文件</title>
</head>
<body>
    <h1>测试标题</h1>
    <p>这是一段测试文本</p>
    <img src="test.jpg" alt="测试图片">
    <p>这是另一段测试文本</p>
    <picture>
        <source srcset="test.webp" type="image/webp">
        <img src="test.jpg" alt="测试图片2">
    </picture>
    <p>这是最后一段测试文本</p>
</body>
</html>
    """
    
    # 创建包含图片的Markdown文件
    md_content = """
# 测试标题

这是一段测试文本

![测试图片](test.jpg)

这是另一段测试文本

![测试图片2](test2.jpg "图片标题")

这是最后一段测试文本
    """
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(md_content)
        md_file = f.name
    
    return html_file, md_file

def test_image_filtering():
    """测试图片过滤功能"""
    print("开始测试图片过滤功能...")
    
    # 创建测试文件
    html_file, md_file = create_test_files()
    print(f"创建测试文件: {html_file}, {md_file}")
    
    # 初始化转换器
    config = Config()
    converter = DocumentConverter(config)
    
    # 创建临时输出目录
    output_dir = tempfile.mkdtemp(prefix='docuflow_test_')
    print(f"创建输出目录: {output_dir}")
    
    try:
        # 测试HTML转Markdown（带图片过滤）
        print("\n测试HTML转Markdown（带图片过滤）...")
        html_output = os.path.join(output_dir, 'html_output.md')
        result = converter.convert_file(html_file, '.md', output_dir, filter_images=True)
        print(f"转换完成: {result}")
        
        # 读取转换结果
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        print("转换结果:")
        print(content)
        print("\n检查是否包含图片标签:")
        if '<img' in content or '!' in content:
            print("❌ 警告：可能包含图片标签")
        else:
            print("✅ 没有图片标签，过滤成功")
        
        # 测试Markdown内容的图片过滤
        print("\n测试Markdown内容的图片过滤...")
        # 直接测试图片过滤方法
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        filtered_content = converter._filter_images_from_markdown(md_content)
        print("过滤后的内容:")
        print(filtered_content)
        print("\n检查是否包含图片引用:")
        if '!' in filtered_content:
            print("❌ 警告：可能包含图片引用")
        else:
            print("✅ 没有图片引用，过滤成功")
        
        print("\n图片过滤功能测试完成！")
        
    finally:
        # 清理临时文件
        if os.path.exists(html_file):
            os.remove(html_file)
        if os.path.exists(md_file):
            os.remove(md_file)
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
        print("\n清理临时文件完成")

if __name__ == "__main__":
    test_image_filtering()
