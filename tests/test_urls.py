# tests/test_urls.py
from __future__ import annotations

from enricher.urls import (
    normalize_url,
    get_domain,
    is_probable_domain,
    extract_urls_from_text,
    filter_external_urls,
)


def test_normalize_url_http():
    u = normalize_url("http://example.com/path?x=1#frag")
    assert u == "http://example.com/path"


def test_normalize_url_www():
    u = normalize_url("www.example.com/contact")
    assert u == "https://www.example.com/contact"


def test_normalize_url_naked_domain():
    u = normalize_url("example.com")
    assert u == "https://example.com"


def test_normalize_url_reject_garbage():
    assert normalize_url("not a url") == ""
    assert normalize_url("hello@world.com") == ""  # looks like email


def test_get_domain():
    assert get_domain("https://Example.com/path") == "example.com"


def test_is_probable_domain():
    assert is_probable_domain("example.com")
    assert is_probable_domain("sub.domain.co.uk")
    assert not is_probable_domain("hello world")
    assert not is_probable_domain("user@example.com")
    assert not is_probable_domain("http://example.com")


def test_extract_urls_from_text_http_www_domain():
    text = """
    Here is a link https://example.com/contact and also www.test.org.
    Another domain: my-site.co.uk and an email hello@domain.com (should not become url).
    """
    urls = extract_urls_from_text(text)
    # Should include normalized URLs
    assert "https://example.com/contact" in urls
    assert "https://www.test.org" in urls
    assert "https://my-site.co.uk" in urls
    # Ensure no email got turned into url
    assert all("@" not in u for u in urls)


def test_filter_external_urls_limits_and_excludes_social():
    urls = [
        "https://tiktok.com/@someone",
        "https://example.com",
        "www.instagram.com/someone",
        "https://paypal.me/someone",
        "https://mybusiness.fr/contact",
    ]
    filtered = filter_external_urls(urls, max_urls=2, exclude_low_value=True)
    # Social + paypal should be excluded, first two useful should remain (limited to 2)
    assert "https://example.com" in filtered
    assert "https://mybusiness.fr/contact" in filtered
    assert len(filtered) == 2
