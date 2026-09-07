# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a_main = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pywinctl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a_ghost = Analysis(
    ['Simulation/stickman_ghost_process.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a_main.pure + a_ghost.pure,
    a_main.zipped_data + a_ghost.zipped_data,
    cipher=block_cipher,
)

exe_ghost = EXE(
    pyz,
    a_ghost.scripts,
    [],
    exclude_binaries=True,
    name='stickman_ghost_process',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

exe = EXE(
    pyz,
    a_main.scripts,
    [],
    exclude_binaries=True,
    name='Polytes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a_main.binaries,
    a_main.zipfiles,
    a_main.datas,
    exe_ghost,
    a_ghost.binaries,
    a_ghost.zipfiles,
    a_ghost.datas,
    strip=False,
    upx=True,
    name='Polytes',
)
