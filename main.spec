# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Assets/polytes.png', 'Assets'),
        ('Assets/polytes.ico', 'Assets'),
        ('Fonts', 'Fonts'),
        ('Tools/rcedit-x64.exe', 'Tools'),
    ],
    hiddenimports=[
        'CreatorWindow.creator_window',
        'CreatorWindow.preview_widget',
        'CreatorWindow.widgets',
        'CreatorWindow.color_picker',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='Polytes',
    icon='Assets/polytes.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)