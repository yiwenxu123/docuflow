#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 优化部署脚本
为用户提供最佳的轻量化部署方案
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import json

class DocuFlowDeployer:
    """DocuFlow 优化部署器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.deploy_dir = self.project_root / "deploy"
        self.app_name = "DocuFlow"
        
    def analyze_current_size(self):
        """分析当前项目大小"""
        print("📊 分析项目大小...")
        
        # 计算各目录大小
        sizes = {}
        total_size = 0
        
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                size = self._get_dir_size(item)
                sizes[item.name] = size
                total_size += size
        
        # 显示分析结果
        print(f"\n📁 当前项目大小分析 (总计: {self._format_size(total_size)})")
        print("=" * 50)
        
        # 按大小排序显示
        for name, size in sorted(sizes.items(), key=lambda x: x[1], reverse=True):
            if size > 1024 * 1024:  # 只显示大于1MB的目录
                print(f"  {name:<20} {self._format_size(size)}")
        
        return total_size, sizes
    
    def create_lightweight_package(self):
        """创建轻量化应用包"""
        print("\n🚀 创建轻量化应用包...")
        
        # 清理旧的部署目录
        if self.deploy_dir.exists():
            shutil.rmtree(self.deploy_dir)
        self.deploy_dir.mkdir()
        
        # 核心文件列表
        core_files = [
            "docuflow",
            "docuflow_launcher.py",
            "main_web.py",
            "main_pyside.py",
            "main_cli.py",
            "requirements.txt",
            "config.py"
        ]
        
        # 核心目录列表
        core_dirs = [
            "converter",
            "ui", 
            "utils",
            "config",
            "templates",
            "static"
        ]
        
        # 复制核心文件
        print("📋 复制核心文件...")
        for file_name in core_files:
            src = self.project_root / file_name
            if src.exists():
                dst = self.deploy_dir / file_name
                if src.is_file():
                    shutil.copy2(src, dst)
                print(f"  ✅ {file_name}")
        
        # 复制核心目录
        print("📁 复制核心目录...")
        for dir_name in core_dirs:
            src = self.project_root / dir_name
            if src.exists():
                dst = self.deploy_dir / dir_name
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                print(f"  ✅ {dir_name}")
        
        # 创建启动脚本
        self._create_startup_scripts()
        
        # 创建安装脚本
        self._create_install_script()
        
        # 计算轻量化包大小
        package_size = self._get_dir_size(self.deploy_dir)
        print(f"\n🎉 轻量化包创建完成！")
        print(f"📦 包大小: {self._format_size(package_size)}")
        print(f"📁 位置: {self.deploy_dir}")
        
        return package_size
    
    def _create_startup_scripts(self):
        """创建启动脚本"""
        print("📝 创建启动脚本...")
        
        # macOS/Linux 启动脚本
        startup_script = self.deploy_dir / "start_docuflow.sh"
        startup_content = '''#!/bin/bash
# DocuFlow 快速启动脚本

cd "$(dirname "$0")"

echo "🚀 启动 DocuFlow..."

# 检查Python环境
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 检查依赖
echo "🔍 检查依赖..."
$PYTHON -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || {
    echo "❌ Python版本过低，需要3.8+"
    exit 1
}

# 安装依赖（如果需要）
if [ ! -f ".deps_installed" ]; then
    echo "📦 首次运行，安装依赖..."
    $PYTHON -m pip install -r requirements.txt --user --quiet
    touch .deps_installed
    echo "✅ 依赖安装完成"
fi

# 启动应用
case "${1:-web}" in
    "gui")
        echo "🖥️  启动GUI版本..."
        $PYTHON main_pyside.py
        ;;
    "web")
        echo "🌐 启动Web版本..."
        echo "📱 访问地址: http://localhost:5003"
        $PYTHON main_web.py
        ;;
    "cli")
        echo "💻 启动命令行版本..."
        shift
        $PYTHON main_cli.py "$@"
        ;;
    *)
        echo "用法: $0 [gui|web|cli] [参数...]"
        echo "  gui - 图形界面"
        echo "  web - 网页界面"
        echo "  cli - 命令行"
        ;;
esac
'''
        
        with open(startup_script, 'w', encoding='utf-8') as f:
            f.write(startup_content)
        
        # 设置执行权限
        os.chmod(startup_script, 0o755)
        
        # Windows 启动脚本
        windows_script = self.deploy_dir / "start_docuflow.bat"
        windows_content = '''@echo off
REM DocuFlow Windows 启动脚本

cd /d "%~dp0"

echo 🚀 启动 DocuFlow...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖（如果需要）
if not exist ".deps_installed" (
    echo 📦 首次运行，安装依赖...
    python -m pip install -r requirements.txt --user --quiet
    echo. > .deps_installed
    echo ✅ 依赖安装完成
)

REM 启动应用
set mode=%1
if "%mode%"=="" set mode=web

if "%mode%"=="gui" (
    echo 🖥️  启动GUI版本...
    python main_pyside.py
) else if "%mode%"=="web" (
    echo 🌐 启动Web版本...
    echo 📱 访问地址: http://localhost:5003
    python main_web.py
) else if "%mode%"=="cli" (
    echo 💻 启动命令行版本...
    shift
    python main_cli.py %*
) else (
    echo 用法: %0 [gui^|web^|cli] [参数...]
    echo   gui - 图形界面
    echo   web - 网页界面  
    echo   cli - 命令行
)

pause
'''
        
        with open(windows_script, 'w', encoding='utf-8') as f:
            f.write(windows_content)
    
    def _create_install_script(self):
        """创建安装脚本"""
        print("📝 创建安装脚本...")
        
        install_script = self.deploy_dir / "install.py"
        install_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 一键安装脚本
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    print("🚀 DocuFlow 一键安装")
    print("=" * 40)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要3.8+")
        print(f"当前版本: {sys.version}")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    print(f"✅ 操作系统: {platform.system()} {platform.release()}")
    
    # 安装依赖
    print("\\n📦 安装依赖包...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements.txt", "--user", "--upgrade"
        ], check=True)
        print("✅ 依赖安装完成")
    except subprocess.CalledProcessError:
        print("❌ 依赖安装失败")
        return False
    
    # 创建桌面快捷方式（可选）
    create_shortcuts()
    
    print("\\n🎉 安装完成！")
    print("\\n🚀 启动方式:")
    print("  ./start_docuflow.sh web    # Web界面")
    print("  ./start_docuflow.sh gui    # 图形界面")
    print("  ./start_docuflow.sh cli    # 命令行")
    
    return True

def create_shortcuts():
    """创建桌面快捷方式"""
    try:
        current_dir = Path(__file__).parent.absolute()
        
        if platform.system() == "Darwin":  # macOS
            # 创建 .command 文件
            command_file = Path.home() / "Desktop" / "DocuFlow.command"
            with open(command_file, 'w') as f:
                f.write(f'#!/bin/bash\\ncd "{current_dir}"\\n./start_docuflow.sh web\\n')
            os.chmod(command_file, 0o755)
            print("✅ 已创建桌面快捷方式")
            
        elif platform.system() == "Windows":
            # 创建 .bat 文件
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "DocuFlow.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = str(current_dir / "start_docuflow.bat")
            shortcut.WorkingDirectory = str(current_dir)
            shortcut.save()
            print("✅ 已创建桌面快捷方式")
            
    except Exception as e:
        print(f"⚠️  快捷方式创建失败: {e}")

if __name__ == "__main__":
    main()
'''
        
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write(install_content)
        
        os.chmod(install_script, 0o755)
    
    def _get_dir_size(self, path):
        """计算目录大小"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total += os.path.getsize(filepath)
        except (OSError, IOError):
            pass
        return total
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def create_readme(self):
        """创建使用说明"""
        readme_content = '''# DocuFlow 轻量化版本

## 🚀 快速开始

### 1. 一键安装
```bash
python install.py
```

### 2. 启动应用

#### macOS/Linux:
```bash
# Web界面（推荐）
./start_docuflow.sh web

# 图形界面
./start_docuflow.sh gui

# 命令行
./start_docuflow.sh cli input.docx output.md
```

#### Windows:
```cmd
# Web界面（推荐）
start_docuflow.bat web

# 图形界面
start_docuflow.bat gui

# 命令行
start_docuflow.bat cli input.docx output.md
```

## 📱 访问地址

Web界面: http://localhost:5003

## 🔧 系统要求

- Python 3.8+
- 50MB 可用空间
- 网络连接（首次安装依赖）

## 📋 支持格式

- Word (.docx) ↔ Markdown
- HTML (.html, .htm) ↔ Markdown, DOCX
- PDF (.pdf) → Markdown
- Excel (.xlsx, .xls) → Markdown

## 🆘 故障排除

### 依赖问题
```bash
pip install -r requirements.txt --user --upgrade
```

### 权限问题
```bash
chmod +x start_docuflow.sh
```

### 端口占用
修改 main_web.py 中的端口号，或关闭占用端口的程序。
'''
        
        readme_path = self.deploy_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def deploy(self):
        """执行完整部署"""
        print("🎯 DocuFlow 优化部署开始")
        print("=" * 50)
        
        # 分析当前大小
        original_size, _ = self.analyze_current_size()
        
        # 创建轻量化包
        package_size = self.create_lightweight_package()
        
        # 创建说明文档
        self.create_readme()
        
        # 显示优化结果
        reduction = original_size - package_size
        reduction_percent = (reduction / original_size) * 100
        
        print(f"\n🎉 部署完成！")
        print("=" * 50)
        print(f"📊 优化结果:")
        print(f"  原始大小: {self._format_size(original_size)}")
        print(f"  优化后:   {self._format_size(package_size)}")
        print(f"  节省:     {self._format_size(reduction)} ({reduction_percent:.1f}%)")
        print(f"\n📁 部署包位置: {self.deploy_dir}")
        print(f"\n🚀 快速启动:")
        print(f"  cd {self.deploy_dir}")
        print(f"  python install.py")
        print(f"  ./start_docuflow.sh web")

if __name__ == "__main__":
    deployer = DocuFlowDeployer()
    deployer.deploy()