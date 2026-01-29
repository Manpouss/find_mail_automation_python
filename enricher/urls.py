from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from .constants import BLOCKED_DOMAINS, OPTIONAL_LOW_VALUE_DOMAINS


def normalize_url(url: str) -> str:
    """
    Normalize URL:
    - strip spaces & trailing punctuation
    - ensure scheme
    - drop query/fragment
    """
    url = (url or "").strip()
    if not url:
        return ""

    url = url.strip(" \t\r\n\"'()[]{}<>,;:.")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return ""
        cleaned = parsed._replace(query="", fragment="")
        return urlunparse(cleaned)
    except Exception:
        return ""


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def extract_urls_from_bio_links(bio_links: str) -> list[str]:
    """
    Extract http(s) links from a string.
    Keeps it "Option A": only explicit http(s) links.
    """
    if not bio_links:
        return []

    urls = re.findall(r"https?://[^\s,]+", str(bio_links))
    cleaned = []
    for u in urls:
        nu = normalize_url(u)
        if nu:
            cleaned.append(nu)

    # dedup preserve order
    seen = set()
    out = []
    for u in cleaned:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def filter_external_urls(urls: list[str], max_urls: int = 2, exclude_low_value: bool = True) -> list[str]:
    """
    Keep only non-social external urls, limited to max_urls.
    """
    out = []
    for u in urls:
        u = normalize_url(u)
        if not u:
            continue

        dom = get_domain(u)

        if not dom:
            continue
        if dom in BLOCKED_DOMAINS:
            continue
        if exclude_low_value and dom in OPTIONAL_LOW_VALUE_DOMAINS:
            continue

        out.append(u)
        if len(out) >= max_urls:
            break
    return out
