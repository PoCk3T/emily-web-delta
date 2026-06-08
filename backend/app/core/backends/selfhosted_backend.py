"""Self-hosted extraction backend with CloakBrowser-to-HTTPX auto-fallback."""

import hashlib
import logging
import re
import time
from datetime import UTC, datetime

import httpx

from app.core.extraction_backend import (
    ExtractionBackend,
    ExtractionMode,
    ExtractionResult,
)
from app.core.html_parser import extract_content

logger = logging.getLogger(__name__)


class SelfHostedBackend(ExtractionBackend):
    """Fallback backend: attempts CloakBrowser first, falls back to httpx if needed."""

    def __init__(self, use_cloakbrowser: bool = True):
        self.use_cloakbrowser = use_cloakbrowser

    async def extract(
        self,
        url: str,
        mode: ExtractionMode = ExtractionMode.MARKDOWN,
        schema: dict | None = None,
        goal: str | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
    ) -> ExtractionResult:
        """Extract content from a URL, trying CloakBrowser first and falling back to httpx."""
        start_time = time.time()
        html = None
        title = "Unknown Title"
        engine_used = "cloakbrowser"
        cloak_err = None

        # ─── Step 1: Primary Attempt (CloakBrowser) ───
        if self.use_cloakbrowser:
            try:
                from cloakbrowser import launch_async

                logger.info(f"Attempting stealth fetch of {url} via CloakBrowser...")
                # Launch stealth Chromium in headless mode, with humanization enabled
                browser = await launch_async(
                    headless=True, humanize=True, args=["--disable-gpu"]
                )
                try:
                    page = await browser.new_page()
                    if headers:
                        await page.set_extra_http_headers(headers)
                    if cookies:
                        for cookie in cookies:
                            await page.context.add_cookie(cookie)

                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    html = await page.content()
                    title = await page.title()
                finally:
                    await browser.close()

            except Exception as e:
                cloak_err = e
                logger.warning(
                    f"CloakBrowser failed or is not available for {url}. "
                    f"Error: {e}. Falling back to standard HTTPX fetch..."
                )

        # ─── Step 2: Fallback Attempt (HTTPX) ───
        if html is None:
            engine_used = "httpx"
            try:
                # Mimic browser headers
                default_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                if headers:
                    default_headers.update(headers)

                async with httpx.AsyncClient(
                    timeout=30.0, follow_redirects=True
                ) as client:
                    response = await client.get(
                        url, headers=default_headers, cookies=cookies
                    )
                    response.raise_for_status()
                    html = response.text

                    # Simple title extraction from raw HTML
                    title_match = re.search(
                        r"<title>(.*?)</title>", html, re.IGNORECASE
                    )
                    if title_match:
                        title = title_match.group(1).strip()
            except Exception as e:
                logger.error(
                    f"Both CloakBrowser and HTTPX failed for {url}. Error: {e}"
                )
                return ExtractionResult(
                    url=url,
                    status="error",
                    content="",
                    content_hash="",
                    error=f"CloakBrowser error: {cloak_err} | HTTPX error: {e}",
                    metadata={
                        "timestamp": datetime.now(UTC),
                        "status_code": getattr(
                            getattr(e, "response", None), "status_code", 500
                        ),
                    },
                )

        load_time = (time.time() - start_time) * 1000

        # Step 3: Extract readable content
        extracted = html
        if mode != ExtractionMode.RAW_HTML:
            extracted = await extract_content(html, "readability", schema)

        # Step 4: Hash (using sanitized content so link changes are ignored)
        from app.core.diff_engine import strip_hyperlink_targets

        clean_content = strip_hyperlink_targets(extracted)
        content_hash = hashlib.sha256(clean_content.encode()).hexdigest()

        return ExtractionResult(
            url=url,
            status="completed",
            content=extracted,
            content_hash=content_hash,
            metadata={
                "title": title,
                "engine": engine_used,
                "load_time_ms": round(load_time, 2),
                "content_length": len(extracted),
                "timestamp": datetime.now(UTC),
            },
        )

    async def supports_structured_extraction(self) -> bool:
        return False

    async def supports_ai_judging(self) -> bool:
        return False
