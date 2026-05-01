#coding: utf-8
"""
clf2.py - Cloudflare challenge solver for NekoDL

Attempts to bypass Cloudflare's JS challenge by using cloudscraper.
Falls back to a plain requests GET if cloudscraper is not installed.
"""

try:
    import cloudscraper as _cs
    _HAS_CS = True
except ImportError:
    _HAS_CS = False

from utils import Session


def solve(url: str, session: Session | None = None) -> bool:
    """
    Attempt to solve a Cloudflare challenge for *url*.

    Cookies obtained during solving are injected into *session* so
    subsequent requests by the same session pass through.

    Returns True if the page is accessible, False otherwise.
    """
    if session is None:
        return False

    if _HAS_CS:
        try:
            scraper = _cs.create_scraper(sess=session)
            resp = scraper.get(url, timeout=30)
            # Merge cookies back into the caller's session
            session.cookies.update(scraper.cookies)
            return resp.ok
        except Exception as e:
            print(f'[clf2] cloudscraper failed: {e}')

    # Fallback — plain GET (works if there is no real CF challenge)
    try:
        resp = session.get(url, timeout=30)
        return resp.ok
    except Exception as e:
        print(f'[clf2] fallback GET failed: {e}')
        return False
