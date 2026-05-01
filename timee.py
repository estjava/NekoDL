#coding: utf-8
"""
timee.py - Time utilities for NekoDL.

Provides a `sleep` helper that is cw-aware: it checks whether the
download worker (cw) is still alive and raises Stopped if not.
"""
import time as _time
from errors import Stopped


def sleep(seconds, cw=None, interval=0.2):
    """
    Sleep for *seconds*, checking *cw.alive* every *interval* seconds.

    If *cw* is None, behaves like ``time.sleep(seconds)``.
    Raises ``errors.Stopped`` if the worker is killed mid-sleep.
    """
    if cw is None:
        _time.sleep(seconds)
        return

    elapsed = 0.0
    while elapsed < seconds:
        chunk = min(interval, seconds - elapsed)
        _time.sleep(chunk)
        elapsed += chunk
        if not getattr(cw, 'alive', True):
            raise Stopped('Download stopped by user.')


def now():
    """Return current Unix timestamp as float."""
    return _time.time()


def timestamp(fmt='%Y%m%d_%H%M%S'):
    """Return current local time formatted as a string."""
    return _time.strftime(fmt, _time.localtime())
