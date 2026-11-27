"""Structural URL feature extraction without network requests."""

from urllib.parse import urlparse
import re

SUSPICIOUS_WORDS = (
    "secure", "account", "login", "signin", "bank", "verify",
    "update", "password", "confirm", "payment", "wallet",
)


def extract_url_features(url: str) -> dict:
    """Extract transparent lexical features; never resolve or contact the URL."""
    if not isinstance(url, str):
        return {}

    value = url.strip()
    parsed = urlparse(value if "://" in value else "//" + value)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""

    digits = sum(char.isdigit() for char in value)
    letters = sum(char.isalpha() for char in value)

    return {
        "url_length": len(value),
        "hostname_length": len(host),
        "path_length": len(path),
        "digit_count": digits,
        "letter_count": letters,
        "dot_count": value.count("."),
        "hyphen_count": value.count("-"),
        "underscore_count": value.count("_"),
        "slash_count": value.count("/"),
        "at_count": value.count("@"),
        "question_count": value.count("?"),
        "equals_count": value.count("="),
        "percent_count": value.count("%"),
        "has_ip_host": bool(re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", host)),
        "has_https": parsed.scheme.lower() == "https",
        "suspicious_word_count": sum(word in value.lower() for word in SUSPICIOUS_WORDS),
        "subdomain_count": max(host.count(".") - 1, 0) if host else 0,
    }
