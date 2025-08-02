#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 转 Markdown 功能测试脚本

此脚本用于测试 DocuFlow 新增的 Excel 转 Markdown 功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from converter.document_converter import DocumentConverter
    from config import config
    print("✅ 核心模块导入成功")
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

# 检查 Excel 支持
try:
    import openpyxl
    import pandas as pd
    EXCEL_AVAILABLE = True
    print("✅ Excel 处理库可用")
except ImportError:
    EXCEL_AVAILABLE = False
    print("⚠️  Excel 处理库不可用，将使用 MCP 服务器进行测试")

def create_test_excel_file(file_path: str) -> None:
    """创建测试用的 Excel 文件"""
    if not EXCEL_AVAILABLE:
        print("⚠️  跳过 Excel 文件创建，因为 openpyxl 不可用")
        return
    
    workbook = openpyxl.Workbook()
    
    # 第一个工作表：员工信息
    ws1 = workbook.active
    ws1.title = "员工信息"
    
    # 添加表头
    headers = ["姓名", "部门", "职位", "工资", "入职日期"]
    for col, header in enumerate(headers, 1):
        ws1.cell(row=1, column=col, value=header)
    
    # 添加数据
    data = [
        ["张三", "技术部", "高级工程师", 15000, "2022-01-15"],
        ["李四", "产品部", "产品经理", 18000, "2021-08-20"],
        ["王五", "设计部", "UI设计师", 12000, "2023-03-10"],
        ["赵六", "技术部", "前端工程师", 13000, "2022-11-05"],
        ["钱七", "运营部", "运营专员", 10000, "2023-06-01"]
    ]
    
    for row_idx, row_data in enumerate(data, 2):
        for col_idx, value in enumerate(row_data, 1):
            ws1.cell(row=row_idx, column=col_idx, value=value)
    
    # 第二个工作表：项目统计
    ws2 = workbook.create_sheet("项目统计")
    
    # 添加项目数据
    project_headers = ["项目名称", "负责人", "状态", "进度", "预算"]
    for col, header in enumerate(project_headers, 1):
        ws2.cell(row=1, column=col, value=header)
    
    project_data = [
        ["DocuFlow", "张三", "进行中", "85%", 500000],
        ["移动应用", "李四", "已完成", "100%", 300000],
        ["网站重构", "王五", "计划中", "10%", 200000],
        ["数据分析", "赵六", "进行中", "60%", 150000]
    ]
    
    for row_idx, row_data in enumerate(project_data, 2):
        for col_idx, value in enumerate(row_data, 1):
            ws2.cell(row=row_idx, column=col_idx, value=value)
    
    # 第三个工作表：空工作表（测试边界情况）
    ws3 = workbook.create_sheet("空工作表")
    
    # 保存文件
    workbook.save(file_path)
    workbook.close()
    print(f"✅ 测试 Excel 文件已创建: {file_path}")

def test_excel_to_markdown_conversion():
    """测试 Excel 转 Markdown 功能"""
    print("🚀 开始测试 Excel 转 Markdown 功能...\n")
    
    if not EXCEL_AVAILABLE:
        print("⚠️  Excel 处理库不可用，跳过实际转换测试")
        print("💡 建议安装依赖: pip install openpyxl pandas")
        return False
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试 Excel 文件
        excel_file = temp_path / "test_data.xlsx"
        create_test_excel_file(str(excel_file))
        
        if not excel_file.exists():
            print("❌ 测试 Excel 文件创建失败")
            return False
        
        # 初始化转换器
        converter = DocumentConverter()
        
        try:
            # 执行转换
            print("📝 正在转换 Excel 文件到 Markdown...")
            output_file = converter.convert_file(
                file_path=str(excel_file),
                output_format=".md",
                output_dir=str(temp_path)
            )
            
            print(f"✅ 转换成功！输出文件: {output_file}")
            
            # 读取并显示转换结果
            with open(output_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            print("\n📄 转换结果预览:")
            print("=" * 50)
            # 只显示前1000个字符
            preview = markdown_content[:1000]
            print(preview)
            if len(markdown_content) > 1000:
                print("\n... (内容已截断，完整内容请查看输出文件)")
            print("=" * 50)
            
            # 显示统计信息
            lines = markdown_content.split('\n')
            print(f"\n📊 转换统计:")
            print(f"   - 总行数: {len(lines)}")
            print(f"   - 字符数: {len(markdown_content)}")
            print(f"   - 表格数量: {markdown_content.count('|')}")
            print(f"   - 工作表数量: {markdown_content.count('## 工作表')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 转换失败: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            return False

def test_converter_capabilities():
    """测试转换器的能力检查"""
    print("\n🔍 测试转换器能力检查...")
    
    converter = DocumentConverter()
    
    # 测试支持的转换
    test_cases = [
        (".xlsx", ".md"),
        (".xls", ".md"),
        (".xlsx", ".html"),
        (".xlsx", ".txt"),  # 不支持的转换
    ]
    
    for source, target in test_cases:
        can_convert = converter.can_convert(source, target)
        status = "✅ 支持" if can_convert else "❌ 不支持"
        print(f"   {source} -> {target}: {status}")

def main():
    """主函数"""
    print("🎯 DocuFlow Excel 转 Markdown 功能测试")
    print("=" * 60)
    
    # 检查依赖
    if EXCEL_AVAILABLE:
        print("✅ Excel 处理库已安装")
    else:
        print("⚠️  Excel 处理库未安装，部分功能将受限")
        print("💡 要完整测试，请运行: pip install openpyxl pandas")
    
    # 测试转换器能力
    test_converter_capabilities()
    
    # 测试实际转换
    success = test_excel_to_markdown_conversion()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！Excel 转 Markdown 功能正常工作。")
        print("\n💡 使用方法:")
        print("   1. GUI 模式: 选择 Excel 文件，选择输出格式为 Markdown")
        print("   2. 命令行: ./docuflow convert input.xlsx --format md")
        print("   3. 快速启动: ./quick_start.sh gui")
    else:
        print("❌ 测试失败，请检查错误信息并修复问题。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)