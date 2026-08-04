#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户提供的HTML文件的图片过滤功能
"""

import os
import sys
import tempfile
import shutil
from converter.document_converter import DocumentConverter
from config import Config

def test_user_file():
    """测试用户提供的HTML文件"""
    print("开始测试用户提供的HTML文件...")
    
    # 用户提供的文件路径
    html_file = "/Users/yiwenxu123/Downloads/llm-wiki (2026_4_7 14：47：37).html"
    
    # 检查文件是否存在
    if not os.path.exists(html_file):
        print(f"❌ 文件不存在: {html_file}")
        return
    
    print(f"找到文件: {html_file}")
    print(f"文件大小: {os.path.getsize(html_file)} 字节")
    
    # 初始化转换器
    config = Config()
    converter = DocumentConverter(config)
    
    # 创建临时输出目录
    output_dir = tempfile.mkdtemp(prefix='docuflow_test_')
    print(f"创建输出目录: {output_dir}")
    
    try:
        # 测试HTML转Markdown（带图片过滤）
        print("\n测试HTML转Markdown（带图片过滤）...")
        output_file = os.path.join(output_dir, 'output.md')
        result = converter.convert_file(html_file, '.md', output_dir, filter_images=True)
        print(f"转换完成: {result}")
        
        # 读取转换结果
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计结果
        original_size = os.path.getsize(html_file)
        output_size = os.path.getsize(result)
        
        print(f"\n转换统计:")
        print(f"原始文件大小: {original_size} 字节")
        print(f"输出文件大小: {output_size} 字节")
        print(f"文件大小变化: {((output_size - original_size) / original_size * 100):.2f}%")
        
        # 检查是否包含图片标签
        has_img_tags = '<img' in content
        has_image_refs = '!' in content
        
        print(f"\n图片过滤结果:")
        print(f"是否包含图片标签: {'❌ 是' if has_img_tags else '✅ 否'}")
        print(f"是否包含图片引用: {'❌ 是' if has_image_refs else '✅ 否'}")
        
        # 显示转换结果的前500个字符
        print("\n转换结果预览（前500字符）:")
        print(content[:500] + "...")
        
        # 保存结果到用户下载目录
        user_output = "/Users/yiwenxu123/Downloads/llm-wiki_filtered.md"
        shutil.copy(result, user_output)
        print(f"\n✅ 过滤后的文件已保存到: {user_output}")
        
        print("\n测试完成！")
        
    finally:
        # 清理临时文件
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        print("\n清理临时文件完成")

if __name__ == "__main__":
    test_user_file()
