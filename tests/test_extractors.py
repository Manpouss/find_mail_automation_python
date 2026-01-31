# tests/test_extractors.py
from __future__ import annotations

from enricher.extractors import (
    extract_emails,
    extract_emails_filtered,
    is_placeholder_email,
    enrich_row_local,
)


def test_extract_emails_normalizes_and_dedups():
    text = "Email: JOHN.DOE@Example.com, john.doe@example.com; other: a@b.com"
    emails = extract_emails(text)
    # lowercased + dedup
    assert emails.count("john.doe@example.com") == 1
    assert "a@b.com" in emails


def test_placeholder_example_domains_filtered():
    assert is_placeholder_email("someone@example.com") is True
    assert is_placeholder_email("someone@example.org") is True
    assert is_placeholder_email("someone@example.net") is True


def test_placeholder_nomdedomaine_filtered():
    assert is_placeholder_email("utilisateur@nomdedomaine.extension") is True


def test_placeholder_extension_tld_filtered():
    assert is_placeholder_email("user@domain.extension") is True


def test_extract_emails_filtered_removes_placeholders():
    text = "Example user@example.com real hello@realcompany.com"
    emails = extract_emails_filtered(text)
    assert "hello@realcompany.com" in emails
    assert all("example.com" not in e for e in emails)


def test_enrich_row_local_priority_detected_over_bio():
    bio = "contact me at bio@real.com"
    det = "detected@real.com"
    email, src, method, status, conf = enrich_row_local(bio, det)
    assert email == "detected@real.com"
    assert src == "detected_emails"
    assert status == "found"
    assert conf == "1.0"


def test_enrich_row_local_fallback_to_bio():
    bio = "contact me at bio@real.com"
    det = ""
    email, src, method, status, conf = enrich_row_local(bio, det)
    assert email == "bio@real.com"
    assert src == "bio_text"
    assert status == "found"
    assert conf == "0.8"


def test_enrich_row_local_not_found():
    email, src, method, status, conf = enrich_row_local("", "")
    assert email == ""
    assert status == "not_found"
