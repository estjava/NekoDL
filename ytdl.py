#coding: utf-8
"""
ytdl.py - yt-dlp wrapper for NekoDL

Wraps yt-dlp's YoutubeDL and provides a Stream/Streams abstraction
compatible with the youtube_downloader.py extractor.
"""

from __future__ import annotations
import re
from typing import Any

import yt_dlp


# ─── Stream ───────────────────────────────────────────────────────────────────
class Stream:
    """Represents a single audio or video format from yt-dlp."""

    def __init__(self, fmt: dict, info: dict):
        self._fmt  = fmt
        self._info = info

        # ── resolution / fps ──────────────────────────────────────────────
        h = fmt.get('height')
        self.resolution : str | None = f'{h}p' if h else None
        self.fps        : int        = int(fmt.get('fps') or 0)

        # ── codecs ────────────────────────────────────────────────────────
        vcodec = fmt.get('vcodec') or ''
        acodec = fmt.get('acodec') or ''
        self.video_codec : str | None = vcodec if vcodec != 'none' else None
        self.audio_codec : str | None = acodec if acodec != 'none' else None

        # ── bitrates ──────────────────────────────────────────────────────
        self.abr     : int | None = int(fmt.get('abr') or 0) or None
        self.abr_str : str        = f'{self.abr}k' if self.abr else ''
        self.abr_fixed: bool      = False
        self.tbr     : float      = fmt.get('tbr') or 0.0

        # ── container ─────────────────────────────────────────────────────
        self.subtype : str = fmt.get('ext') or ''
        self.format  : str = fmt.get('format') or fmt.get('format_id') or ''

        # ── live ──────────────────────────────────────────────────────────
        self.live : bool = bool(info.get('is_live'))

        # ── URL (may be a DASH segment) ────────────────────────────────────
        self._url : str = fmt.get('url') or ''
        self._dash_type: str | None = None

    @property
    def url(self) -> str:
        return self._url

    def setDashType(self, type_: str) -> None:
        self._dash_type = type_

    def __repr__(self) -> str:
        return (
            f'Stream(res={self.resolution}, fps={self.fps}, '
            f'vcodec={self.video_codec}, acodec={self.audio_codec}, '
            f'abr={self.abr}, ext={self.subtype})'
        )


# ─── Streams collection ───────────────────────────────────────────────────────
class Streams:
    """List-like container of Stream objects."""

    def __init__(self, formats: list[dict], info: dict):
        self._streams = [Stream(f, info) for f in formats]

    def all(self) -> list[Stream]:
        return list(self._streams)

    def __iter__(self):
        return iter(self._streams)

    def __len__(self):
        return len(self._streams)


# ─── YouTube ─────────────────────────────────────────────────────────────────
class YouTube:
    """
    Fetch metadata for a single YouTube video URL using yt-dlp.

    Parameters
    ----------
    url : YouTube watch/short/playlist URL
    cw  : download worker (used for cookie/proxy settings if available)
    """

    def __init__(self, url: str, cw=None):
        self.url = url
        self.cw  = cw

        ydl_opts = {
            'quiet'           : True,
            'no_warnings'     : True,
            'skip_download'   : True,
            'extract_flat'    : False,
            'noplaylist'      : True,
        }

        _apply_cw_opts(ydl_opts, cw)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            self.info : dict = ydl.extract_info(url, download=False)

        self.video_id  : str     = self.info.get('id', '')
        self.subtitles : dict    = self.info.get('subtitles', {})
        self.streams   : Streams = Streams(
            self.info.get('formats', []), self.info
        )


# ─── YoutubeDL (playlist / channel) ──────────────────────────────────────────
class YoutubeDL:
    """
    Thin yt-dlp wrapper for playlist/channel extraction.

    Parameters
    ----------
    options : dict passed directly to yt-dlp (e.g. extract_flat, playlistend)
    cw      : download worker
    """

    def __init__(self, options: dict, cw=None):
        self._opts = {
            'quiet'      : True,
            'no_warnings': True,
        }
        self._opts.update(options)
        _apply_cw_opts(self._opts, cw)

    def extract_info(self, url: str) -> dict:
        with yt_dlp.YoutubeDL(self._opts) as ydl:
            return ydl.extract_info(url, download=False)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _apply_cw_opts(opts: dict, cw) -> None:
    """Inject proxy / cookie options from the cw worker into *opts*."""
    if cw is None:
        return
    proxy = getattr(cw, 'proxy', None)
    if proxy:
        opts['proxy'] = proxy
    cookiefile = getattr(cw, 'cookiefile', None)
    if cookiefile:
        opts['cookiefile'] = cookiefile
