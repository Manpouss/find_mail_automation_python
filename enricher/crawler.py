# enricher/crawler.py
from __future__ import annotations

import re
from typing import Tuple

import requests

from .constants import HEADERS, KEYWORD_HINTS, LOW_VALUE_PAGE_HINTS
from .extractors import extract_emails_filtered
from .urls import get_domain, normalize_url


def fetch_html(url: str, timeout: int = 10) -> Tuple[int, str]:
    """
    Fetch HTML content from a public URL.
    Returns (status_code, html_text). If error, returns (0, "").
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if not r.ok:
            return r.status_code, ""
        return r.status_code, r.text or ""
    except requests.RequestException:
        return 0, ""


def extract_internal_links(base_url: str, html: str, max_links: int = 5) -> list[str]:
    """
    Extract internal links from an HTML page that likely lead to contact/privacy/legal pages.
    Only keeps links on the same domain as base_url.
    """
    if not html:
        return []

    base_domain = get_domain(base_url)
    if not base_domain:
        return []

    # naive href extraction (good enough for controlled crawl)
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)

    candidates: list[str] = []
    for h in hrefs:
        h = (h or "").strip()
        if not h:
            continue

        low = h.lower()
        if not any(k in low for k in KEYWORD_HINTS):
            continue

        # normalize relative/partial links into absolute
        if h.startswith("//"):
            h = "https:" + h
        elif h.startswith("/"):
            h = "https://" + base_domain + h
        elif not h.startswith(("http://", "https://")):
            h = base_url.rstrip("/") + "/" + h.lstrip("/")

        # keep only internal
        if get_domain(h) != base_domain:
            continue

        nu = normalize_url(h)
        if nu:
            candidates.append(nu)

    # dedup preserve order + limit
    seen = set()
    out = []
    for u in candidates:
        if u not in seen:
            seen.add(u)
            out.append(u)
        if len(out) >= max_links:
            break

    return out


def _page_looks_low_value(url: str, html: str) -> bool:
    """
    Detect pages likely containing example emails (documentation/tutorial) rather than contact info.
    We only use this as a gentle filter to avoid selecting misleading emails.
    """
    u = (url or "").lower()
    h = (html or "").lower()
    return any(hint in u or hint in h for hint in LOW_VALUE_PAGE_HINTS)


def crawl_for_email(start_url: str, timeout: int = 10, max_pages: int = 3) -> Tuple[str, str, str, str]:
    """
    Controlled crawl: visit at most `max_pages` pages on a domain:
      - start_url
      - then a few internal contact/privacy/about/legal links from the first page

    Returns: (email, source_url, status, confidence)
      status: found / not_found / blocked / error
      confidence: "0.6" when found via crawl
    """
    first = normalize_url(start_url)
    if not first:
        return "", "", "error", ""

    to_visit = [first]
    visited = set()
    pages_checked = 0

    while to_visit and pages_checked < max_pages:
        url = to_visit.pop(0)
        if not url or url in visited:
            continue
        visited.add(url)

        code, html = fetch_html(url, timeout=timeout)
        pages_checked += 1

        if code in (401, 403, 429):
            return "", "", "blocked", ""

        if not html:
            continue

        # Avoid selecting misleading "example email" pages (gentle filter)
        if not _page_looks_low_value(url, html):
            emails = extract_emails_filtered(html)
            if emails:
                return emails[0], url, "found", "0.6"

        # only from first page: enqueue internal “contact-ish” pages
        if pages_checked == 1:
            for link in extract_internal_links(url, html, max_links=5):
                if link not in visited:
                    to_visit.append(link)

    return "", "", "not_found", ""
