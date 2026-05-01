#coding: utf-8
"""
error_printer.py - Format exceptions into readable strings for NekoDL
"""
import traceback


def print_error(e: Exception, show_tb: bool = True) -> str:
    """
    Format *e* into a human-readable string.

    Parameters
    ----------
    e       : the exception to format
    show_tb : include the full traceback (default True)

    Returns
    -------
    str : formatted error message, also printed to stdout
    """
    lines = [f'[ERROR] {type(e).__name__}: {e}']
    if show_tb:
        tb = traceback.format_exc()
        if tb and tb.strip() != 'NoneType: None':
            lines.append(tb)
    msg = '\n'.join(lines)
    print(msg)
    return msg
