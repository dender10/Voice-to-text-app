# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for Wispr Flow."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / 'config' / 'default_config.yaml'), 'config'),
    ],
    hiddenimports=[
        'sounddevice',
        'numpy',
        'scipy',
        'scipy.io',
        'scipy.io.wavfile',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
        'pyperclip',
        'openai',
        'yaml',
        'tkinter',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='WisprFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'icon.ico') if (project_root / 'assets' / 'icon.ico').exists() else None,
)
