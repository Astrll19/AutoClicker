# -*- mode: python ; coding: utf-8 -*-
# AstryxlDesk.spec — PyInstaller build config

block_cipher = None

a = Analysis(
    ['AstryxlDesk.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('icon.png', '.'),
    ],
    hiddenimports=[
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib','numpy','scipy','pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Auto Clicker by Astryxl',
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
    icon='icon.ico',
    version_file=None,
)
