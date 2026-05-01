#coding: utf-8
"""
utils.py - Core utilities for NekoDL

Provides:
  - Downloader   base class for all extractors
  - Session      requests.Session wrapper with default headers & retries
  - LazyUrl      deferred URL resolver
  - Soup         BeautifulSoup shortcut
  - try_n        retry decorator
  - check_alive  raise Stopped if cw is dead
  - clean_title  sanitise filenames
  - get_ext      guess file extension from URL/content-type
  - urljoin      urllib urljoin re-export
  - query_url    parse query string from URL
  - lock         threading.Lock decorator
  - uuid         generate unique id
  - format_filename, filter_range, get_max_range
  - get_resolution, get_abr
  - compatstr, html_unescape
  - SD           shared settings dict
  - ui / ui_setting / windows / exec_queue  (set at runtime by main.py)
"""

import os
import re
import threading
import traceback
import uuid as _uuid
from functools import wraps
from urllib.parse import urljoin, urlparse, parse_qs, unquote, quote
from html import unescape as html_unescape

import requests
from bs4 import BeautifulSoup

import constants
from errors import Stopped, Invalid

# ─── Runtime references (set by main.py) ─────────────────────────────────────
ui          = None   # main QMainWindow instance
ui_setting  = None   # settings widget / namespace
windows     = []     # list of open sub-windows
exec_queue  = None   # Qt-thread executor

# ─── Shared settings dict ─────────────────────────────────────────────────────
SD: dict = {
    'youtube': {
        'channel_reverse': False,
    },
}

# ─── image_reader stub (replaced by GUI at runtime) ──────────────────────────
class _ImageReader:
    def getFilePixmap(self, name, size=32, pad=2):
        return None

image_reader = _ImageReader()


# ─── lock decorator ──────────────────────────────────────────────────────────
def lock(fn):
    """Method decorator that acquires a per-instance threading.Lock."""
    attr = f'_lock_{fn.__name__}'
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, attr):
            object.__setattr__(self, attr, threading.Lock()) \
                if hasattr(self, '__dict__') else None
            setattr(self.__class__, attr, threading.Lock())
        l = getattr(self, attr, None) or getattr(self.__class__, attr)
        with l:
            return fn(self, *args, **kwargs)
    return wrapper


# ─── actions registry ─────────────────────────────────────────────────────────
_action_registry: dict = {}

def actions(type_name):
    """Decorator to register a context-menu action builder for a downloader type."""
    def decorator(fn):
        _action_registry[type_name] = fn
        return fn
    return decorator

def get_actions(type_name, cw):
    fn = _action_registry.get(type_name)
    return fn(cw) if fn else []


# ─── Session ──────────────────────────────────────────────────────────────────
DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}

class Session(requests.Session):
    """requests.Session with sane defaults for scraping."""
    def __init__(self):
        super().__init__()
        self.headers.update(DEFAULT_HEADERS)
        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.adapters.Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504],
            )
        )
        self.mount('http://', adapter)
        self.mount('https://', adapter)

    def get(self, url, **kwargs):
        kwargs.setdefault('timeout', constants.DEFAULT_TIMEOUT)
        return super().get(url, **kwargs)

    def post(self, url, **kwargs):
        kwargs.setdefault('timeout', constants.DEFAULT_TIMEOUT)
        return super().post(url, **kwargs)


# ─── Soup shortcut ────────────────────────────────────────────────────────────
def Soup(html: str, parser: str = 'html.parser') -> BeautifulSoup:
    return BeautifulSoup(html, parser)


# ─── URL helpers ─────────────────────────────────────────────────────────────
def query_url(url: str) -> dict:
    """Return parsed query string as dict of lists."""
    return parse_qs(urlparse(url).query)


def compatstr(s) -> str:
    """Ensure s is a plain str."""
    if isinstance(s, bytes):
        return s.decode('utf-8', errors='replace')
    return str(s)


# ─── Filename helpers ─────────────────────────────────────────────────────────
_ILLEGAL = r'\/:*?"<>|'
_ILLEGAL_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

