#coding: utf-8
"""
translator.py - Lightweight i18n for NekoDL.

Translation files live in  translation/tr_<lang>.hdl
Each line is:  source_text=translated_text
Lines starting with # are comments.

Usage
-----
    from translator import tr_, tr
    print(tr_('읽는 중... {}').format('MyTitle'))
"""
import os
import re

# ─── State ───────────────────────────────────────────────────────────────────
_table: dict[str, str] = {}
_lang:  str             = 'en'

TRANS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translation')


# ─── Loader ──────────────────────────────────────────────────────────────────
def load(lang: str = 'en') -> None:
    """Load translation table for *lang* (e.g. 'ko', 'ja', 'en')."""
    global _table, _lang
    _table = {}
    _lang  = lang
    path   = os.path.join(TRANS_DIR, f'tr_{lang}.hdl')
    if not os.path.exists(path):
        return   # silently fall back to pass-through
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                src, _, dst = line.partition('=')
                _table[src.strip()] = dst.strip()


def get_lang() -> str:
    return _lang


# ─── Public helpers ───────────────────────────────────────────────────────────
def tr_(text: str) -> str:
    """
    Translate *text*, returning the original if no translation found.
    Supports format strings — callers do  tr_('hello {}').format(name).
    """
    return _table.get(text, text)


def tr(widget) -> None:
    """
    Walk a PyQt5 widget tree and translate all visible text in-place.
    Falls back to no-op if PyQt5 is not available.
    """
    try:
        from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QAction
    except ImportError:
        return

    if isinstance(widget, (QLabel, QPushButton)):
        widget.setText(tr_(widget.text()))
    elif hasattr(widget, 'actions'):
        for action in widget.actions():
            action.setText(tr_(action.text()))

    if isinstance(widget, QWidget):
        for child in widget.findChildren(QWidget):
            tr(child)


# Load English by default
load('en')
