#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 统一启动器
解决所有GUI启动问题的终极方案
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List

class DocuFlowLauncher:
    """DocuFlow 统一启动器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.venv_path = self.project_root / "venv"
        self.python_exe = self._get_python_executable()
        
    def _get_python_executable(self) -> str:
        """获取Python可执行文件路径"""
        # 优先使用虚拟环境中的Python
        if self.venv_path.exists():
            if sys.platform == "win32":
                venv_python = self.venv_path / "Scripts" / "python.exe"
            else:
                venv_python = self.venv_path / "bin" / "python"
            
            if venv_python.exists():
                return str(venv_python)
        
        # 回退到系统Python
        return sys.executable
    
    def _setup_environment(self):
        """设置环境变量"""
        # 设置Python路径
        os.environ['PYTHONPATH'] = str(self.project_root)
        
        # 设置Qt环境变量
        if self.venv_path.exists():
            # 查找Qt插件路径
            possible_paths = [
                self.venv_path / "lib" / "python3.13" / "site-packages" / "PySide6" / "Qt" / "plugins",
                self.venv_path / "lib" / "python3.12" / "site-packages" / "PySide6" / "Qt" / "plugins",
                self.venv_path / "lib" / "python3.11" / "site-packages" / "PySide6" / "Qt" / "plugins",
                self.venv_path / "lib" / "python3.10" / "site-packages" / "PySide6" / "Qt" / "plugins",
                self.venv_path / "lib" / "python3.9" / "site-packages" / "PySide6" / "Qt" / "plugins",
            ]
            
            for path in possible_paths:
                if path.exists():
                    os.environ['QT_PLUGIN_PATH'] = str(path)
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(path)
                    break
        
        # 设置其他Qt环境变量
        os.environ['QT_X11_NO_MITSHM'] = '1'
        if sys.platform == "darwin":  # macOS
            os.environ['QT_QPA_PLATFORM'] = 'cocoa'
        elif sys.platform == "linux":
            os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    def _check_dependencies(self) -> bool:
        """检查依赖是否安装"""
        try:
            result = subprocess.run(
                [self.python_exe, "-c", "import PySide6; print('PySide6 available')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _install_dependencies(self) -> bool:
        """安装依赖"""
        print("📦 正在安装GUI依赖...")
        try:
            # 升级pip
            subprocess.run([self.python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
            
            # 安装PySide6
            subprocess.run([self.python_exe, "-m", "pip", "install", "PySide6>=6.4.0"], check=True)
            
            # 安装其他依赖
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                subprocess.run([self.python_exe, "-m", "pip", "install", "-r", str(requirements_file)], check=True)
            
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    
    def launch_gui(self) -> int:
        """启动GUI版本"""
        print("🚀 启动DocuFlow GUI版本...")
        
        # 设置环境
        self._setup_environment()
        
        # 检查依赖
        if not self._check_dependencies():
            print("⚠️ GUI依赖未安装")
            if input("是否自动安装依赖? (y/n): ").lower() == 'y':
                if not self._install_dependencies():
                    return 1
            else:
                print("❌ 无法启动GUI，请手动安装依赖")
                return 1
        
        # 尝试启动GUI
        gui_scripts = [
            "main_pyside.py",
            "main.py"
        ]
        
        for script in gui_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                try:
                    print(f"📱 使用 {script} 启动GUI...")
                    result = subprocess.run(
                        [self.python_exe, str(script_path)],
                        cwd=str(self.project_root)
                    )
                    return result.returncode
                except KeyboardInterrupt:
                    print("\n👋 用户中断")
                    return 0
                except Exception as e:
                    print(f"❌ 启动 {script} 失败: {e}")
                    continue
        
        print("❌ 找不到可用的GUI脚本")
        return 1
    
    def launch_cli(self, args: List[str]) -> int:
        """启动命令行版本"""
        print("💻 启动DocuFlow 命令行版本...")
        
        # 设置环境
        self._setup_environment()
        
        # 尝试使用增强版启动器
        enhanced_script = self.project_root / "run_enhanced.py"
        if enhanced_script.exists():
            try:
                cmd = [self.python_exe, str(enhanced_script)] + args
                result = subprocess.run(cmd, cwd=str(self.project_root))
                return result.returncode
            except Exception as e:
                print(f"❌ 增强版启动器失败: {e}")
        
        # 回退到基础CLI
        cli_script = self.project_root / "main_cli.py"
        if cli_script.exists():
            try:
                cmd = [self.python_exe, str(cli_script)] + args
                result = subprocess.run(cmd, cwd=str(self.project_root))
                return result.returncode
            except Exception as e:
                print(f"❌ CLI启动器失败: {e}")
        
        print("❌ 找不到可用的CLI脚本")
        return 1
    
    def launch_web(self) -> int:
        """启动Web版本"""
        print("🌐 启动DocuFlow Web版本...")
        
        # 设置环境
        self._setup_environment()
        
        web_scripts = [
            "main_web.py",
            "launch_web_fixed.py"
        ]
        
        for script in web_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                try:
                    print(f"🌐 使用 {script} 启动Web服务...")
                    result = subprocess.run(
                        [self.python_exe, str(script_path)],
                        cwd=str(self.project_root)
                    )
                    return result.returncode
                except KeyboardInterrupt:
                    print("\n👋 用户中断")
                    return 0
                except Exception as e:
                    print(f"❌ 启动 {script} 失败: {e}")
                    continue
        
        print("❌ 找不到可用的Web脚本")
        return 1
    
    def launch_docker_gui(self) -> int:
        """启动Docker GUI版本"""
        print("🐳 启动DocuFlow Docker GUI版本...")
        
        docker_script = self.project_root / "run_gui_docker.sh"
        if docker_script.exists():
            try:
                result = subprocess.run(["bash", str(docker_script)], cwd=str(self.project_root))
                return result.returncode
            except Exception as e:
                print(f"❌ Docker GUI启动失败: {e}")
                return 1
        else:
            print("❌ Docker GUI脚本不存在")
            return 1
    
    def show_status(self):
        """显示系统状态"""
        print("📊 DocuFlow 系统状态")
        print("=" * 40)
        
        # Python信息
        print(f"Python路径: {self.python_exe}")
        print(f"项目路径: {self.project_root}")
        print(f"虚拟环境: {'存在' if self.venv_path.exists() else '不存在'}")
        
        # 依赖检查
        print("\n📦 依赖状态:")
        dependencies = {
            "PySide6": "import PySide6",
            "PyYAML": "import yaml",
            "pdfplumber": "import pdfplumber",
            "python-docx": "import docx",
        }
        
        for name, import_cmd in dependencies.items():
            try:
                result = subprocess.run(
                    [self.python_exe, "-c", import_cmd],
                    capture_output=True,
                    timeout=5
                )
                status = "✅" if result.returncode == 0 else "❌"
                print(f"  {status} {name}")
            except Exception:
                print(f"  ❌ {name}")
        
        # 可用脚本
        print("\n📄 可用脚本:")
        scripts = [
            "main_pyside.py",
            "main.py",
            "run_enhanced.py",
            "main_cli.py",
            "main_web.py",
            "run_gui_docker.sh"
        ]
        
        for script in scripts:
            script_path = self.project_root / script
            status = "✅" if script_path.exists() else "❌"
            print(f"  {status} {script}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="DocuFlow 统一启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s gui                    # 启动GUI版本
  %(prog)s cli input.md           # 命令行转换文件
  %(prog)s web                    # 启动Web版本
  %(prog)s docker-gui             # 启动Docker GUI版本
  %(prog)s status                 # 显示系统状态
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["gui", "cli", "web", "docker-gui", "status"],
        help="启动模式"
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        help="传递给CLI模式的参数"
    )
    
    args = parser.parse_args()
    
    launcher = DocuFlowLauncher()
    
    try:
        if args.mode == "gui":
            return launcher.launch_gui()
        elif args.mode == "cli":
            return launcher.launch_cli(args.args)
        elif args.mode == "web":
            return launcher.launch_web()
        elif args.mode == "docker-gui":
            return launcher.launch_docker_gui()
        elif args.mode == "status":
            launcher.show_status()
            return 0
    except KeyboardInterrupt:
        print("\n👋 用户中断")
        return 0
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())