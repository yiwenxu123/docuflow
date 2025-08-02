#!/usr/bin/env python3
"""
修复部署包中的导入路径问题
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """修复单个文件中的导入路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复相对导入
        fixes = [
            # 修复 exceptions 导入
            (r'from exceptions import', 'from .exceptions import'),
            (r'import exceptions', 'from . import exceptions'),
            
            # 修复 config 导入
            (r'from config import', 'from .config import'),
            (r'import config\b', 'from . import config'),
            
            # 修复 utils 导入
            (r'from utils\.', 'from .utils.'),
            
            # 修复其他模块导入
            (r'from converter\.', 'from .converter.'),
            (r'from ui\.', 'from .ui.'),
        ]
        
        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 修复失败 {file_path}: {e}")
        return False

def fix_all_imports(deploy_dir):
    """修复部署目录中所有Python文件的导入"""
    deploy_path = Path(deploy_dir)
    fixed_count = 0
    
    # 遍历所有Python文件
    for py_file in deploy_path.rglob("*.py"):
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\n🎉 修复完成！共修复 {fixed_count} 个文件")

if __name__ == "__main__":
    deploy_dir = "/Users/yiwenxu123/Documents/tare/文档转换/deploy"
    print("🔧 开始修复导入路径...")
    fix_all_imports(deploy_dir)