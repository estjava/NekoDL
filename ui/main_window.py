#coding: utf-8
"""
ui/main_window.py - NekoDL Main Window (PyQt5)

Dark industrial aesthetic — dense, functional, no-nonsense downloader UI.
"""
import os
import sys


from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,QLineEdit, QPushButton, QListWidget, QListWidgetItem,QLabel, QProgressBar, QTextEdit, QSplitter,QStatusBar, QAction, QMenuBar, QFileDialog,QAbstractItemView, QFrame, QComboBox, QSizePolicy,QMessageBox,)
from PyQt5.QtCore    import Qt, QSize, pyqtSlot, QThread
from PyQt5.QtGui     import QFont, QColor, QPalette, QIcon, QFontDatabase

import constants
from ui.cw import DownloadWorker


# ─── Palette ──────────────────────────────────────────────────────────────────
STYLE = """
QMainWindow, QWidget {
    background: #0f0f0f;
    color: #e0e0e0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}

/* URL input */
#urlInput {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 6px 10px;
    color: #f0f0f0;
    font-size: 13px;
}
#urlInput:focus {
    border-color: #ff4d4d;
}

/* Buttons */
QPushButton {
    background: #1e1e1e;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 6px 16px;
    color: #ddd;
    font-weight: bold;
}
QPushButton:hover  { background: #2a2a2a; border-color: #ff4d4d; color: #fff; }
QPushButton:pressed{ background: #111; }

#btnDownload {
    background: #c0392b;
    border: 1px solid #e74c3c;
    color: #fff;
    padding: 6px 24px;
    font-size: 13px;
    letter-spacing: 1px;
}
#btnDownload:hover  { background: #e74c3c; }
#btnDownload:pressed{ background: #922b21; }

#btnStop {
    background: #1e1e1e;
    border: 1px solid #666;
    color: #aaa;
}
#btnStop:hover { border-color: #ff4d4d; color: #fff; }

/* Queue list */
#queueList {
    background: #111;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    alternate-background-color: #141414;
}
#queueList::item {
    padding: 4px 8px;
    border-bottom: 1px solid #1a1a1a;
}
#queueList::item:selected {
    background: #1f1f1f;
    color: #ff4d4d;
}

/* Log panel */
#logPanel {
    background: #0a0a0a;
    border: 1px solid #1e1e1e;
    border-radius: 4px;
    color: #666;
    font-size: 11px;
    font-family: 'Consolas', monospace;
}

/* Progress bar */
QProgressBar {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 3px;
    text-align: center;
    color: #999;
    height: 14px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c0392b, stop:1 #e74c3c);
    border-radius: 2px;
}

/* Status bar */
QStatusBar {
    background: #0a0a0a;
    border-top: 1px solid #1e1e1e;
    color: #555;
    font-size: 11px;
}

/* Splitter */
QSplitter::handle { background: #1e1e1e; }

/* Menu */
QMenuBar {
    background: #0f0f0f;
    border-bottom: 1px solid #1e1e1e;
    color: #aaa;
}
QMenuBar::item:selected { background: #1e1e1e; color: #fff; }
QMenu {
    background: #141414;
    border: 1px solid #333;
    color: #ccc;
}
QMenu::item:selected { background: #c0392b; color: #fff; }

/* Section labels */
#sectionLabel {
    color: #555;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 4px 0 2px 0;
}

/* Combo */
QComboBox {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 4px 8px;
    color: #ccc;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #141414;
    border: 1px solid #333;
    color: #ccc;
    selection-background-color: #c0392b;
}
"""

# ─── Queue Item Widget ────────────────────────────────────────────────────────
STATUS_COLOR = {
    'idle'       : '#555',
    'reading'    : '#f39c12',
    'downloading': '#3498db',
    'done'       : '#27ae60',
    'error'      : '#e74c3c',
    'stop'       : '#7f8c8d',
}

