"""Extraction backend abstraction layer.

All backends implement this ABC so the rest of the codebase
never needs to know whether content came from Firecrawl or
self-hosted polling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExtractionMode(Enum):
    """What kind of content to extract."""

    MARKDOWN = "markdown"
    JSON_SCHEMA = "json_schema"
    MIXED = "mixed"
    RAW_HTML = "raw_html"


@dataclass
class ExtractionResult:
    """Standardized result from ANY backend."""

    url: str
    status: str  # "same", "changed", "new", "removed", "error"
    content: str
    content_hash: str
    structured_data: Optional[dict] = None
    diff_text: Optional[str] = None
    diff_json: Optional[dict] = None
    judgment: Optional[dict] = None
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


class ExtractionBackend(ABC):
    """Common interface for all extraction backends."""

    @abstractmethod
    async def extract(
        self,
        url: str,
        mode: ExtractionMode = ExtractionMode.MARKDOWN,
        schema: Optional[dict] = None,
        goal: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ) -> ExtractionResult:
        """Extract content from a URL."""
        ...

    @abstractmethod
    async def supports_structured_extraction(self) -> bool:
        """Whether this backend supports JSON-mode extraction."""
        ...

    @abstractmethod
    async def supports_ai_judging(self) -> bool:
        """Whether this backend supports AI-powered change judging."""
        ...
