#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 功能测试脚本
测试PDF转MD、Excel转MD等所有转换功能
"""

import os
import sys
from pathlib import Path
import tempfile
from converter.document_converter import DocumentConverter

def create_test_excel():
    """创建测试Excel文件"""
    try:
        import openpyxl
        
        # 创建工作簿
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "测试数据"
        
        # 添加测试数据
        headers = ["姓名", "年龄", "职业", "城市", "薪资"]
        ws.append(headers)
        
        test_data = [
            ["张三", 28, "软件工程师", "北京", 15000],
            ["李四", 32, "产品经理", "上海", 18000],
            ["王五", 25, "UI设计师", "深圳", 12000],
            ["赵六", 30, "数据分析师", "杭州", 14000],
            ["钱七", 35, "项目经理", "广州", 20000]
        ]
        
        for row in test_data:
            ws.append(row)
        
        # 添加第二个工作表
        ws2 = wb.create_sheet("销售数据")
        sales_headers = ["月份", "销售额", "增长率"]
        ws2.append(sales_headers)
        
        sales_data = [
            ["1月", 100000, "5%"],
            ["2月", 120000, "20%"],
            ["3月", 110000, "-8.3%"],
            ["4月", 135000, "22.7%"]
        ]
        
        for row in sales_data:
            ws2.append(row)
        
        # 保存文件
        test_file = "test_conversion.xlsx"
        wb.save(test_file)
        print(f"✅ 创建测试Excel文件: {test_file}")
        return test_file
        
    except Exception as e:
        print(f"❌ 创建Excel文件失败: {e}")
        return None

def create_test_markdown():
    """创建测试Markdown文件"""
    content = """
# DocuFlow 测试文档

## 简介

这是一个用于测试DocuFlow转换功能的Markdown文档。

## 功能特性

### 支持的格式

- **PDF文档** (.pdf)
- **Word文档** (.docx)
- **Excel表格** (.xlsx, .xls)
- **Markdown文档** (.md)
- **HTML文档** (.html)
- **EPUB电子书** (.epub)

### 转换功能

1. **PDF转Markdown**: 提取PDF中的文本和表格
2. **Excel转Markdown**: 将Excel表格转换为Markdown表格格式
3. **Word转Markdown**: 保留文档结构和格式
4. **跨格式转换**: 支持多种格式之间的相互转换

## 技术特点

| 特性 | 描述 | 状态 |
|------|------|------|
| 批量转换 | 支持多文件同时转换 | ✅ 已实现 |
| 进度显示 | 实时显示转换进度 | ✅ 已实现 |
| 错误处理 | 详细的错误信息和日志 | ✅ 已实现 |
| 现代UI | 美观的用户界面 | ✅ 已实现 |

## 使用方法

### 命令行使用

```bash
# 启动GUI界面
python run_modern_gui.py

# 或使用原始界面
python main.py
```

### 编程接口

```python
from converter.document_converter import DocumentConverter

converter = DocumentConverter()
output_file = converter.convert_file(
    "input.pdf", 
    ".md", 
    "output_dir", 
    keep_original_name=True
)
```

## 注意事项

> **重要**: 确保安装了所有必要的依赖包:
> - PyPDF2
> - pdfplumber
> - openpyxl
> - pandas
> - PySide6 或 PyQt5

## 更新日志

### v2.0 (最新)
- ✨ 全新现代化UI界面
- 🚀 优化转换性能
- 🐛 修复PDF转换问题
- 📊 增强Excel处理能力

### v1.0
- 🎉 初始版本发布
- 📄 基础转换功能
- 🖥️ 简单GUI界面

---

