# tests/test_crawler.py
from __future__ import annotations

import types

import enricher.crawler as crawler


class FakeResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


def test_extract_internal_links_filters_and_builds_absolute():
    base = "https://example.com"
    html = """
    <a href="/contact">Contact</a>
    <a href="/privacy">Privacy</a>
    <a href="https://example.com/about">About</a>
    <a href="https://other.com/contact">Other</a>
    <a href="/random">Random</a>
    """
    links = crawler.extract_internal_links(base, html, max_links=10)
    # Only contact/privacy/about, internal only
    assert "https://example.com/contact" in links
    assert "https://example.com/privacy" in links
    assert "https://example.com/about" in links
    assert all("other.com" not in u for u in links)


def test_crawl_for_email_found_on_homepage(monkeypatch):
    def fake_get(url, headers=None, timeout=None, allow_redirects=True):
        assert "User-Agent" in (headers or {})
        return FakeResponse(200, "<html>Reach us at hello@realcompany.com</html>")

    monkeypatch.setattr(crawler.requests, "get", fake_get)

    email, src, status, conf = crawler.crawl_for_email("https://example.com", timeout=5, max_pages=3)
    assert status == "found"
    assert email == "hello@realcompany.com"
    assert src == "https://example.com"
    assert conf == "0.6"


def test_crawl_for_email_blocked(monkeypatch):
    def fake_get(url, headers=None, timeout=None, allow_redirects=True):
        return FakeResponse(403, "")

    monkeypatch.setattr(crawler.requests, "get", fake_get)

    email, src, status, conf = crawler.crawl_for_email("https://example.com", timeout=5, max_pages=3)
    assert status == "blocked"
    assert email == ""
    assert src == ""
    assert conf == ""


def test_crawl_for_email_finds_on_internal_contact(monkeypatch):
    pages = {
        "https://example.com": FakeResponse(
            200,
            """
            <html>
              <a href="/contact">contact</a>
              <a href="/privacy">privacy</a>
              no email here
            </html>
            """,
        ),
        "https://example.com/contact": FakeResponse(
            200,
            "<html>Contact us: team@realcompany.com</html>",
        ),
        "https://example.com/privacy": FakeResponse(
            200,
            "<html>privacy policy</html>",
        ),
    }

    def fake_get(url, headers=None, timeout=None, allow_redirects=True):
        return pages.get(url, FakeResponse(404, ""))

    monkeypatch.setattr(crawler.requests, "get", fake_get)

    email, src, status, conf = crawler.crawl_for_email("https://example.com", timeout=5, max_pages=3)
    assert status == "found"
    assert email == "team@realcompany.com"
    assert src == "https://example.com/contact"
    assert conf == "0.6"


def test_crawl_for_email_low_value_page_ignored(monkeypatch):
    # Page contains "doc_email" hint and an example email; should be ignored -> not_found
    def fake_get(url, headers=None, timeout=None, allow_redirects=True):
        return FakeResponse(200, "<html>doc_email example user@example.com</html>")

    monkeypatch.setattr(crawler.requests, "get", fake_get)

    email, src, status, conf = crawler.crawl_for_email("https://example.com/doc_email", timeout=5, max_pages=1)
    assert status == "not_found"
    assert email == ""
