#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 问题诊断工具
用于快速诊断转换功能问题
"""

import sys
import os
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """检查Python版本"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 7:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro} (需要3.7+)"

def check_dependencies() -> Dict[str, Tuple[bool, str]]:
    """检查依赖库"""
    dependencies = {
        'PySide6': 'GUI框架',
        'PyPDF2': 'PDF处理',
        'pdfplumber': 'PDF文本提取',
        'python-docx': 'Word文档处理',
        'openpyxl': 'Excel处理',
        'pandas': '数据处理',
        'PyYAML': '配置文件',
        'pydantic': '数据验证'
    }
    
    results = {}
    for package, description in dependencies.items():
        try:
            __import__(package.lower().replace('-', '_'))
            results[package] = (True, f"✅ {package} ({description})")
        except ImportError:
            results[package] = (False, f"❌ {package} 未安装 ({description})")
    
    return results

def check_pandoc() -> Tuple[bool, str]:
    """检查Pandoc"""
    try:
        import subprocess
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            return True, f"✅ {version}"
        else:
            return False, "❌ Pandoc未正确安装"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "❌ Pandoc未找到或无法执行"

def check_converter_functionality() -> Dict[str, Tuple[bool, str]]:
    """检查转换器功能"""
    results = {}
    
    try:
        from converter.document_converter import DocumentConverter
        converter = DocumentConverter()
        
        # 检查PDF支持
        try:
            pdf_support = converter.can_convert('.pdf', '.md')
            results['PDF转换'] = (pdf_support, "✅ PDF转换支持" if pdf_support else "❌ PDF转换不支持")
        except Exception as e:
            results['PDF转换'] = (False, f"❌ PDF转换检查失败: {str(e)}")
        
        # 检查Excel支持
        try:
            excel_support = converter.can_convert('.xlsx', '.md')
            results['Excel转换'] = (excel_support, "✅ Excel转换支持" if excel_support else "❌ Excel转换不支持")
        except Exception as e:
            results['Excel转换'] = (False, f"❌ Excel转换检查失败: {str(e)}")
        
        # 检查Word支持
        try:
            word_support = converter.can_convert('.docx', '.md')
            results['Word转换'] = (word_support, "✅ Word转换支持" if word_support else "❌ Word转换不支持")
        except Exception as e:
            results['Word转换'] = (False, f"❌ Word转换检查失败: {str(e)}")
            
    except ImportError as e:
        results['转换器导入'] = (False, f"❌ 无法导入转换器: {str(e)}")
    except Exception as e:
        results['转换器初始化'] = (False, f"❌ 转换器初始化失败: {str(e)}")
    
    return results

def check_file_permissions() -> List[Tuple[bool, str]]:
    """检查文件权限"""
    results = []
    
    # 检查当前目录权限
    current_dir = Path.cwd()
    if os.access(current_dir, os.R_OK | os.W_OK):
        results.append((True, f"✅ 当前目录可读写: {current_dir}"))
    else:
        results.append((False, f"❌ 当前目录权限不足: {current_dir}"))
    
    # 检查应用目录
    app_path = Path.home() / "Applications" / "DocuFlow.app"
    if app_path.exists():
        if os.access(app_path, os.X_OK):
            results.append((True, f"✅ 应用可执行: {app_path}"))
        else:
            results.append((False, f"❌ 应用无执行权限: {app_path}"))
    else:
        results.append((False, f"❌ 应用未找到: {app_path}"))
    
    return results

def test_actual_conversion() -> Dict[str, Tuple[bool, str]]:
    """测试实际转换功能"""
    results = {}
    
    try:
        from converter.document_converter import DocumentConverter
        converter = DocumentConverter()
        
        # 测试文件路径
        test_files = {
            'PDF': 'test_document.pdf',
            'Excel': 'test_excel.xlsx',
            'Word': 'test_word.docx'
        }
        
        for file_type, filename in test_files.items():
            if Path(filename).exists():
                try:
                    output_path = converter.convert_file(filename, '.md')
                    if Path(output_path).exists():
                        file_size = Path(output_path).stat().st_size
                        results[f'{file_type}实际转换'] = (True, f"✅ {file_type}转换成功 ({file_size}字节)")
                    else:
                        results[f'{file_type}实际转换'] = (False, f"❌ {file_type}转换失败: 输出文件不存在")
                except Exception as e:
                    results[f'{file_type}实际转换'] = (False, f"❌ {file_type}转换异常: {str(e)}")
            else:
                results[f'{file_type}实际转换'] = (False, f"⚠️ {file_type}测试文件不存在: {filename}")
    
    except Exception as e:
        results['转换测试'] = (False, f"❌ 转换测试失败: {str(e)}")
    
    return results

