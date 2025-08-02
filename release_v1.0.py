#!/usr/bin/env python3
"""
DocuFlow 1.0版本发布脚本
用于创建稳定的1.0版本发布包
"""

import os
import shutil
import json
import zipfile
import datetime
from pathlib import Path

def create_release_package():
    """创建1.0版本发布包"""
    
    # 获取当前目录
    current_dir = Path.cwd()
    
    # 创建发布目录
    release_dir = current_dir / "releases" / "v1.0.0"
    release_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 开始创建DocuFlow 1.0版本发布包...")
    
    # 1. 复制核心文件到发布目录
    core_files = [
        "config.py",
        "main_cli.py", 
        "main_web.py",
        "main_pyside.py",
        "requirements.txt",
        "README.md",
        "exceptions.py",
        "install.py"
    ]
    
    core_dirs = [
        "converter",
        "utils", 
        "ui",
        "static",
        "templates"
    ]
    
    print("📁 复制核心文件...")
    for file in core_files:
        if (current_dir / file).exists():
            shutil.copy2(current_dir / file, release_dir / file)
            print(f"  ✅ {file}")
    
    print("📁 复制核心目录...")
    for dir_name in core_dirs:
        src_dir = current_dir / dir_name
        if src_dir.exists():
            dst_dir = release_dir / dir_name
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)
            print(f"  ✅ {dir_name}/")
    
    # 2. 创建版本信息文件
    version_info = {
        "version": "1.0.0",
        "release_date": datetime.datetime.now().isoformat(),
        "description": "DocuFlow 1.0 稳定版本",
        "features": [
            "支持多种文档格式转换",
            "Web界面操作",
            "命令行工具",
            "图形界面",
            "批量转换功能",
            "自定义转换参数",
            "下载文件名修复"
        ],
        "supported_formats": {
            "input": [".pdf", ".docx", ".doc", ".txt", ".md", ".html", ".xlsx", ".xls", ".pptx", ".ppt"],
            "output": [".pdf", ".docx", ".html", ".txt", ".md", ".xlsx", ".pptx"]
        },
        "requirements": {
            "python": ">=3.7",
            "system": "Windows/macOS/Linux"
        }
    }
    
    with open(release_dir / "VERSION.json", "w", encoding="utf-8") as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)
    
    print("📄 创建版本信息文件...")
    
    # 3. 创建安装说明
    install_guide = """# DocuFlow 1.0 安装指南

## 系统要求
- Python 3.7 或更高版本
- 操作系统: Windows/macOS/Linux

## 安装步骤

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 安装系统依赖
- **macOS**: `brew install pandoc`
- **Ubuntu/Debian**: `sudo apt-get install pandoc`
- **Windows**: 从 https://pandoc.org/installing.html 下载安装

### 3. 运行程序

#### Web界面
```bash
python main_web.py
```
然后访问 http://localhost:5003

#### 命令行工具
```bash
python main_cli.py
```

#### 图形界面
```bash
python main_pyside.py
```

## 功能特性
- ✅ 多格式文档转换
- ✅ 批量处理
- ✅ 自定义参数
- ✅ 三种使用方式 (Web/CLI/GUI)
- ✅ 下载文件名自动修正

## 技术支持
如有问题，请查看README.md或提交Issue。
"""
    
    with open(release_dir / "INSTALL.md", "w", encoding="utf-8") as f:
        f.write(install_guide)
    
    print("📖 创建安装指南...")
    
    # 4. 创建发布包压缩文件
    zip_path = current_dir / "releases" / f"DocuFlow-v1.0.0-{datetime.datetime.now().strftime('%Y%m%d')}.zip"
    
    print("📦 创建压缩包...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(release_dir)
                zipf.write(file_path, arc_path)
    
    # 5. 生成发布报告
    release_report = f"""
🎉 DocuFlow 1.0版本发布包创建完成！

📦 发布包信息:
  版本: 1.0.0
  创建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  发布目录: {release_dir}
  压缩包: {zip_path}
  
📁 包含文件:
  - 核心程序文件
  - 配置文件
  - 依赖列表
  - 说明文档
  - 版本信息

🚀 使用方法:
  1. 解压发布包到目标目录
  2. 按照INSTALL.md安装依赖
  3. 运行对应的主程序文件

💡 建议:
  - 将发布包备份到安全位置
  - 为后续开发创建新的分支
  - 在生产环境中使用此稳定版本
"""
    
    print(release_report)
    
    # 保存发布报告
    with open(current_dir / "releases" / "RELEASE_NOTES_v1.0.0.txt", "w", encoding="utf-8") as f:
        f.write(release_report)
    
    return release_dir, zip_path

def create_git_tag():
    """创建Git标签（如果在Git仓库中）"""
    try:
        import subprocess
        
        # 检查是否在Git仓库中
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n🔖 创建Git标签...")
            
            # 添加所有更改
            subprocess.run(['git', 'add', '.'], check=True)
            
            # 提交更改
            subprocess.run(['git', 'commit', '-m', 'Release v1.0.0 - 稳定版本发布'], check=True)
            
            # 创建标签
            subprocess.run(['git', 'tag', '-a', 'v1.0.0', '-m', 'DocuFlow 1.0.0 稳定版本'], check=True)
            
            print("  ✅ Git标签 v1.0.0 创建成功")
            print("  💡 使用 'git push origin v1.0.0' 推送标签到远程仓库")
            
    except (ImportError, subprocess.CalledProcessError, FileNotFoundError):
        print("  ⚠️  Git操作跳过（未安装Git或不在Git仓库中）")

if __name__ == "__main__":
    try:
        release_dir, zip_path = create_release_package()
        create_git_tag()
        
        print(f"\n✨ 发布完成！")
        print(f"📁 发布目录: {release_dir}")
        print(f"📦 压缩包: {zip_path}")
        print(f"\n🎯 下一步建议:")
        print(f"  1. 测试发布包功能")
        print(f"  2. 备份到安全位置") 
        print(f"  3. 为后续开发创建新分支")
        print(f"  4. 在生产环境部署此版本")
        
    except Exception as e:
        print(f"❌ 发布过程中出现错误: {e}")