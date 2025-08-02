# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_pyside.py'],
    pathex=[],
    binaries=[],
    datas=[('converter', 'converter'), ('ui', 'ui'), ('utils', 'utils'), ('config', 'config'), ('templates', 'templates'), ('static', 'static')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
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
    bundle_identifier=None,
)
