"""URL polling scheduler for self-hosted fallback."""

import hashlib
import logging

from app.core.extraction_backend import ExtractionBackend, ExtractionMode
from app.models.check_result import CheckResult
from app.models.url import Url

logger = logging.getLogger(__name__)


class Scheduler:
    """Scheduler that polls URLs on a configurable interval."""

    def __init__(self, backend: ExtractionBackend):
        self.backend = backend
        self._running = False

    async def poll_urls(self, urls: list[Url]) -> list[CheckResult]:
        """Poll a batch of URLs and return check results."""
        results = []
        for url in urls:
            try:
                result = await self._poll_url(url)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to poll URL {url.id}: {e}")
                results.append(
                    CheckResult(
                        url_id=url.id,
                        status="error",
                        error_message=str(e),
                    )
                )
        return results

    async def _poll_url(self, url: Url) -> CheckResult:
        """Poll a single URL and compute the check result."""
        logger.info(f"Polling URL: {url.url}")

        # Extract content via backend
        result = await self.backend.extract(
            url=url.url,
            mode=ExtractionMode.MARKDOWN,
            goal=url.goal if hasattr(url, "goal") else None,
        )

        # Compute hash (ignoring raw hyperlink changes)
        from app.core.diff_engine import strip_hyperlink_targets

        clean_content = strip_hyperlink_targets(result.content)
        content_hash = hashlib.sha256(clean_content.encode()).hexdigest()

        # Compare with last snapshot
        status = "same"
        if url.last_hash and content_hash == url.last_hash:
            status = "same"
        elif url.last_hash is None:
            status = "new"
        else:
            status = "changed"

        # Create check result
        check = CheckResult(
            url_id=url.id,
            backend="selfhosted",
            status=status,
            diff_text=result.diff_text,
            diff_json=result.diff_json,
            snapshot_json=result.structured_data,
            content_hash=content_hash,
            judgment=result.judgment,
        )

        # Update URL last_hash
        url.last_hash = content_hash
        url.last_checked = result.metadata.get("timestamp")

        logger.info(f"URL {url.url}: {status}")
        return check
