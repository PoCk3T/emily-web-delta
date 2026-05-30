"""Check service layer."""

import logging
from typing import Optional

from app.core.extraction_backend import ExtractionBackend
from app.models.check_result import CheckResult
from app.models.url import Url

logger = logging.getLogger(__name__)


class CheckService:
    """Service layer for check operations."""

    def __init__(self, backend: ExtractionBackend):
        self.backend = backend

    async def check_url(self, url: Url) -> Optional[CheckResult]:
        """Check a URL and return the result."""
        if not url.enabled:
            return None

        try:
            result = await self.backend.extract(
                url=url.url,
                mode="markdown",
                goal=getattr(url, "goal", None),
                headers=url.headers,
                cookies=url.cookies,
            )

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
            return None
