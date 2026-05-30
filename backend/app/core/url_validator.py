"""URL validation utilities."""

import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Internal IP ranges to block
INTERNAL_PATTERNS = [
    r"^https?://127\.0\.0\.",
    r"^https?://10\.",
    r"^https?://192\.168\.",
    r"^https?://172\.(1[6-9]|2[0-9]|3[01])\.",
    r"^https?://localhost",
    r"^https?://0\.0\.0\.0",
    r"^https?://\[::1\]",
]


def validate_url(url: str) -> tuple[bool, str]:
    """Validate a URL for monitoring.

    Returns:
        (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    parsed = urlparse(url)

    # Scheme check
    if parsed.scheme not in ("http", "https"):
        return False, "URL must use http or https scheme"

    # Host check
    if not parsed.hostname:
        return False, "URL must have a valid hostname"

    # Block internal/private IPs
    hostname = parsed.hostname.lower()
    for pattern in INTERNAL_PATTERNS:
        if re.match(pattern, hostname, re.IGNORECASE):
            return False, "URL points to internal/private network"

    # Check for suspicious protocols
    if not re.match(r"^https?://", url, re.IGNORECASE):
        return False, "URL must start with http:// or https://"

    return True, ""


def validate_url_format(url: str) -> bool:
    """Quick format check for URL."""
    pattern = re.compile(
        r"^https?://"
        r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
        r"[A-Z]{2,63}"
        r"(?:[/?#][^\s]*)?$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))