class QueueItemWidget(QWidget):
    def __init__(self, cw: DownloadWorker, parent=None):
        super().__init__(parent)
        self.cw = cw
        self._build()
        self._connect()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        # Row 1: status dot + title
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        self.dot   = QLabel('●')
        self.dot.setFixedWidth(14)
        self.dot.setStyleSheet('color: #555; font-size: 10px;')
        self.lbl_title = QLabel(self.cw.title)
        self.lbl_title.setStyleSheet('color: #ccc; font-size: 12px;')
        self.lbl_title.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred)
        row1.addWidget(self.dot)
        row1.addWidget(self.lbl_title)
        layout.addLayout(row1)

        # Row 2: progress bar + speed
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setFixedHeight(6)
        self.pbar.setTextVisible(False)
        self.lbl_speed = QLabel('')
        self.lbl_speed.setStyleSheet('color: #444; font-size: 10px;')
        self.lbl_speed.setFixedWidth(70)
        row2.addWidget(self.pbar)
        row2.addWidget(self.lbl_speed)
        layout.addLayout(row2)

    def _connect(self):
        self.cw.sig_title.connect(self._on_title)
        self.cw.sig_status.connect(self._on_status)
        self.cw.sig_progress.connect(self._on_progress)
        self.cw.sig_speed.connect(self._on_speed)

    @pyqtSlot(str)
    def _on_title(self, title):
        # truncate for display
        short = title if len(title) <= 60 else title[:57] + '…'
        self.lbl_title.setText(short)
        self.lbl_title.setToolTip(title)

    @pyqtSlot(str)
    def _on_status(self, status):
        color = STATUS_COLOR.get(status, '#555')
        self.dot.setStyleSheet(f'color: {color}; font-size: 10px;')
        if status == 'done':
            self.pbar.setValue(100)

    @pyqtSlot(int, int)
    def _on_progress(self, done, total):
        if total > 0:
            self.pbar.setValue(int(done / total * 100))

    @pyqtSlot(float)
    def _on_speed(self, bps):
        if bps < 1024:
            self.lbl_speed.setText(f'{bps:.0f} B/s')
        elif bps < 1024**2:
            self.lbl_speed.setText(f'{bps/1024:.1f} KB/s')
        else:
            self.lbl_speed.setText(f'{bps/1024**2:.1f} MB/s')


