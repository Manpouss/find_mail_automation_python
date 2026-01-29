import re

EMAIL_REGEX = re.compile(
    r"""(?ix)\b[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}\b"""
)

STRIP_CHARS = " \t\r\n\"'()[]{}<>,;:."

# "Social / platforms" excluded from external crawling (Option A)
BLOCKED_DOMAINS = {
    "tiktok.com", "www.tiktok.com",
    "instagram.com", "www.instagram.com",
    "facebook.com", "www.facebook.com",
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    "x.com", "www.x.com",
    "twitter.com", "www.twitter.com",
    "linkedin.com", "www.linkedin.com",
}

# A few extra “low ROI / not contact” domains you may want to exclude (optional)
OPTIONAL_LOW_VALUE_DOMAINS = {
    "paypal.me", "www.paypal.me",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EmailEnricher/1.0)"
}

KEYWORD_HINTS = ("contact", "about", "privacy", "legal", "imprint", "terms", "support")

# Placeholder / example email patterns (to avoid false positives)
PLACEHOLDER_DOMAIN_SUBSTRINGS = (
    "nomdedomaine",  # e.g. utilisateur@nomdedomaine.extension
)

PLACEHOLDER_TLDS = (
    "extension",     # literal ".extension" is a placeholder
)

PLACEHOLDER_DOMAINS = {
    "example.com", "example.org", "example.net",
}
