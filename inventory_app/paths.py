"""Resolve writable app data dir (dev vs PyInstaller frozen EXE)."""

import os
import sys


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def bundle_dir() -> str:
    """Read-only PyInstaller extract dir (_MEIPASS), or package root in dev."""
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def app_data_dir() -> str:
    """Writable folder beside the EXE (or project inventory_app/ in dev)."""
    if is_frozen():
        root = os.path.dirname(os.path.abspath(sys.executable))
    else:
        root = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(root, exist_ok=True)
    return root
