#coding: utf-8
"""
filesize.py - Human-readable file size formatter for NekoDL
"""


def size(n: int | float, suffix: str = 'B') -> str:
    """
    Convert *n* bytes to a human-readable string.

    Examples
    --------
    >>> size(1024)
    '1.00 KB'
    >>> size(1_500_000)
    '1.43 MB'
    """
    n = float(n)
    for unit in ('', 'K', 'M', 'G', 'T', 'P'):
        if abs(n) < 1024.0:
            return f'{n:6.2f} {unit}{suffix}'
        n /= 1024.0
    return f'{n:.2f} E{suffix}'
