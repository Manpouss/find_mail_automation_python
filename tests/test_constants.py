# tests/test_constants.py
from __future__ import annotations

from enricher.constants import (
    EMAIL_REGEX,
    BLOCKED_DOMAINS,
    OPTIONAL_LOW_VALUE_DOMAINS,
    KEYWORD_HINTS,
    PLACEHOLDER_DOMAINS,
    PLACEHOLDER_DOMAIN_SUBSTRINGS,
    PLACEHOLDER_TLDS,
    LOW_VALUE_PAGE_HINTS,
)


def test_email_regex_basic():
    text = "Contact: John.Doe+test@example.com and hello@my-site.co.uk"
    found = EMAIL_REGEX.findall(text)
    # Regex should capture both
    assert "John.Doe+test@example.com" in found or "john.doe+test@example.com" in [f.lower() for f in found]
    assert any("hello@my-site.co.uk" == f.lower() for f in found)


def test_blocked_domains_contains_socials():
    assert "tiktok.com" in BLOCKED_DOMAINS
    assert "www.instagram.com" in BLOCKED_DOMAINS
    assert "linkedin.com" in BLOCKED_DOMAINS


def test_optional_low_value_domains():
    assert "paypal.me" in OPTIONAL_LOW_VALUE_DOMAINS


def test_keyword_hints_not_empty():
    assert isinstance(KEYWORD_HINTS, tuple)
    assert "contact" in KEYWORD_HINTS


def test_placeholder_sets_not_empty():
    assert "example.com" in PLACEHOLDER_DOMAINS
    assert "nomdedomaine" in PLACEHOLDER_DOMAIN_SUBSTRINGS
    assert "extension" in PLACEHOLDER_TLDS


def test_low_value_page_hints_contains_doc_email():
    assert any("doc_email" == h for h in LOW_VALUE_PAGE_HINTS)
