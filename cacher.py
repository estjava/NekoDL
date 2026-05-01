#coding: utf-8
"""
cacher.py - Simple LRU-style in-memory cache for NekoDL
"""
from collections import OrderedDict


class Cache:
    """
    Thread-safe LRU cache with a fixed capacity.

    Usage
    -----
        c = Cache(128)
        c.set('key', value)
        val = c.get('key')   # None if missing
    """

    def __init__(self, capacity: int = 256):
        self._cap   = capacity
        self._store : OrderedDict = OrderedDict()

    def get(self, key):
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, key, value) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self._cap:
            self._store.popitem(last=False)

    def delete(self, key) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key) -> bool:
        return key in self._store
