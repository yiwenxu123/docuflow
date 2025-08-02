import PyInstaller.__main__
import os
from pathlib import Path

print("🚀 开始打包 DocuFlow 应用...")

# 检查必要文件是否存在
required_files = ['main_pyside.py', 'converter', 'ui', 'utils']
missing_files = []

for file in required_files:
    if not Path(file).exists():
        missing_files.append(file)

if missing_files:
    print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
    exit(1)

print("✅ 所有必要文件检查完成")

# 打包配置
args = [
    'main_pyside.py',
    '--name=DocuFlow',
    '--windowed',  # 不显示控制台
    '--onedir',    # 单目录模式
    '--add-data=converter:converter',
    '--add-data=ui:ui',
    '--add-data=utils:utils',
    '--clean',
    '--noconfirm'
]

# 可选文件检查
optional_dirs = ['config', 'templates', 'static']
for dir_name in optional_dirs:
    if Path(dir_name).exists():
        args.append(f'--add-data={dir_name}:{dir_name}')
        print(f"✅ 添加目录: {dir_name}")

# 检查图标文件
icon_files = ['icon.icns', 'icon.ico', 'assets/icon.icns']
for icon in icon_files:
    if Path(icon).exists():
        args.append(f'--icon={icon}')
        print(f"✅ 使用图标: {icon}")
        break

print("📦 开始打包...")
PyInstaller.__main__.run(args)
print("🎉 打包完成！应用位于 dist/DocuFlow/ 目录")
