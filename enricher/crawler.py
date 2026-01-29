from __future__ import annotations

import re
import requests

from .constants import HEADERS, KEYWORD_HINTS
from .extractors import extract_emails_filtered
from .urls import get_domain, normalize_url


def fetch_html(url: str, timeout: int = 10) -> tuple[int, str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r.status_code, r.text if r.ok else ""
    except requests.RequestException:
        return 0, ""


def extract_internal_links(base_url: str, html: str, max_links: int = 5) -> list[str]:
    if not html:
        return []

    base_domain = get_domain(base_url)
    if not base_domain:
        return []

    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)

    candidates = []
    for h in hrefs:
        h = (h or "").strip()
        if not h:
            continue

        low = h.lower()
        if not any(k in low for k in KEYWORD_HINTS):
            continue

        if h.startswith("//"):
            h = "https:" + h
        elif h.startswith("/"):
            h = "https://" + base_domain + h
        elif not h.startswith(("http://", "https://")):
            h = base_url.rstrip("/") + "/" + h.lstrip("/")

        if get_domain(h) != base_domain:
            continue

        nu = normalize_url(h)
        if nu:
            candidates.append(nu)

    # dedup preserve order
    seen = set()
    out = []
    for u in candidates:
        if u not in seen:
            seen.add(u)
            out.append(u)
        if len(out) >= max_links:
            break

    return out


def crawl_for_email(start_url: str, timeout: int = 10, max_pages: int = 3) -> tuple[str, str, str, str]:
    """
    Returns: (email, source_url, status, confidence)
    status: found / not_found / blocked
    """
    to_visit = [normalize_url(start_url)]
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

        emails = extract_emails_filtered(html)
        if emails:
            print(f"[DEBUG] emails found on {url}: {emails[:10]}")
            return emails[0], url, "found", "0.6"

        if pages_checked == 1:
            extra = extract_internal_links(url, html, max_links=5)
            for e in extra:
                if e not in visited:
                    to_visit.append(e)

    return "", "", "not_found", ""
