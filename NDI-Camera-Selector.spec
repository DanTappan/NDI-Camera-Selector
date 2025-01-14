# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\dan\\PycharmProjects\\NDI-Camera-Selector\\ndiselector.py'],
    pathex=[],
    binaries=[],
    datas=[('NDI-Camera-Selector.png', '.'), ('NDI-Camera-Selector.ico', '.')],
    hiddenimports=[],
    hookspath=['.'],
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
    name='NDI-Camera-Selector',
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
    version='C:\\Users\\dan\\PycharmProjects\\NDI-Camera-Selector\\version_info.rs',
    icon=['NDI-Camera-Selector.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NDI-Camera-Selector',
)
