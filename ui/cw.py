#coding: utf-8
"""
ui/cw.py - DownloadWorker (CW) — the per-download thread object
"""
import os
import threading
import traceback

from PyQt5.QtCore import QObject, pyqtSignal

import constants
from errors import Stopped, Invalid
from utils  import Session, get_ext, clean_title, check_alive
import downloader as dl_engine


class DownloadWorker(QObject):
    sig_title    = pyqtSignal(str)
    sig_status   = pyqtSignal(str)
    sig_progress = pyqtSignal(int, int)
    sig_speed    = pyqtSignal(float)
    sig_log      = pyqtSignal(str)
    sig_finished = pyqtSignal(object)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url        = url
        self.gal_num    = url
        self.title      = url
        self.status     = 'idle'
        self.alive      = True
        self.paused     = False
        self.pause_lock = False
        self.pause_data = {}
        self.seeding    = False
        self.urls       = []
        self.imgs       = []
        self.dones      = set()
        self.names      = []
        self.dir        = constants.DEFAULT_DOWNLOAD_DIR
        self._filesize_total = 0
        self._filesize_done  = 0
        self._speed          = 0.0
        self.range   = 0
        self._extras = {}
        self.v3      = {}
        self._torrent_s = None
        self.downloader_pausable = False
        self.pbar    = _ProgressBarStub()
        self._thread = None

    def get_extra(self, key, default=None): return self._extras.get(key, default)
    def set_extra(self, key, value):        self._extras[key] = value
    def remove_extra(self, key):            self._extras.pop(key, None)

    def print_(self, msg):      self.sig_log.emit(str(msg))
    def print_error(self, e):   self.print_(f'[ERROR] {e}\n{traceback.format_exc()}')

    def setTitle(self, title, update_filter=True):
        self.title = title
        self.sig_title.emit(title)

    def setTotalFileSize(self, n):  self._filesize_total = n
    def setFileSize(self, n):
        self._filesize_done = n
        if self._filesize_total:
            self.sig_progress.emit(n, self._filesize_total)
    def setSpeed(self, bps):        self.sig_speed.emit(bps)
    def setUploadSpeed(self, bps):  pass
    def setColor(self, color):      self.sig_status.emit(color)
    def setIcon(self, url, icon=False): return True
    def setPieces(self, p):         pass
    def clearPieces(self):          pass
    def enableSegment(self, overwrite=False): pass
    def update_tools_buttons(self): pass
    def listWidget(self):           return None

    def stop(self):
        self.alive  = False
        self.status = 'stop'
        self.sig_status.emit('stop')

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            self._do_run()
        except Stopped:
            self.status = 'stop'
            self.sig_status.emit('stop')
        except Exception as e:
            self.print_error(e)
            self.status = 'error'
            self.sig_status.emit('error')
        finally:
            self.sig_finished.emit(self)

    def _do_run(self):
        from utils import Downloader
        cls = Downloader.find(self.url)
        if cls is None:
            raise Invalid(f'No extractor found for: {self.url}', fail=True)

        self.status = 'reading'
        self.sig_status.emit('reading')
        self.setTitle(f'Reading... {self.url}')

        extractor = cls(self.url, cw=self)
        extractor.init()
        extractor.read()
        check_alive(self)

        self.title = extractor.title
        self.urls  = list(extractor.urls)
        self.dir   = os.path.join(
            constants.DEFAULT_DOWNLOAD_DIR,
            clean_title(extractor.title),
        )
        os.makedirs(self.dir, exist_ok=True)

        self.status = 'downloading'
        self.sig_status.emit('downloading')

        session = extractor.session or Session()
        total   = len(self.urls)

        for i, url_item in enumerate(self.urls):
            check_alive(self)
            actual_url = str(url_item) if callable(url_item) else url_item
            ext  = get_ext(actual_url)
            dest = os.path.join(self.dir, f'{i+1:04d}{ext}')
            self.setTitle(f'{self.title}  ({i+1}/{total})')
            self.sig_progress.emit(i, total)
            dl_engine.download_file(actual_url, dest, session=session, cw=self)
            self.imgs.append(dest)
            self.names.append(dest)

        self.sig_progress.emit(total, total)
        self.status = 'done'
        self.sig_status.emit('done')
        self.setTitle(self.title)


class _ProgressBarStub:
    def hide(self): pass
    def show(self): pass
    def setFormat(self, fmt): pass
    def setMaximum(self, n): pass
    def setValue(self, n): pass