**DocuFlow** - 让文档转换更简单！
"""
    
    test_file = "test_document.md"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 创建测试Markdown文件: {test_file}")
    return test_file

def test_pdf_conversion():
    """测试PDF转换功能"""
    print("\n🔍 测试PDF转换功能...")
    
    # 查找现有的PDF文件
    pdf_files = []
    for file in os.listdir('.'):
        if file.lower().endswith('.pdf'):
            pdf_files.append(file)
    
    if not pdf_files:
        print("⚠️ 未找到PDF文件，跳过PDF转换测试")
        return True
    
    converter = DocumentConverter()
    success_count = 0
    
    for pdf_file in pdf_files[:2]:  # 只测试前2个PDF文件
        try:
            print(f"   转换: {pdf_file}")
            output_file = converter.convert_file(
                pdf_file, ".md", 
                "test_output", 
                keep_original_name=True
            )
            
            if output_file and os.path.exists(output_file):
                print(f"   ✅ 成功: {output_file}")
                success_count += 1
            else:
                print(f"   ❌ 失败: 输出文件不存在")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    
    print(f"PDF转换测试完成: {success_count}/{len(pdf_files[:2])} 成功")
    return success_count > 0

def test_excel_conversion():
    """测试Excel转换功能"""
    print("\n📊 测试Excel转换功能...")
    
    # 创建测试Excel文件
    test_file = create_test_excel()
    if not test_file:
        return False
    
    try:
        converter = DocumentConverter()
        output_file = converter.convert_file(
            test_file, ".md", 
            "test_output", 
            keep_original_name=True
        )
        
        if output_file and os.path.exists(output_file):
            print(f"✅ Excel转换成功: {output_file}")
            
            # 检查输出内容
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "姓名" in content and "销售数据" in content:
                    print("✅ 输出内容验证通过")
                    return True
                else:
                    print("❌ 输出内容验证失败")
                    return False
        else:
            print("❌ Excel转换失败")
            return False
            
    except Exception as e:
        print(f"❌ Excel转换错误: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)

def test_markdown_conversion():
    """测试Markdown转换功能"""
    print("\n📝 测试Markdown转换功能...")
    
    # 创建测试Markdown文件
    test_file = create_test_markdown()
    
    try:
        converter = DocumentConverter()
        
        # 测试转换为HTML
        output_file = converter.convert_file(
            test_file, ".html", 
            "test_output", 
            keep_original_name=True
        )
        
        if output_file and os.path.exists(output_file):
            print(f"✅ Markdown转HTML成功: {output_file}")
            return True
        else:
            print("❌ Markdown转换失败")
            return False
            
    except Exception as e:
        print(f"❌ Markdown转换错误: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)

def test_batch_conversion():
    """测试批量转换功能"""
    print("\n🔄 测试批量转换功能...")
    
    # 创建多个测试文件
    test_files = []
    
    # 创建Excel文件
    excel_file = create_test_excel()
    if excel_file:
        test_files.append(excel_file)
    
    # 创建Markdown文件
    md_file = create_test_markdown()
    if md_file:
        test_files.append(md_file)
    
    if not test_files:
        print("❌ 无法创建测试文件")
        return False
    
    try:
        converter = DocumentConverter()
        success_count = 0
        
        for test_file in test_files:
            try:
                output_file = converter.convert_file(
                    test_file, ".html", 
                    "test_output", 
                    keep_original_name=True
                )
                
                if output_file and os.path.exists(output_file):
                    success_count += 1
                    print(f"   ✅ {test_file} -> {output_file}")
                else:
                    print(f"   ❌ {test_file} 转换失败")
                    
            except Exception as e:
                print(f"   ❌ {test_file} 错误: {e}")
        
        print(f"批量转换完成: {success_count}/{len(test_files)} 成功")
        return success_count == len(test_files)
        
    finally:
        # 清理测试文件
        for test_file in test_files:
            if os.path.exists(test_file):
                os.remove(test_file)

def main():
    """主测试函数"""
    print("🧪 DocuFlow 功能测试开始")
    print("=" * 50)
    
    # 确保输出目录存在
    os.makedirs("test_output", exist_ok=True)
    
    # 运行各项测试
    tests = [
        ("Excel转换", test_excel_conversion),
        ("Markdown转换", test_markdown_conversion),
        ("PDF转换", test_pdf_conversion),
        ("批量转换", test_batch_conversion)
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
    print("📋 测试结果汇总:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("🎉 所有功能测试通过！DocuFlow运行正常。")
    else:
        print("⚠️ 部分功能存在问题，请检查错误信息。")
    
    return passed == len(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)