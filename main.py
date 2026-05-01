#coding: utf-8
"""
main.py - NekoDL entry point

Usage
-----
    python main.py
"""
import sys
import os

# ── Make sure root is on sys.path ─────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Load extractors ───────────────────────────────────────────────────────────
def _load_extractors():
    """Auto-import all extractor modules so they register themselves."""
    extractor_dir = os.path.join(ROOT, 'src', 'extractor')
    if not os.path.isdir(extractor_dir):
        return
    for fname in os.listdir(extractor_dir):
        if fname.endswith('_downloader.py') and not fname.startswith('_'):
            modname = fname[:-3]
            try:
                # Add extractor dir to path temporarily
                if extractor_dir not in sys.path:
                    sys.path.insert(0, extractor_dir)
                __import__(modname)
            except Exception as e:
                print(f'[WARN] Could not load extractor {modname}: {e}')


def main():
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore    import Qt
    from PyQt5.QtGui     import QFont

    import constants
    import utils
    from ui.main_window import MainWindow
    from translator import load as load_lang

    # ── Qt high-DPI ───────────────────────────────────────────────────────
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(constants.APP_NAME)
    app.setApplicationVersion(constants.VERSION)

    # ── Default font ──────────────────────────────────────────────────────
    font = QFont('Consolas', 10)
    app.setFont(font)

    # ── Language ──────────────────────────────────────────────────────────
    load_lang('en')

    # ── Load extractors ───────────────────────────────────────────────────
    _load_extractors()

    # ── Main window ───────────────────────────────────────────────────────
    win = MainWindow()
    constants.set_main_window(win)
    utils.ui = win

    win.setAcceptDrops(True)
    win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
