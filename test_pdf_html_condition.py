#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 测试PDF转HTML的条件判断
input_format = ".pdf"
output_format = ".html"

print(f"输入格式: {input_format}")
print(f"输出格式: {output_format}")
print(f"输入格式匹配: {input_format.lower() == '.pdf'}")
print(f"输出格式匹配: {output_format.lower() in ['.html', '.htm']}")
print(f"整体条件: {input_format.lower() == '.pdf' and output_format.lower() in ['.html', '.htm']}")

# 测试PDF转TXT的条件判断
output_format_txt = ".txt"
print(f"\nPDF转TXT测试:")
print(f"输出格式: {output_format_txt}")
print(f"输出格式匹配: {output_format_txt.lower() == '.txt'}")
print(f"整体条件: {input_format.lower() == '.pdf' and output_format_txt.lower() == '.txt'}")