def clean_title(title: str, max_len: int = 200) -> str:
    """Remove characters illegal in filenames and truncate."""
    title = html_unescape(title or '')
    title = _ILLEGAL_RE.sub('_', title).strip(' ._')
    return title[:max_len] or 'untitled'


def format_filename(title: str, url: str, p: int = 0, ext: str = '') -> str:
    """Build a numbered filename like  title/0001.ext"""
    base = clean_title(title)
    if not ext:
        ext = get_ext(url)
    return os.path.join(base, f'{p:04d}{ext}')


# ─── Extension helpers ────────────────────────────────────────────────────────
_EXT_MAP = {
    'image/jpeg': '.jpg',
    'image/png':  '.png',
    'image/gif':  '.gif',
    'image/webp': '.webp',
    'video/mp4':  '.mp4',
    'video/webm': '.webm',
    'audio/mpeg': '.mp3',
    'audio/webm': '.weba',
    'application/pdf': '.pdf',
}

def get_ext(url: str, content_type: str = '') -> str:
    """Guess file extension from URL path or content-type header."""
    if content_type:
        for mime, ext in _EXT_MAP.items():
            if mime in content_type:
                return ext
    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    return ext.lower() if ext else ''


# ─── Range / resolution helpers ───────────────────────────────────────────────
def get_max_range(cw) -> int:
    if cw is None:
        return 9999
    return getattr(cw, 'range', 9999) or 9999

def filter_range(items: list, range_: int) -> list:
    if not range_:
        return items
    return items[:range_]

def get_resolution(text: str = '') -> int | None:
    """Parse '1080p' → 1080, or return None for 'best'."""
    if not text:
        return None
    m = re.search(r'(\d+)', text)
    return int(m.group(1)) if m else None

def get_abr(text: str = '') -> int | None:
    """Parse '128kbps' → 128, or return None for 'best'."""
    if not text:
        return None
    m = re.search(r'(\d+)', text)
    return int(m.group(1)) if m else None


# ─── UUID ────────────────────────────────────────────────────────────────────
def uuid() -> str:
    return str(_uuid.uuid4())


# ─── check_alive ─────────────────────────────────────────────────────────────
def check_alive(cw) -> None:
    """Raise Stopped if *cw* has been killed."""
    if cw is not None and not getattr(cw, 'alive', True):
        raise Stopped('Download stopped.')


