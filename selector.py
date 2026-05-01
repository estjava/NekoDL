#coding: utf-8
"""
selector.py - Format/option selector registry for NekoDL

Extractors register:
  @selector.register('youtube')   → GUI dialog builder
  @selector.options('youtube')    → list of format choices
  @selector.default_option('youtube') → default choice string

Special return value:
  return selector.Cancel  → user dismissed the dialog
"""

# Sentinel for "user cancelled"
Cancel = object()

_register_registry : dict = {}
_options_registry  : dict = {}
_default_registry  : dict = {}


def register(type_name: str):
    """Decorator: register a GUI selector dialog for *type_name*."""
    def decorator(fn):
        _register_registry[type_name] = fn
        return fn
    return decorator


def options(type_name: str):
    """Decorator: register an options-list builder for *type_name*."""
    def decorator(fn):
        _options_registry[type_name] = fn
        return fn
    return decorator


def default_option(type_name: str):
    """Decorator: register a default-option getter for *type_name*."""
    def decorator(fn):
        _default_registry[type_name] = fn
        return fn
    return decorator


# ── Query helpers ─────────────────────────────────────────────────────────────
def get_selector(type_name: str):
    return _register_registry.get(type_name)

def get_options(type_name: str, urls: list = None):
    fn = _options_registry.get(type_name)
    return fn(urls) if fn else []

def get_default(type_name: str):
    fn = _default_registry.get(type_name)
    return fn() if fn else None
