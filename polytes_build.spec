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

pyz_main = PYZ(a_main.pure, a_main.zipped_data, cipher=block_cipher)
pyz_ghost = PYZ(a_ghost.pure, a_ghost.zipped_data, cipher=block_cipher)

exe_main = EXE(
    pyz_main,
    a_main.scripts,
    [],
    exclude_binaries=True,
    name='Polytes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,  # icone customizado entra aqui depois
)

exe_ghost = EXE(
    pyz_ghost,
    a_ghost.scripts,
    [],
    exclude_binaries=True,
    name='stickman_ghost_process',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,  # icone customizado entra aqui depois
)

coll = COLLECT(
    exe_main,
    a_main.binaries,
    a_main.zipfiles,
    a_main.datas,
    exe_ghost,
    a_ghost.binaries,
    a_ghost.zipfiles,
    a_ghost.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Polytes',
)
