"""Firecrawl extraction backend implementation."""

import hashlib
import logging
import time
from datetime import UTC, datetime

from app.core.extraction_backend import (
    ExtractionBackend,
    ExtractionMode,
    ExtractionResult,
)
from app.services.firecrawl_service import FirecrawlService

logger = logging.getLogger(__name__)


class FirecrawlBackend(ExtractionBackend):
    """Primary backend: uses Firecrawl API."""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.service = FirecrawlService()

    async def extract(
        self,
        url: str,
        mode: ExtractionMode = ExtractionMode.MARKDOWN,
        schema: dict | None = None,
        goal: str | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
    ) -> ExtractionResult:
        """Extract content from a URL using Firecrawl Scrape API."""
        start_time = time.time()

        formats = ["markdown"]
        if mode == ExtractionMode.JSON_SCHEMA and schema:
            formats = ["json"]

        try:
            data = await self.service.scrape(url, formats=formats)
        except Exception as e:
            logger.error(f"Firecrawl scrape failed for {url}: {e}")
            return ExtractionResult(
                url=url,
                status="error",
                content="",
                content_hash="",
                error=str(e),
                metadata={
                    "timestamp": datetime.now(UTC),
                    "status_code": 500,
                },
            )

        load_time = (time.time() - start_time) * 1000

        # Map Firecrawl response to ExtractionResult
        scrape_data = data.get("data", {})
        content = scrape_data.get("markdown", "")
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        return ExtractionResult(
            url=url,
            status="completed",
            content=content,
            content_hash=content_hash,
            structured_data=scrape_data.get("json"),
            metadata={
                "title": scrape_data.get("metadata", {}).get("title", "Unknown Title"),
                "status_code": 200,
                "load_time_ms": round(load_time, 2),
                "timestamp": datetime.now(UTC),
            },
        )

    async def supports_structured_extraction(self) -> bool:
        return True

    async def supports_ai_judging(self) -> bool:
        return True
