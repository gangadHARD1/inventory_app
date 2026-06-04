# PyInstaller spec for InventoryManager (Windows EXE).
# CI: pyinstaller --clean --noconfirm InventoryManager.spec
# Local: same command from repo root.

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
ROOT = Path(SPECPATH).resolve()
ICON = ROOT / "assets" / "icon.ico"

# Lazy imports across inventory_app.ui.* — collect entire package tree.
hiddenimports = collect_submodules("inventory_app")
hiddenimports += [
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.sql.default_comparator",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.utils",
    "openpyxl.cell",
    "openpyxl.workbook",
]

datas = []
email_cfg = ROOT / "inventory_app" / "email_config.json"
if email_cfg.is_file():
    datas.append((str(email_cfg), "inventory_app"))

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "unittest",
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
    ],
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
    name="InventoryManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if ICON.is_file() else None,
)
