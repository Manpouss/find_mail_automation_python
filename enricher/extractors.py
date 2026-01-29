from __future__ import annotations

from typing import List, Tuple
from .constants import EMAIL_REGEX, STRIP_CHARS, PLACEHOLDER_DOMAINS, PLACEHOLDER_DOMAIN_SUBSTRINGS, PLACEHOLDER_TLDS


def is_placeholder_email(email: str) -> bool:
    """
    Filters obvious example emails like:
    - utilisateur@nomdedomaine.extension
    - any domain ending with .extension
    - example.com/org/net
    """
    if not email or "@" not in email:
        return True

    local, domain = email.lower().split("@", 1)

    if domain in PLACEHOLDER_DOMAINS:
        return True

    if any(sub in domain for sub in PLACEHOLDER_DOMAIN_SUBSTRINGS):
        return True

    # tld check
    if "." in domain:
        tld = domain.rsplit(".", 1)[-1]
        if tld in PLACEHOLDER_TLDS:
            return True

    return False


def extract_emails(text: str) -> List[str]:
    """Extract and normalize emails from arbitrary text."""
    if not text:
        return []

    raw = EMAIL_REGEX.findall(str(text))
    cleaned: List[str] = []

    for e in raw:
        e2 = e.strip(STRIP_CHARS).lower()
        if "@" in e2 and "." in e2.split("@")[-1] and " " not in e2:
            cleaned.append(e2)

    # deduplicate while preserving order
    seen = set()
    uniq = []
    for e in cleaned:
        if e not in seen:
            seen.add(e)
            uniq.append(e)

    return uniq


def extract_emails_filtered(text: str) -> List[str]:
    """Extract emails and remove placeholder/example ones."""
    emails = extract_emails(text)
    return [e for e in emails if not is_placeholder_email(e)]


def enrich_row_local(bio_text: str, detected_emails: str) -> Tuple[str, str, str, str, str]:
    """
    Returns: (email, source_url, method, status, confidence)
    Priority:
      1) detected_emails (confidence 1.0)
      2) bio_text (confidence 0.8)
      3) not_found
    """
    emails = extract_emails_filtered(detected_emails)
    if emails:
        return emails[0], "detected_emails", "detected_emails", "found", "1.0"

    emails = extract_emails_filtered(bio_text)
    if emails:
        return emails[0], "bio_text", "bio_text", "found", "0.8"

    return "", "", "", "not_found", ""
