# InventoryManager.spec
# Generated for PyInstaller — used by the GitHub Actions build.
# Run locally with: pyinstaller InventoryManager.spec

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=[
        ('inventory_app', 'inventory_app'),
    ],
    hiddenimports=[
        'inventory_app',
        'inventory_app.db',
        'inventory_app.auth',
        'inventory_app.ui',
        'inventory_app.utils',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.postgresql',
        'PySide6.QtSvg',
        'PySide6.QtXml',
        'PySide6.QtPrintSupport',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'passlib',
        'passlib.handlers.sha2_crypt',
        'email.mime.multipart',
        'email.mime.base',
        'email.mime.text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest', 'tkinter'],
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
    name='InventoryManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',   # uncomment if you add an icon
)
