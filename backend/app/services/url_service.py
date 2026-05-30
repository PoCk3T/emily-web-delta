"""URL service layer."""

import logging
from typing import Optional

from app.core.extraction_backend import ExtractionBackend, ExtractionMode
from app.core.scheduler import Scheduler
from app.models.url import Url
from app.models.check_result import CheckResult

logger = logging.getLogger(__name__)


class UrlService:
    """Service layer for URL operations."""

    def __init__(self, backend: ExtractionBackend):
        self.backend = backend
        self.scheduler = Scheduler(backend)

    async def check_url(self, url: Url) -> Optional[CheckResult]:
        """Check a URL and return the result."""
        if not url.enabled:
            logger.info(f"URL {url.url} is disabled, skipping")
            return None

        try:
            result = await self.backend.extract(
                url=url.url,
                mode=ExtractionMode.MARKDOWN,
                goal=getattr(url, "goal", None),
                headers=url.headers,
                cookies=url.cookies,
            )

            # Update URL state
            url.last_checked = result.metadata.get("timestamp")
            url.last_hash = result.content_hash

            # Create check result
            check = CheckResult(
                url_id=url.id,
                backend=url.backend,
                status=result.status,
                is_meaningful=result.judgment.get("meaningful", False) if result.judgment else False,
                judgment=result.judgment,
                diff_text=result.diff_text,
                diff_json=result.diff_json,
                snapshot_json=result.structured_data,
                content_hash=result.content_hash,
            )

            return check

        except Exception as e:
            logger.error(f"Failed to check URL {url.url}: {e}")
            url.last_checked = None
            return None

    async def bulk_check(self, urls: list[Url]) -> list[CheckResult]:
        """Check multiple URLs."""
        results = await self.scheduler.poll_urls(urls)
        return results
