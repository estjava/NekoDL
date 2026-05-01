#coding: utf-8
"""
constants.py - Global constants and configuration for NekoDL
"""
import os
import sys

# ─── App Info ───────────────────────────────────────────────────────────────
APP_NAME = 'NekoDL'
VERSION  = '1.0.0'

# ─── Paths ───────────────────────────────────────────────────────────────────
ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
SRC_DIR     = os.path.join(ROOT_DIR, 'src')
TRANS_DIR   = os.path.join(ROOT_DIR, 'translation')
IMGS_DIR    = os.path.join(ROOT_DIR, 'imgs')
TEMP_DIR    = os.path.join(ROOT_DIR, '.temp')
SETTINGS_PATH = os.path.join(ROOT_DIR, 'settings.json')

os.makedirs(TEMP_DIR, exist_ok=True)

# ─── Download Settings ───────────────────────────────────────────────────────
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads', APP_NAME)
MAX_PARALLEL         = 4       # max parallel downloads
MAX_CORE             = 4       # max threads per download
DEFAULT_TIMEOUT      = 30      # seconds
MAX_RETRY            = 3

# ─── Video Codec Priority ────────────────────────────────────────────────────
# Lower index = higher priority
CODECS_PRI = [
    'avc1',  # H.264
    'av1',   # AV1
    'vp9',   # VP9
    'vp8',   # VP8
    'hvc1',  # H.265
]

# ─── UI ──────────────────────────────────────────────────────────────────────
opacity_max   = 1.0
opacity_min   = 0.3
mainWindow    = None   # set at runtime by main.py

# ─── Misc ────────────────────────────────────────────────────────────────────
isdeleted = '__deleted__'

def compact(path):
    """Return path relative to download dir, or basename if not under it."""
    try:
        rel = os.path.relpath(path, DEFAULT_DOWNLOAD_DIR)
        if not rel.startswith('..'):
            return rel
    except ValueError:
        pass
    return os.path.basename(path)

def set_main_window(win):
    global mainWindow
    mainWindow = win
