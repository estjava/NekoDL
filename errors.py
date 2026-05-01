#coding: utf-8
"""
errors.py - Custom exception classes for NekoDL
"""

class NekoDLError(Exception):
    """Base exception for NekoDL."""
    pass


class Invalid(NekoDLError):
    """
    Raised when a URL or resource is invalid or cannot be processed.
    
    Args:
        msg  : human-readable error message
        fail : if True, do not retry — mark download as failed immediately
    """
    def __init__(self, msg='', fail=False):
        super().__init__(msg)
        self.fail = fail


class Retry(NekoDLError):
    """Raised to signal that the current operation should be retried."""
    pass


class NotSupported(NekoDLError):
    """Raised when a URL/feature is not supported by any extractor."""
    pass


class AuthRequired(NekoDLError):
    """Raised when authentication (login/cookie) is required."""
    pass


class Stopped(NekoDLError):
    """Raised when the user explicitly stops a download."""
    pass


class Timeout(NekoDLError):
    """Raised when a network operation times out."""
    pass


class ParseError(NekoDLError):
    """Raised when parsing HTML/JSON/etc. fails unexpectedly."""
    pass
