# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置：DocuFlow GUI（.app）
用法: ./venv/bin/pyinstaller DocuFlow.spec
"""

import os

block_cipher = None

a = Analysis(
    ['main_pyside.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'pypdf',
        'pdfplumber',
        'openpyxl',
        'pandas',
        'pandas._libs.tslibs.timedeltas',
        'numpy',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['flask', 'werkzeug', 'matplotlib', 'reportlab'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DocuFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DocuFlow',
)

app = BUNDLE(
    coll,
    name='DocuFlow.app',
    icon=None,
    bundle_identifier='com.docuflow.app',
    info_plist={
        'CFBundleName': 'DocuFlow',
        'CFBundleDisplayName': 'DocuFlow 文档转换器',
        'CFBundleShortVersionString': '1.2.0',
        'CFBundleVersion': '1.2.0',
        'NSHighResolutionCapable': True,
    },
)
