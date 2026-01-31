# enricher/urls.py
from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from .constants import BLOCKED_DOMAINS, OPTIONAL_LOW_VALUE_DOMAINS, STRIP_CHARS


# Basic list of commonly used TLD patterns (not exhaustive, but safe)
# We only use this to avoid obvious false positives like "hello.local" or "abc.def" if you decide.
# Here we keep it permissive: 2-24 letters (covers most real TLDs).
_DOMAIN_REGEX = re.compile(
    r"""(?ix)
    \b
    (?:[a-z0-9-]+\.)+          # one or more labels + dots
    [a-z]{2,24}                # tld
    \b
    """
)

_HTTP_URL_REGEX = re.compile(r"(?ix)\bhttps?://[^\s<>\"]+")
_WWW_URL_REGEX = re.compile(r"(?ix)\bwww\.[^\s<>\"]+")


def normalize_url(url: str) -> str:
    """
    Normalize URL:
    - strip spaces & trailing punctuation
    - ensure scheme (https:// if missing)
    - drop query/fragment
    """
    url = (url or "").strip()
    if not url:
        return ""

    url = url.strip(STRIP_CHARS)

    # If it's a naked domain like example.com -> add scheme
    if url.startswith("www."):
        url = "https://" + url
    elif not url.startswith(("http://", "https://")):
        # If it looks like a domain, make it a URL
        if is_probable_domain(url):
            url = "https://" + url
        else:
            return ""

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return ""
        cleaned = parsed._replace(query="", fragment="")
        return urlunparse(cleaned)
    except Exception:
        return ""


def get_domain(url: str) -> str:
    """Return lowercase netloc domain from a URL (normalized)."""
    try:
        p = urlparse(url)
        return (p.netloc or "").lower()
    except Exception:
        return ""


def is_probable_domain(text: str) -> bool:
    """
    Returns True if 'text' looks like a domain.tld (no scheme).
    We keep this simple and permissive.
    """
    if not text:
        return False
    t = text.strip(STRIP_CHARS).lower()

    # exclude if spaces or slashes
    if any(ch in t for ch in (" ", "/", "\\", "@")):
        return False

    # exclude obvious emails
    if "@" in t:
        return False

    return bool(_DOMAIN_REGEX.search(t))


def extract_urls_from_text(text: str) -> list[str]:
    """
    Extract URLs from arbitrary text:
    - http(s)://...
    - www....
    - naked domains like example.com
    Returns normalized, deduplicated list.
    """
    if not text:
        return []

    s = str(text)

    candidates: list[str] = []

    # 1) http(s)
    candidates.extend(_HTTP_URL_REGEX.findall(s))

    # 2) www.
    candidates.extend(_WWW_URL_REGEX.findall(s))

    # 3) naked domains (domain.tld)
    # We will take matches and normalize to https://domain.tld
    for m in _DOMAIN_REGEX.findall(s):
        candidates.append(m)

    # Normalize + dedup preserve order
    seen = set()
    out: list[str] = []
    for c in candidates:
        nu = normalize_url(c)
        if not nu:
            continue
        if nu not in seen:
            seen.add(nu)
            out.append(nu)

    return out


def filter_external_urls(
    urls: list[str],
    max_urls: int = 2,
    exclude_low_value: bool = True,
) -> list[str]:
    """
    Keep only useful external urls:
    - normalize each URL
    - exclude social/platform domains (BLOCKED_DOMAINS)
    - optionally exclude low ROI domains
    - limit to max_urls
    """
    out: list[str] = []
    for u in urls:
        nu = normalize_url(u)
        if not nu:
            continue

        dom = get_domain(nu)
        if not dom:
            continue

        # exact domain match (we store www. variants too)
        if dom in BLOCKED_DOMAINS:
            continue
        if exclude_low_value and dom in OPTIONAL_LOW_VALUE_DOMAINS:
            continue

        out.append(nu)
        if len(out) >= max_urls:
            break

    return out
