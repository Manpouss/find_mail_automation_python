# enricher/constants.py
from __future__ import annotations

import re

# -----------------------------
# Email extraction
# -----------------------------
EMAIL_REGEX = re.compile(
    r"""(?ix)               # ignore case + verbose
    \b
    [a-z0-9._%+\-]+         # local part
    @
    [a-z0-9.\-]+            # domain
    \.
    [a-z]{2,}               # tld
    \b
    """
)

# Characters to strip around extracted emails/urls
STRIP_CHARS = " \t\r\n\"'()[]{}<>,;:."

# -----------------------------
# Crawling rules (public-only)
# -----------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EmailEnricher/1.0)"
}

# Internal link keywords to prioritize (contact-ish pages)
KEYWORD_HINTS = (
    "contact",
    "about",
    "privacy",
    "legal",
    "imprint",
    "terms",
    "support",
)

# Domains we do NOT crawl (low value / likely blocked / non-contact)
# These are typically social platforms or profile platforms.
BLOCKED_DOMAINS = {
    "tiktok.com", "www.tiktok.com",
    "instagram.com", "www.instagram.com",
    "facebook.com", "www.facebook.com",
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    "x.com", "www.x.com",
    "twitter.com", "www.twitter.com",
    "linkedin.com", "www.linkedin.com",
}

# Extra domains that are usually not useful for email discovery (optional)
OPTIONAL_LOW_VALUE_DOMAINS = {
    "paypal.me", "www.paypal.me",
}

# Pages that often contain example emails (docs/tutorials) rather than real contacts.
# If the crawler lands on such pages, we should avoid picking misleading example emails.
LOW_VALUE_PAGE_HINTS = (
    "doc_email",
    "adresse électronique",     # FR
    "adresse electronique",     # FR no accent
    "email valide",
    "nom d'utilisateur@",       # FR
    "username@",                # EN
    "example@",                 # EN
)

# -----------------------------
# Placeholder / example email filtering
# -----------------------------
# Domains used in documentation examples
PLACEHOLDER_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
}

# Substrings indicating obvious placeholders (e.g. utilisateur@nomdedomaine.extension)
PLACEHOLDER_DOMAIN_SUBSTRINGS = (
    "nomdedomaine",
    "domainname",
)

# Fake TLDs sometimes used in examples (literal ".extension")
PLACEHOLDER_TLDS = (
    "extension",
)
