#coding: utf-8
"""
putils.py - Path/process utilities for NekoDL
"""
import os
import sys
import subprocess
import platform

# ── DIR ───────────────────────────────────────────────────────────────────────
# Root directory of the application
DIR = os.path.dirname(os.path.abspath(__file__))


def open_folder(path: str) -> None:
    """Open *path* in the system file explorer."""
    path = os.path.realpath(path)
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


def open_file(path: str) -> None:
    """Open *path* with the default application."""
    path = os.path.realpath(path)
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


def which(name: str) -> str | None:
    """Return full path of *name* executable, or None."""
    import shutil
    return shutil.which(name)
