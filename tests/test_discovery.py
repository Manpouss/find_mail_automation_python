# tests/test_discovery.py
from __future__ import annotations

from enricher.discovery import DiscoveryConfig, discover_external_urls_from_row


def test_discovery_prefers_bio_links_when_present():
    row = {
        "bio_links": "Check https://example.com and https://mybusiness.fr/contact",
        "bio_text": "also www.other.com",
        "description": "desc example.org",
    }
    urls, src = discover_external_urls_from_row(row, DiscoveryConfig(max_urls_per_row=2))
    assert src == "bio_links"
    assert "https://example.com" in urls
    assert "https://mybusiness.fr/contact" in urls
    assert len(urls) == 2


def test_discovery_falls_back_to_bio_text():
    row = {
        "bio_links": "",
        "bio_text": "My site is www.example.com/contact",
        "description": "",
    }
    urls, src = discover_external_urls_from_row(row)
    assert src == "bio_text"
    assert "https://www.example.com/contact" in urls


def test_discovery_falls_back_to_description():
    row = {
        "bio_links": "",
        "bio_text": "",
        "description": "Reach me at mybusiness.co.uk",
    }
    urls, src = discover_external_urls_from_row(row)
    assert src == "description"
    assert "https://mybusiness.co.uk" in urls


def test_discovery_returns_none_when_no_urls():
    row = {"bio_links": "", "bio_text": "hello world", "description": ""}
    urls, src = discover_external_urls_from_row(row)
    assert urls == []
    assert src == "none"


def test_discovery_excludes_social_and_low_value_domains():
    row = {
        "bio_links": "https://tiktok.com/@x https://paypal.me/abc https://example.com",
        "bio_text": "",
        "description": "",
    }
    urls, src = discover_external_urls_from_row(row, DiscoveryConfig(max_urls_per_row=5, exclude_low_value=True))
    assert src == "bio_links"
    assert "https://example.com" in urls
    assert all("tiktok.com" not in u for u in urls)
    assert all("paypal.me" not in u for u in urls)