# ─── try_n decorator ──────────────────────────────────────────────────────────
def try_n(n: int = 3, sleep: float = 0.0, exc=Exception):
    """
    Decorator: retry the function up to *n* times on *exc*.
    Uses timee.sleep between retries if sleep > 0.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(n):
                try:
                    return fn(*args, **kwargs)
                except exc as e:
                    last_exc = e
                    if sleep > 0:
                        import timee
                        timee.sleep(sleep * (i + 1))
            raise last_exc
        return wrapper
    return decorator


# ─── get_imgs_already ────────────────────────────────────────────────────────
def get_imgs_already(type_: str, title: str, page, cw) -> list:
    """
    Return cached image list for *page* if it was already downloaded.
    Stub — real implementation checks the filesystem / DB.
    """
    return []


# ─── LazyUrl ─────────────────────────────────────────────────────────────────
class LazyUrl:
    """
    A URL that is resolved lazily on first access.

    Parameters
    ----------
    url      : the seed URL passed to the resolver
    resolver : callable(url) → str  — returns the actual download URL
    owner    : the object that owns this LazyUrl (for error context)
    pp       : optional post-processor callable(resolved_url) → str
    """
    def __init__(self, url: str, resolver, owner=None, pp=None):
        self._url      = url
        self._resolver = resolver
        self._owner    = owner
        self._pp       = pp
        self._resolved: str | None = None

    def __call__(self) -> str:
        if self._resolved is None:
            result = self._resolver(self._url)
            if self._pp:
                result = self._pp(result)
            self._resolved = result
        return self._resolved

    def __str__(self) -> str:
        return self()

    def __repr__(self) -> str:
        resolved = self._resolved or '<unresolved>'
        return f'LazyUrl({resolved!r})'

    # Allow `if lazy_url:` checks
    def __bool__(self) -> bool:
        return bool(self._url)


# ─── Downloader base class ────────────────────────────────────────────────────
class Downloader:
    """
    Abstract base class for all NekoDL extractors.

    Subclasses must define:
      - type        : str  — unique identifier e.g. 'youtube'
      - URLS        : list — URL patterns this extractor handles
      - read(self)  : populate self.urls and self.title

    Optional class attributes:
      - MAX_CORE    : int   — max download threads
      - MAX_SPEED   : float — MB/s cap (0 = unlimited)
      - display_name: str   — human-readable name shown in UI
      - ACCEPT_COOKIES: list of regex patterns
    """
    type         : str  = ''
    URLS         : list = []
    MAX_CORE     : int  = 4
    MAX_SPEED    : float = 0.0
    display_name : str  = ''
    ACCEPT_COOKIES: list = []
    single       : bool = False
    PRIORITY     : int  = 0
    STOP_READING : bool = False

    # ── Registry ──────────────────────────────────────────────────────────
    _registry: dict = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.type:
            Downloader._registry[cls.type] = cls

    @classmethod
    def get(cls, type_: str):
        return cls._registry.get(type_)

    @classmethod
    def find(cls, url: str):
        """Return the first registered Downloader subclass that handles *url*."""
        for sub in cls._registry.values():
            if sub.match(url):
                return sub
        return None

    @classmethod
    def match(cls, url: str) -> bool:
        for pattern in cls.URLS:
            if callable(pattern):
                if pattern(url):
                    return True
            elif isinstance(pattern, str):
                if pattern.startswith('regex:'):
                    if re.search(pattern[6:], url):
                        return True
                elif pattern in url:
                    return True
        return False

    @classmethod
    def fix_url(cls, url: str) -> str:
        """Optionally normalise the URL before processing."""
        return url

    @classmethod
    def key_id(cls, url: str) -> str:
        """Return a stable identifier for deduplication."""
        return url

    # ── Instance ──────────────────────────────────────────────────────────
    def __init__(self, url: str, cw=None):
        self.url    = self.fix_url(url)
        self.cw     = cw
        self.urls   : list = []
        self.title  : str  = ''
        self.artist : str  = ''
        self.session: Session | None = None

        # download directory — set by cw or default
        dl_dir = getattr(cw, 'dir', None) or constants.DEFAULT_DOWNLOAD_DIR
        self.dir = dl_dir

    def init(self):
        """Called once before read(). Override for setup logic."""
        pass

    def read(self):
        """Populate self.urls and self.title. Must be overridden."""
        raise NotImplementedError

    def print_(self, msg: str) -> None:
        if self.cw is not None and hasattr(self.cw, 'print_'):
            self.cw.print_(msg)
        else:
            print(msg)

    def print_error(self, e: Exception) -> None:
        self.print_(f'[ERROR] {e}\n{traceback.format_exc()}')

    def setIcon(self, url, icon=False):
        if self.cw and hasattr(self.cw, 'setIcon'):
            return self.cw.setIcon(url, icon=icon)

    def process_playlist(self, title: str, videos: list):
        """Handle playlist mode — append all video URLs."""
        self.title = title
        for video in videos:
            self.urls.append(video.url)
        return videos[0] if videos else None

    def enableSegment(self, overwrite=False):
        if self.cw and hasattr(self.cw, 'enableSegment'):
            self.cw.enableSegment(overwrite=overwrite)

    def update_tools_buttons(self):
        if self.cw and hasattr(self.cw, 'update_tools_buttons'):
            self.cw.update_tools_buttons()

    @property
    def status(self):
        if self.cw:
            return getattr(self.cw, 'status', 'run')
        return 'run'

    def stop(self):
        if self.cw and hasattr(self.cw, 'stop'):
            self.cw.stop()
