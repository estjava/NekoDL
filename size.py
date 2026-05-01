#coding: utf-8
"""
size.py - Bandwidth/speed tracker for NekoDL

Usage
-----
    s = Size()
    s += 1024        # add bytes
    print(s.speed)   # bytes/sec since last reset
"""

import time


class Size:
    """Tracks cumulative bytes and computes a rolling speed estimate."""

    def __init__(self):
        self._total: int   = 0
        self._window: list = []   # list of (timestamp, bytes) tuples
        self._window_sec   = 3.0  # rolling window in seconds

    # ── Arithmetic ────────────────────────────────────────────────────────
    def __iadd__(self, n: int):
        self._total += n
        now = time.monotonic()
        self._window.append((now, n))
        # prune old entries
        cutoff = now - self._window_sec
        self._window = [(t, b) for t, b in self._window if t >= cutoff]
        return self

    def __int__(self):
        return self._total

    def __float__(self):
        return float(self._total)

    def __repr__(self):
        return f'Size(total={self._total}, speed={self.speed:.1f} B/s)'

    # ── Properties ────────────────────────────────────────────────────────
    @property
    def total(self) -> int:
        return self._total

    @property
    def speed(self) -> float:
        """Return bytes/sec averaged over the last window_sec seconds."""
        if not self._window:
            return 0.0
        now = time.monotonic()
        cutoff = now - self._window_sec
        window = [(t, b) for t, b in self._window if t >= cutoff]
        if not window:
            return 0.0
        elapsed = now - window[0][0]
        if elapsed <= 0:
            return 0.0
        total_bytes = sum(b for _, b in window)
        return total_bytes / elapsed

    def reset(self):
        self._total  = 0
        self._window = []
