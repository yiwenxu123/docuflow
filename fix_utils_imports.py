#!/usr/bin/env python3
"""
修复deploy/utils目录下的导入问题
"""

import os
import re

def fix_utils_imports():
    """修复utils目录下的相对导入"""
    utils_dir = "deploy/utils"
    
    # 需要修复的文件
    files_to_fix = [
        "config_manager.py",
        "error_handler.py", 
        "file_utils.py",
        "logger.py",
        "performance.py"
    ]
    
    # 导入替换规则
    import_fixes = [
        (r'from \.utils\.logger import', 'from utils.logger import'),
        (r'from \.utils\.config_manager import', 'from utils.config_manager import'),
        (r'from \.utils\.error_handler import', 'from utils.error_handler import'),
        (r'from \.utils\.file_utils import', 'from utils.file_utils import'),
        (r'from \.utils\.performance import', 'from utils.performance import'),
        (r'from \.logger import', 'from utils.logger import'),
        (r'from \.config_manager import', 'from utils.config_manager import'),
        (r'from \.error_handler import', 'from utils.error_handler import'),
        (r'from \.file_utils import', 'from utils.file_utils import'),
        (r'from \.performance import', 'from utils.performance import'),
    ]
    
    fixed_files = []
    
    for filename in files_to_fix:
        filepath = os.path.join(utils_dir, filename)
        if not os.path.exists(filepath):
            print(f"⚠️  文件不存在: {filepath}")
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 应用所有修复规则
            for pattern, replacement in import_fixes:
                content = re.sub(pattern, replacement, content)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(filename)
                print(f"✅ 修复导入: {filename}")
            else:
                print(f"ℹ️  无需修复: {filename}")
                
        except Exception as e:
            print(f"❌ 修复失败 {filename}: {e}")
    
    print(f"\n🎉 修复完成! 共修复 {len(fixed_files)} 个文件")
    if fixed_files:
        print("修复的文件:", ", ".join(fixed_files))

if __name__ == "__main__":
    fix_utils_imports()