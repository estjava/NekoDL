#coding: utf-8
"""
ree.py - Thin regex wrapper used across extractors.

Provides a `find` helper that returns the first match (or a group/tuple)
instead of a match object, making extractor code more concise.
"""
import re as _re

# Re-export everything from the stdlib re so callers can do `import ree as re`
from re import (
    compile, escape, fullmatch, match, purge, search, split, sub, subn,
    findall, finditer, error,
    IGNORECASE, MULTILINE, DOTALL, VERBOSE, ASCII, UNICODE,
    I, M, S, X, A, U,
    Pattern, Match,
)


def find(pattern, string, flags=0, group=None):
    """
    Search *string* for *pattern* and return the matched content.

    - If the pattern has no groups  → return the whole match string, or None.
    - If the pattern has one group  → return that group string, or None.
    - If the pattern has 2+ groups → return a tuple of groups, or None.
    - Pass ``group=N`` to always return group N regardless of group count.

    Examples
    --------
    >>> find(r'v=([A-Za-z0-9_-]+)', 'https://youtu.be/watch?v=abc123')
    'abc123'
    >>> find(r'(\\w+):(\\w+)', 'key:value')
    ('key', 'value')
    >>> find(r'no-match', 'hello')   # → None
    """
    m = _re.search(pattern, string, flags)
    if m is None:
        return None
    if group is not None:
        return m.group(group)
    groups = m.groups()
    if not groups:
        return m.group(0)
    if len(groups) == 1:
        return groups[0]
    return groups
