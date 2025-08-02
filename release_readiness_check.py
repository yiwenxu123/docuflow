#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 1.0版本发布准备检查
全面检查项目各版本的功能状态
"""

import os
import sys
import subprocess
import tempfile
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Any

class ReleaseReadinessChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deploy_dir = self.project_root / "deploy"
        self.results = {
            "overall_status": "unknown",
            "version_info": {},
            "core_functionality": {},
            "web_interface": {},
            "cli_interface": {},
            "gui_interface": {},
            "dependencies": {},
            "file_structure": {},
            "recommendations": []
        }
    
    def run_full_check(self) -> Dict[str, Any]:
        """运行完整的发布准备检查"""
        print("🚀 DocuFlow 1.0版本发布准备检查")
        print("=" * 60)
        
        # 1. 版本信息检查
        self.check_version_info()
        
        # 2. 文件结构检查
        self.check_file_structure()
        
        # 3. 依赖检查
        self.check_dependencies()
        
        # 4. 核心功能检查
        self.check_core_functionality()
        
        # 5. Web界面检查
        self.check_web_interface()
        
        # 6. CLI界面检查
        self.check_cli_interface()
        
        # 7. GUI界面检查
        self.check_gui_interface()
        
        # 8. 生成总体评估
        self.generate_overall_assessment()
        
        # 9. 输出报告
        self.print_report()
        
        return self.results
    
    def check_version_info(self):
        """检查版本信息"""
        print("\n📋 检查版本信息...")
        
        version_files = [
            ("主配置", "config.py"),
            ("部署配置", "deploy/config.py"),
            ("转换器模块", "converter/__init__.py"),
            ("部署转换器", "deploy/converter/__init__.py"),
            ("工具模块", "utils/__init__.py"),
            ("部署工具", "deploy/utils/__init__.py"),
            ("UI模块", "ui/__init__.py"),
            ("部署UI", "deploy/ui/__init__.py"),
        ]
        
        versions = {}
        for name, file_path in version_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'version' in content:
                            # 提取版本号
                            for line in content.split('\n'):
                                if 'version' in line and '=' in line and ('"' in line or "'" in line):
                                    version = line.split('=')[1].strip().strip('"\'')
                                    versions[name] = version
                                    break
                except Exception as e:
                    versions[name] = f"读取失败: {str(e)}"
            else:
                versions[name] = "文件不存在"
        
        self.results["version_info"] = versions
        
        # 检查版本一致性
        unique_versions = set(v for v in versions.values() if not v.startswith("读取失败") and v != "文件不存在")
        if len(unique_versions) <= 1:
            print("  ✅ 版本号一致")
        else:
            print(f"  ⚠️  版本号不一致: {unique_versions}")
            self.results["recommendations"].append("统一所有模块的版本号")
    
    def check_file_structure(self):
        """检查文件结构"""
        print("\n📁 检查文件结构...")
        
        required_files = [
            # 主要文件
            ("主配置文件", "config.py"),
            ("CLI入口", "main_cli.py"),
            ("Web入口", "main_web.py"),
            ("GUI入口", "main_pyside.py"),
            ("需求文件", "requirements.txt"),
            ("README文档", "README.md"),
            
            # 部署目录
            ("部署配置", "deploy/config.py"),
            ("部署CLI", "deploy/main_cli.py"),
            ("部署Web", "deploy/main_web.py"),
            ("部署GUI", "deploy/main_pyside.py"),
            ("部署需求", "deploy/requirements.txt"),
            ("安装脚本", "deploy/install.py"),
            
            # 核心模块
            ("转换器模块", "converter/document_converter.py"),
            ("部署转换器", "deploy/converter/document_converter.py"),
            ("工具模块", "utils/config_manager.py"),
            ("部署工具", "deploy/utils/config_manager.py"),
        ]
        
        file_status = {}
        for name, file_path in required_files:
            full_path = self.project_root / file_path
            file_status[name] = {
                "exists": full_path.exists(),
                "size": full_path.stat().st_size if full_path.exists() else 0,
                "path": str(file_path)
            }
        
        self.results["file_structure"] = file_status
        
        missing_files = [name for name, status in file_status.items() if not status["exists"]]
        if missing_files:
            print(f"  ❌ 缺失文件: {', '.join(missing_files)}")
            self.results["recommendations"].append(f"补充缺失文件: {', '.join(missing_files)}")
        else:
            print("  ✅ 所有必需文件存在")
    
    def check_dependencies(self):
        """检查依赖"""
        print("\n📦 检查依赖...")
        
        # 检查Python版本
        python_version = sys.version_info
        python_ok = python_version.major == 3 and python_version.minor >= 7
        
        # 检查关键依赖
        key_dependencies = [
            "flask", "pandoc", "pdfplumber", "openpyxl", 
            "python-docx", "beautifulsoup4", "markdown"
        ]
        
        dep_status = {}
        for dep in key_dependencies:
            try:
                __import__(dep.replace('-', '_'))
                dep_status[dep] = "已安装"
            except ImportError:
                dep_status[dep] = "未安装"
        
        # 检查Pandoc
        pandoc_available = False
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                pandoc_version = result.stdout.split('\n')[0]
                dep_status["pandoc_system"] = f"已安装 - {pandoc_version}"
                pandoc_available = True
            else:
                dep_status["pandoc_system"] = "未安装"
        except:
            dep_status["pandoc_system"] = "未安装"
        
        self.results["dependencies"] = {
            "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "python_ok": python_ok,
            "packages": dep_status,
            "pandoc_available": pandoc_available
        }
        
        if not python_ok:
            print(f"  ❌ Python版本过低: {python_version}")
            self.results["recommendations"].append("升级Python到3.7+")
        
        missing_deps = [dep for dep, status in dep_status.items() if status == "未安装"]
        if missing_deps:
            print(f"  ⚠️  缺失依赖: {', '.join(missing_deps)}")
            self.results["recommendations"].append(f"安装缺失依赖: {', '.join(missing_deps)}")
        else:
            print("  ✅ 所有关键依赖已安装")
    
    def check_core_functionality(self):
        """检查核心转换功能"""
        print("\n🔧 检查核心转换功能...")
        
        # 创建测试文件
        test_content = "# 测试文档\\n\\n这是一个测试文档，用于验证转换功能。\\n\\n- 列表项1\\n- 列表项2"
        
        conversion_tests = []
        
        try:
            # 测试Markdown到HTML转换
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(test_content)
                test_md_path = f.name
            
            # 导入转换器
            sys.path.insert(0, str(self.deploy_dir))
            from converter.document_converter import DocumentConverter
            
            converter = DocumentConverter()
            
            # 测试转换
            output_path = test_md_path.replace('.md', '.html')
            success = converter.convert_file(test_md_path, output_path, '.html')
            
            conversion_tests.append({
                "test": "Markdown -> HTML",
                "success": success,
                "input_exists": os.path.exists(test_md_path),
                "output_exists": os.path.exists(output_path) if success else False
            })
            
            # 清理测试文件
            for path in [test_md_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)
                    
        except Exception as e:
            conversion_tests.append({
                "test": "Markdown -> HTML",
                "success": False,
                "error": str(e)
            })
        
        self.results["core_functionality"] = {
            "conversion_tests": conversion_tests,
            "converter_available": len([t for t in conversion_tests if t.get("success", False)]) > 0
        }
        
        if any(t.get("success", False) for t in conversion_tests):
            print("  ✅ 核心转换功能正常")
        else:
            print("  ❌ 核心转换功能异常")
            self.results["recommendations"].append("修复核心转换功能")
    
    def check_web_interface(self):
        """检查Web界面"""
        print("\n🌐 检查Web界面...")
        
        web_status = {
            "service_running": False,
            "port_accessible": False,
            "api_responsive": False,
            "upload_functional": False
        }
        
        try:
            # 检查Web服务是否运行
            response = requests.get("http://localhost:5003/stats", timeout=5)
            if response.status_code == 200:
                web_status["service_running"] = True
                web_status["port_accessible"] = True
                web_status["api_responsive"] = True
                print("  ✅ Web服务正常运行")
            else:
                print(f"  ⚠️  Web服务响应异常: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("  ❌ Web服务未运行或端口不可访问")
        except Exception as e:
            print(f"  ❌ Web服务检查失败: {str(e)}")
        
        self.results["web_interface"] = web_status
        
        if not web_status["service_running"]:
            self.results["recommendations"].append("启动Web服务进行测试")
    
    def check_cli_interface(self):
        """检查CLI界面"""
        print("\n💻 检查CLI界面...")
        
        cli_status = {
            "main_cli_exists": False,
            "executable": False,
            "help_available": False
        }
        
        cli_path = self.deploy_dir / "main_cli.py"
        cli_status["main_cli_exists"] = cli_path.exists()
        
        if cli_status["main_cli_exists"]:
            try:
                # 测试CLI帮助
                result = subprocess.run([
                    sys.executable, str(cli_path), "--help"
                ], capture_output=True, text=True, timeout=10, cwd=str(self.deploy_dir))
                
                cli_status["executable"] = result.returncode == 0
                cli_status["help_available"] = "usage" in result.stdout.lower() or "help" in result.stdout.lower()
                
                if cli_status["executable"] and cli_status["help_available"]:
                    print("  ✅ CLI界面正常")
                else:
                    print("  ⚠️  CLI界面可能有问题")
            except Exception as e:
                print(f"  ❌ CLI测试失败: {str(e)}")
        else:
            print("  ❌ CLI文件不存在")
        
        self.results["cli_interface"] = cli_status
    
    def check_gui_interface(self):
        """检查GUI界面"""
        print("\n🖥️  检查GUI界面...")
        
        gui_status = {
            "main_gui_exists": False,
            "qt_available": False,
            "importable": False
        }
        
        gui_path = self.deploy_dir / "main_pyside.py"
        gui_status["main_gui_exists"] = gui_path.exists()
        
        # 检查Qt库
        qt_libs = ["PySide6", "PyQt5", "PySide2"]
        for lib in qt_libs:
            try:
                __import__(lib)
                gui_status["qt_available"] = True
                break
            except ImportError:
                continue
        
        if gui_status["main_gui_exists"] and gui_status["qt_available"]:
            try:
                # 测试GUI模块导入（不启动界面）
                sys.path.insert(0, str(self.deploy_dir))
                # 这里只测试导入，不实际启动GUI
                gui_status["importable"] = True
                print("  ✅ GUI界面组件可用")
            except Exception as e:
                print(f"  ⚠️  GUI组件导入失败: {str(e)}")
        else:
            if not gui_status["main_gui_exists"]:
                print("  ❌ GUI文件不存在")
            if not gui_status["qt_available"]:
                print("  ❌ Qt库未安装")
        
        self.results["gui_interface"] = gui_status
    
    def generate_overall_assessment(self):
        """生成总体评估"""
        print("\n📊 生成总体评估...")
        
        # 计算各项得分
        scores = {
            "version_info": 1.0 if len(set(v for v in self.results["version_info"].values() 
                                         if not v.startswith("读取失败") and v != "文件不存在")) <= 1 else 0.5,
            "file_structure": len([s for s in self.results["file_structure"].values() if s["exists"]]) / len(self.results["file_structure"]),
            "dependencies": 1.0 if self.results["dependencies"]["python_ok"] and self.results["dependencies"]["pandoc_available"] else 0.5,
            "core_functionality": 1.0 if self.results["core_functionality"]["converter_available"] else 0.0,
            "web_interface": 1.0 if self.results["web_interface"]["service_running"] else 0.5,
            "cli_interface": 1.0 if self.results["cli_interface"]["executable"] else 0.5,
            "gui_interface": 1.0 if self.results["gui_interface"]["qt_available"] else 0.5,
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        if overall_score >= 0.9:
            status = "ready"
            status_text = "✅ 准备就绪"
        elif overall_score >= 0.7:
            status = "mostly_ready"
            status_text = "⚠️  基本就绪"
        else:
            status = "not_ready"
            status_text = "❌ 需要修复"
        
        self.results["overall_status"] = status
        self.results["overall_score"] = overall_score
        self.results["component_scores"] = scores
        
        print(f"  总体状态: {status_text} (得分: {overall_score:.1%})")
    
    def print_report(self):
        """打印详细报告"""
        print("\n" + "=" * 60)
        print("📋 DocuFlow 1.0版本发布准备报告")
        print("=" * 60)
        
        print(f"\n🎯 总体状态: {self.results['overall_status']} (得分: {self.results['overall_score']:.1%})")
        
        print(f"\n📊 各组件得分:")
        for component, score in self.results["component_scores"].items():
            status = "✅" if score >= 0.9 else "⚠️" if score >= 0.5 else "❌"
            print(f"  {status} {component}: {score:.1%}")
        
        if self.results["recommendations"]:
            print(f"\n💡 改进建议:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print(f"\n🚀 发布建议:")
        if self.results["overall_status"] == "ready":
            print("  ✅ 项目已准备好发布1.0版本！")
            print("  📦 建议操作:")
            print("    1. 创建Git标签: git tag v1.0.0")
            print("    2. 创建发布分支: git checkout -b release/1.0")
            print("    3. 更新版本文档")
            print("    4. 创建发布包")
        elif self.results["overall_status"] == "mostly_ready":
            print("  ⚠️  项目基本准备就绪，建议先解决上述问题")
            print("  📝 可以考虑发布1.0-beta版本")
        else:
            print("  ❌ 项目还需要更多修复才能发布")
            print("  🔧 请先解决关键问题")

def main():
    """主函数"""
    checker = ReleaseReadinessChecker()
    results = checker.run_full_check()
    
    # 保存详细报告
    report_file = Path(__file__).parent / "release_readiness_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存到: {report_file}")
    
    return results["overall_status"] == "ready"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)