"""Extraction backend implementations."""

from app.core.backends.firecrawl_backend import FirecrawlBackend
from app.core.backends.selfhosted_backend import SelfHostedBackend

__all__ = ["FirecrawlBackend", "SelfHostedBackend"]
