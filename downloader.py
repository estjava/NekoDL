#coding: utf-8
"""
downloader.py - Core download engine for NekoDL

Provides:
  - read_html / read_soup   : fetch a URL and return HTML or BeautifulSoup
  - get_ext                 : detect extension via HEAD request
  - ok_url                  : check if a URL is accessible
  - makedir_event           : create directory, notify cw
  - download_file           : download a single file with progress
  - total_download_size_*   : global counters
"""

import os
import re
import threading
import traceback
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import constants
from utils import Session, Soup, get_ext as _get_ext, clean_title

# ─── Global size counters ─────────────────────────────────────────────────────
total_download_size        = 0   # bytes downloaded via HTTP
total_download_size_torrent= 0   # bytes downloaded via BitTorrent
total_upload_size_torrent  = 0   # bytes uploaded via BitTorrent
_counter_lock = threading.Lock()


def _add_download(n: int) -> None:
    global total_download_size
    with _counter_lock:
        total_download_size += n


# ─── HTTP helpers ─────────────────────────────────────────────────────────────
def read_html(url: str, session: Session | None = None,
              referer: str = '', encoding: str = '') -> str:
    """
    Fetch *url* and return the response body as a string.

    Parameters
    ----------
    session  : reuse an existing Session (creates a temporary one if None)
    referer  : value for the Referer header
    encoding : force a specific charset (default: detect from response)
    """
    sess = session or Session()
    headers = {}
    if referer:
        headers['Referer'] = referer
    resp = sess.get(url, headers=headers)
    resp.raise_for_status()
    if encoding:
        resp.encoding = encoding
    return resp.text


def read_soup(url: str, session: Session | None = None,
              referer: str = '', encoding: str = '',
              parser: str = 'html.parser') -> BeautifulSoup:
    """Fetch *url* and return a BeautifulSoup object."""
    html = read_html(url, session=session, referer=referer, encoding=encoding)
    return Soup(html, parser)


def get_ext(url: str, referer: str = '',
            session: Session | None = None) -> str:
    """
    Determine the file extension for *url* via a HEAD request.
    Falls back to parsing the URL path.
    """
    # First try from the URL itself
    ext = _get_ext(url)
    if ext:
        return ext

    # HEAD request to read Content-Type
    try:
        sess = session or Session()
        headers = {'Referer': referer} if referer else {}
        resp = sess.head(url, headers=headers, allow_redirects=True,
                         timeout=constants.DEFAULT_TIMEOUT)
        ct = resp.headers.get('Content-Type', '')
        return _get_ext(url, content_type=ct)
    except Exception:
        return ''


def ok_url(url: str, referer: str = '',
           session: Session | None = None) -> bool:
    """
    Return True if *url* is accessible (HTTP 2xx/3xx).
    Used by extractors to validate stream URLs before committing.
    """
    try:
        sess = session or Session()
        headers = {'Referer': referer} if referer else {}
        resp = sess.head(url, headers=headers, allow_redirects=True,
                         timeout=constants.DEFAULT_TIMEOUT)
        return resp.ok
    except Exception:
        return False


# ─── Directory helpers ────────────────────────────────────────────────────────
def makedir_event(path: str, cw=None) -> None:
    """Create *path* (including parents) and notify *cw* if provided."""
    os.makedirs(path, exist_ok=True)
    if cw and hasattr(cw, 'print_'):
        cw.print_(f'Created directory: {path}')


# ─── Single-file downloader ───────────────────────────────────────────────────
_CHUNK = 1024 * 256   # 256 KB


def download_file(url: str, dest: str,
                  session: Session | None = None,
                  referer: str = '',
                  cw=None,
                  chunk_size: int = _CHUNK) -> str:
    """
    Download *url* to *dest* (full file path).

    Progress is reported to *cw* if it has a ``setFileSize`` method.
    Returns the destination path.
    """
    sess = session or Session()
    headers = {'Referer': referer} if referer else {}

    os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)

    with sess.get(url, headers=headers, stream=True,
                  timeout=constants.DEFAULT_TIMEOUT) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get('Content-Length', 0))
        downloaded = 0

        if cw and hasattr(cw, 'setTotalFileSize') and total:
            cw.setTotalFileSize(total)

        with open(dest, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    _add_download(len(chunk))

                    if cw:
                        if hasattr(cw, 'setFileSize'):
                            cw.setFileSize(downloaded)
                        if not getattr(cw, 'alive', True):
                            raise InterruptedError('Download stopped.')

    return dest
