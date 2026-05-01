#coding: utf-8
"""
myjson.py - JSON helpers for NekoDL

Thin wrapper around stdlib json with convenience helpers.
"""
import json as _json


def loads(s: str | bytes, **kwargs):
    """Parse JSON string, stripping leading/trailing whitespace."""
    if isinstance(s, (bytes, bytearray)):
        s = s.decode('utf-8', errors='replace')
    return _json.loads(s.strip(), **kwargs)


def dumps(obj, indent: int = 2, ensure_ascii: bool = False, **kwargs) -> str:
    return _json.dumps(obj, indent=indent,
                       ensure_ascii=ensure_ascii, **kwargs)


def load(fp, **kwargs):
    return _json.load(fp, **kwargs)


def dump(obj, fp, indent: int = 2,
         ensure_ascii: bool = False, **kwargs) -> None:
    _json.dump(obj, fp, indent=indent,
               ensure_ascii=ensure_ascii, **kwargs)
