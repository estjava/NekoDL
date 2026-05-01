#coding: utf-8
"""
page_selector.py - Page/chapter selection registry for NekoDL

Extractors register themselves with @page_selector.register('type')
The GUI can then call filter() to let the user pick a range of pages.
"""

_registry: dict = {}


def register(type_name: str):
    """
    Decorator to register a page-list fetcher for *type_name*.

    Usage
    -----
    @page_selector.register('webtoon')
    def f(url):
        return [Page(...), Page(...)]
    """
    def decorator(fn):
        _registry[type_name] = fn
        return fn
    return decorator


def get(type_name: str):
    """Return the registered fetcher for *type_name*, or None."""
    return _registry.get(type_name)


def filter(pages: list, cw) -> list:
    """
    Return a slice of *pages* based on the range set in *cw*.

    If *cw* is None or has no range, all pages are returned.
    """
    if cw is None:
        return pages
    r = getattr(cw, 'range', None)
    if not r:
        return pages
    return pages[:r]
