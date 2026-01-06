# -*- mode: python ; coding: utf-8 -*-
"""
UceAsistan Backend PyInstaller Spec File
Creates a single executable for the Python backend
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the backend directory
backend_dir = os.path.dirname(os.path.abspath(SPEC))

# Collect all submodules for complex packages
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'websockets',
    'websockets.legacy',
    'websockets.legacy.server',
    'engineio',
    'socketio',
    'aiohttp',
    'pandas',
    'numpy',
    'ta',
    'sklearn',
    'sklearn.ensemble',
    'sklearn.preprocessing',
    'openai',
    'anthropic',
    'google.generativeai',
    'MetaTrader5',
    'sqlite3',
    'json',
    'asyncio',
    'threading',
]

# Data files to include
datas = [
    ('*.json', '.'),
    ('*.txt', '.'),
]

a = Analysis(
    ['start_server.py'],
    pathex=[backend_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'IPython',
        'jupyter',
        'notebook',
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='uceasistan_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging, can change to False later
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