# ─── Main Window ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'{constants.APP_NAME}  v{constants.VERSION}')
        self.resize(900, 620)
        self.setStyleSheet(STYLE)
        self._workers: list[DownloadWorker] = []
        self._build_ui()
        self._build_menu()
        self._update_status()

    # ── UI construction ───────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 8)
        root.setSpacing(8)

        # ── Header ────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(0)
        lbl_app = QLabel(constants.APP_NAME)
        lbl_app.setStyleSheet(
            'color: #ff4d4d; font-size: 20px; font-weight: bold; '
            'letter-spacing: 4px; font-family: Consolas;'
        )
        lbl_ver = QLabel(f'  v{constants.VERSION}')
        lbl_ver.setStyleSheet('color: #333; font-size: 11px; padding-top: 6px;')
        hdr.addWidget(lbl_app)
        hdr.addWidget(lbl_ver)
        hdr.addStretch()
        root.addLayout(hdr)

        # ── URL input row ──────────────────────────────────────────────────
        url_row = QHBoxLayout()
        url_row.setSpacing(6)

        self.url_input = QLineEdit()
        self.url_input.setObjectName('urlInput')
        self.url_input.setPlaceholderText('Paste URL here…  (YouTube, Webtoon, and more)')
        self.url_input.returnPressed.connect(self._on_download)

        self.btn_download = QPushButton('DOWNLOAD')
        self.btn_download.setObjectName('btnDownload')
        self.btn_download.setFixedHeight(34)
        self.btn_download.clicked.connect(self._on_download)

        self.btn_stop = QPushButton('STOP')
        self.btn_stop.setObjectName('btnStop')
        self.btn_stop.setFixedHeight(34)
        self.btn_stop.setFixedWidth(60)
        self.btn_stop.clicked.connect(self._on_stop)

        url_row.addWidget(self.url_input)
        url_row.addWidget(self.btn_download)
        url_row.addWidget(self.btn_stop)
        root.addLayout(url_row)

        # ── Splitter: queue (top) + log (bottom) ──────────────────────────
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(4)

        # Queue panel
        queue_panel = QWidget()
        qp_layout   = QVBoxLayout(queue_panel)
        qp_layout.setContentsMargins(0, 0, 0, 0)
        qp_layout.setSpacing(4)

        lbl_q = QLabel('QUEUE')
        lbl_q.setObjectName('sectionLabel')
        qp_layout.addWidget(lbl_q)

        self.queue_list = QListWidget()
        self.queue_list.setObjectName('queueList')
        self.queue_list.setAlternatingRowColors(True)
        self.queue_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.queue_list.setSpacing(1)
        qp_layout.addWidget(self.queue_list)

        splitter.addWidget(queue_panel)

        # Log panel
        log_panel  = QWidget()
        lp_layout  = QVBoxLayout(log_panel)
        lp_layout.setContentsMargins(0, 0, 0, 0)
        lp_layout.setSpacing(4)

        lbl_log = QLabel('LOG')
        lbl_log.setObjectName('sectionLabel')
        lp_layout.addWidget(lbl_log)

        self.log_panel = QTextEdit()
        self.log_panel.setObjectName('logPanel')
        self.log_panel.setReadOnly(True)
        self.log_panel.setLineWrapMode(QTextEdit.NoWrap)
        lp_layout.addWidget(self.log_panel)

        splitter.addWidget(log_panel)
        splitter.setSizes([420, 160])

        root.addWidget(splitter)

        # ── Status bar ────────────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_status = QLabel('Ready.')
        self.status_bar.addWidget(self.lbl_status)

    def _build_menu(self):
        mb = self.menuBar()

        # File
        m_file = mb.addMenu('File')
        act_dir = QAction('Change Download Folder…', self)
        act_dir.triggered.connect(self._on_change_dir)
        act_quit = QAction('Quit', self)
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_dir)
        m_file.addSeparator()
        m_file.addAction(act_quit)

        # Queue
        m_queue = mb.addMenu('Queue')
        act_clear_done = QAction('Clear Completed', self)
        act_clear_done.triggered.connect(self._on_clear_done)
        act_clear_all = QAction('Clear All', self)
        act_clear_all.triggered.connect(self._on_clear_all)
        m_queue.addAction(act_clear_done)
        m_queue.addAction(act_clear_all)

        # About
        m_about = mb.addMenu('Help')
        act_about = QAction(f'About {constants.APP_NAME}', self)
        act_about.triggered.connect(self._on_about)
        m_about.addAction(act_about)

    # ── Slots ─────────────────────────────────────────────────────────────
    @pyqtSlot()
    def _on_download(self):
        url = self.url_input.text().strip()
        if not url:
            return
        self.url_input.clear()
        self._add_download(url)

    def _add_download(self, url: str):
        from utils import Downloader
        # check extractor exists
        cls = Downloader.find(url)
        if cls is None:
            self._log(f'[WARN] No extractor found for: {url}')
            self.lbl_status.setText(f'No extractor for: {url[:60]}')
            return

        cw = DownloadWorker(url)
        cw.sig_log.connect(self._log)
        cw.sig_finished.connect(self._on_finished)

        # Add to list
        item   = QListWidgetItem(self.queue_list)
        widget = QueueItemWidget(cw)
        item.setSizeHint(QSize(0, 58))
        self.queue_list.addItem(item)
        self.queue_list.setItemWidget(item, widget)

        self._workers.append(cw)
        cw.start()

        self._log(f'Added: {url}')
        self._update_status()

    @pyqtSlot()
    def _on_stop(self):
        for item in self.queue_list.selectedItems():
            row = self.queue_list.row(item)
            if 0 <= row < len(self._workers):
                self._workers[row].stop()

    @pyqtSlot(object)
    def _on_finished(self, cw: DownloadWorker):
        self._log(
            f'[{"DONE" if cw.status == "done" else cw.status.upper()}] '
            f'{cw.title}'
        )
        self._update_status()

    @pyqtSlot()
    def _on_change_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, 'Select Download Folder',
            constants.DEFAULT_DOWNLOAD_DIR,
        )
        if path:
            constants.DEFAULT_DOWNLOAD_DIR = path
            self._log(f'Download folder: {path}')
            self.lbl_status.setText(f'Folder: {path}')

    @pyqtSlot()
    def _on_clear_done(self):
        to_remove = []
        for i, w in enumerate(self._workers):
            if w.status in ('done', 'stop', 'error'):
                to_remove.append(i)
        for i in reversed(to_remove):
            self.queue_list.takeItem(i)
            self._workers.pop(i)
        self._update_status()

    @pyqtSlot()
    def _on_clear_all(self):
        for w in self._workers:
            w.stop()
        self.queue_list.clear()
        self._workers.clear()
        self._update_status()

    @pyqtSlot()
    def _on_about(self):
        QMessageBox.about(
            self,
            f'About {constants.APP_NAME}',
            f'<b>{constants.APP_NAME}</b> v{constants.VERSION}<br><br>'
            'A multi-platform media downloader.<br>'
            'Built with Python + PyQt5 + yt-dlp.',
        )

    # ── Helpers ───────────────────────────────────────────────────────────
    def _log(self, msg: str):
        self.log_panel.append(msg)
        # keep log lean
        doc = self.log_panel.document()
        if doc.blockCount() > 500:
            cursor = self.log_panel.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def _update_status(self):
        total  = len(self._workers)
        active = sum(1 for w in self._workers
                     if w.status in ('reading', 'downloading'))
        done   = sum(1 for w in self._workers if w.status == 'done')
        self.lbl_status.setText(
            f'Queue: {total}  |  Active: {active}  |  Done: {done}'
        )

    # ── Drag-and-drop URL ─────────────────────────────────────────────────
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e):
        url = e.mimeData().text().strip()
        if url:
            self.url_input.setText(url)
            self._on_download()
