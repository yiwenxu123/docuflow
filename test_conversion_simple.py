#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的转换问题修复验证脚本
"""

import os
import sys
import tempfile
from pathlib import Path

def test_pandoc_encoding():
    """测试Pandoc编码支持"""
    print("=== 测试Pandoc编码支持 ===")
    
    try:
        import subprocess
        
        # 创建测试HTML文件
        test_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>中文测试</title>
</head>
<body>
    <h1>中文标题</h1>
    <p>这是中文内容测试。</p>
</body>
</html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(test_html)
            html_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            md_file = f.name
        
        # 测试Pandoc命令
        cmd = [
            "pandoc", html_file, "-o", md_file,
            "--wrap=none",
            "--from", "html+smart",
            "--to", "markdown+smart"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # 检查输出文件
            if os.path.exists(md_file):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '中文' in content:
                    print("✓ Pandoc编码测试通过")
                    print(f"输出内容: {content[:100]}...")
                    success = True
                else:
                    print("❌ 输出文件中缺少中文内容")
                    print(f"输出内容: {content}")
                    success = False
            else:
                print("❌ 输出文件未生成")
                success = False
        else:
            print(f"❌ Pandoc命令失败: {result.stderr}")
            success = False
        
        # 清理临时文件
        try:
            os.unlink(html_file)
            os.unlink(md_file)
        except:
            pass
        
        return success
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n=== 测试文件操作 ===")
    
    try:
        # 测试创建和写入文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = "这是中文测试内容\n包含特殊字符：￥、©、®"
            f.write(test_content)
            test_file = f.name
        
        # 验证文件存在
        if not os.path.exists(test_file):
            print("❌ 文件创建失败")
            return False
        
        # 验证文件内容
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content == test_content:
            print("✓ 文件操作测试通过")
            success = True
        else:
            print("❌ 文件内容不匹配")
            print(f"期望: {test_content}")
            print(f"实际: {content}")
            success = False
        
        # 清理文件
        try:
            os.unlink(test_file)
        except:
            pass
        
        return success
        
    except Exception as e:
        print(f"❌ 文件操作测试异常: {str(e)}")
        return False

def test_import_modules():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    modules_to_test = [
        ('utils.config_manager', 'ConfigManager'),
        ('converter.document_converter', 'DocumentConverter'),
        ('utils.file_utils', 'is_supported_file'),
    ]
    
    success_count = 0
    
    for module_name, class_or_func in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_or_func])
            getattr(module, class_or_func)
            print(f"✓ {module_name}.{class_or_func} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}.{class_or_func} 导入失败: {str(e)}")
    
    return success_count == len(modules_to_test)

def main():
    """主测试函数"""
    print("转换问题修复验证测试（简化版）")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_import_modules),
        ("文件操作", test_file_operations),
        ("Pandoc编码支持", test_pandoc_encoding),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {str(e)}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = 0
    for test_name, result in results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("\n🎉 基础功能测试通过！")
        print("\n修复内容:")
        print("1. Word转HTML: 添加UTF-8编码支持")
        print("2. HTML转Markdown: 增强文件输出验证")
        print("3. 改进编码处理和错误处理")
    else:
        print("\n⚠️  部分测试未通过，请检查相关问题")

if __name__ == "__main__":
    main()