def generate_fix_suggestions(all_results: Dict) -> List[str]:
    """生成修复建议"""
    suggestions = []
    
    # Python版本问题
    if not all_results.get('python_version', (True, ''))[0]:
        suggestions.append("🔧 请升级Python到3.7或更高版本")
    
    # 依赖问题
    missing_deps = [pkg for pkg, (success, _) in all_results.get('dependencies', {}).items() if not success]
    if missing_deps:
        suggestions.append(f"🔧 安装缺失依赖: pip3 install {' '.join(missing_deps)}")
    
    # Pandoc问题
    if not all_results.get('pandoc', (True, ''))[0]:
        suggestions.append("🔧 安装Pandoc: brew install pandoc")
    
    # 权限问题
    permission_issues = [msg for success, msg in all_results.get('permissions', []) if not success]
    if permission_issues:
        suggestions.append("🔧 修复权限: chmod -R 755 ~/Applications/DocuFlow.app")
    
    # 转换功能问题
    conversion_issues = [name for name, (success, _) in all_results.get('converter_functionality', {}).items() if not success]
    if conversion_issues:
        suggestions.append(f"🔧 转换功能问题: {', '.join(conversion_issues)}")
        suggestions.append("🔧 尝试重新安装: bash install.sh")
    
    if not suggestions:
        suggestions.append("🎉 所有检查都通过了！如果仍有问题，请提供具体的错误信息。")
    
    return suggestions

def main():
    """主函数"""
    print("🔍 DocuFlow 问题诊断工具")
    print("=" * 50)
    
    all_results = {}
    
    # 1. 检查Python版本
    print("\n📋 检查Python版本...")
    python_ok, python_msg = check_python_version()
    all_results['python_version'] = (python_ok, python_msg)
    print(python_msg)
    
    # 2. 检查依赖库
    print("\n📦 检查依赖库...")
    deps_results = check_dependencies()
    all_results['dependencies'] = deps_results
    for package, (success, message) in deps_results.items():
        print(f"  {message}")
    
    # 3. 检查Pandoc
    print("\n🔧 检查Pandoc...")
    pandoc_ok, pandoc_msg = check_pandoc()
    all_results['pandoc'] = (pandoc_ok, pandoc_msg)
    print(pandoc_msg)
    
    # 4. 检查转换器功能
    print("\n⚙️ 检查转换器功能...")
    converter_results = check_converter_functionality()
    all_results['converter_functionality'] = converter_results
    for name, (success, message) in converter_results.items():
        print(f"  {message}")
    
    # 5. 检查文件权限
    print("\n🔐 检查文件权限...")
    permission_results = check_file_permissions()
    all_results['permissions'] = permission_results
    for success, message in permission_results:
        print(f"  {message}")
    
    # 6. 测试实际转换
    print("\n🧪 测试实际转换...")
    conversion_results = test_actual_conversion()
    all_results['actual_conversion'] = conversion_results
    for name, (success, message) in conversion_results.items():
        print(f"  {message}")
    
    # 7. 生成修复建议
    print("\n💡 修复建议:")
    suggestions = generate_fix_suggestions(all_results)
    for suggestion in suggestions:
        print(f"  {suggestion}")
    
    # 8. 总结
    print("\n" + "=" * 50)
    total_checks = sum(len(results) if isinstance(results, dict) else 1 
                      for results in all_results.values() if isinstance(results, (dict, tuple)))
    passed_checks = sum(
        sum(1 for success, _ in results.values() if success) if isinstance(results, dict)
        else (1 if results[0] else 0) if isinstance(results, tuple)
        else sum(1 for success, _ in results if success) if isinstance(results, list)
        else 0
        for results in all_results.values()
    )
    
    print(f"📊 诊断完成: {passed_checks}/{total_checks} 项检查通过")
    
    if passed_checks == total_checks:
        print("🎉 所有检查都通过！DocuFlow应该可以正常工作。")
    else:
        print("⚠️ 发现问题，请按照上述建议进行修复。")
    
    print("\n如需更多帮助，请查看 代码质量改进建议.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 诊断已取消")
    except Exception as e:
        print(f"\n\n❌ 诊断工具出错: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()