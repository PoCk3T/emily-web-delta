"""Self-hosted extraction backend with CloakBrowser-to-HTTPX auto-fallback."""

import asyncio
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
from app.core.html_parser import extract_content, visible_text_length
from app.core.pdf_parser import extract_pdf_text, looks_like_pdf

logger = logging.getLogger(__name__)

# Minimum number of visible (tag-stripped) characters an extraction must yield
# before it is accepted as a real snapshot.
MIN_VISIBLE_CHARS = 50

# Extractions above the hard minimum but below this threshold are still
# accepted, because some monitored pages are legitimately short, but they are
# logged loudly: on a large HTML document a result this small almost always
# means the extractor collapsed the page rather than the page being small.
# See DEVOPS_GUIDELINES.md Lesson 16.
THIN_EXTRACTION_CHARS = 500

# Only warn about a thin extraction when the source document was large enough
# that a rich extraction was clearly expected.
_SUBSTANTIAL_HTML_BYTES = 20_000


def _visible_text_length(content: str) -> int:
    """Count human-visible characters, ignoring markup and whitespace."""
    return visible_text_length(content)


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
        js_required: bool = False,
    ) -> ExtractionResult:
        """Extract content from a URL, trying CloakBrowser first and falling back to httpx.

        Args:
            js_required: Set for pages that only render client-side. The plain
                httpx fallback returns an empty shell for those, so it is
                skipped and the failure is reported against CloakBrowser
                instead of being masked by a meaningless 200 response.
        """
        start_time = time.time()
        html = None
        title = "Unknown Title"
        engine_used = "cloakbrowser"
        cloak_err = None
        pdf_bytes: bytes | None = None

        # A headless browser cannot hand back PDF bytes via page.content() —
        # it either renders the built-in viewer or triggers a download — so
        # PDF URLs bypass CloakBrowser entirely and are fetched with httpx.
        expect_pdf = looks_like_pdf(url=url)

        # ─── Step 1: Primary Attempt (CloakBrowser) ───
        if self.use_cloakbrowser and not expect_pdf:
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
        if html is None and js_required and not expect_pdf:
            # Falling back to a plain fetch for a client-rendered page yields
            # an empty shell that hashes stably forever. Surface the real
            # cause instead.
            logger.error(
                f"{url} is marked js_required but CloakBrowser was unavailable "
                f"({cloak_err}); refusing to fall back to a non-JS fetch."
            )
            return ExtractionResult(
                url=url,
                status="error",
                content="",
                content_hash="",
                error=(
                    "Page requires JavaScript rendering but CloakBrowser "
                    f"was unavailable: {cloak_err}"
                ),
                metadata={"timestamp": datetime.now(UTC), "status_code": 503},
            )

        if html is None:
            engine_used = "httpx"
            try:
                # Mimic browser headers
                default_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                if expect_pdf:
                    default_headers["Accept"] = "application/pdf,*/*;q=0.8"
                if headers:
                    default_headers.update(headers)

                async with httpx.AsyncClient(
                    timeout=60.0 if expect_pdf else 30.0, follow_redirects=True
                ) as client:
                    response = await client.get(
                        url, headers=default_headers, cookies=cookies
                    )
                    response.raise_for_status()

                    if looks_like_pdf(
                        content=response.content,
                        content_type=response.headers.get("content-type"),
                        url=url,
                    ):
                        engine_used = "httpx+pdf"
                        pdf_bytes = response.content
                        title = url.rsplit("/", 1)[-1]
                    else:
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

        # ─── Step 3: Extract readable content ───
        if pdf_bytes is not None:
            # PDF path. Parsing is CPU-bound and synchronous, so it runs in a
            # worker thread to avoid stalling the event loop.
            try:
                extracted = await asyncio.to_thread(extract_pdf_text, pdf_bytes)
            except Exception as e:
                logger.error(f"PDF extraction failed for {url}: {e}")
                return ExtractionResult(
                    url=url,
                    status="error",
                    content="",
                    content_hash="",
                    error=f"PDF extraction error: {e}",
                    metadata={
                        "timestamp": datetime.now(UTC),
                        "status_code": 422,
                    },
                )
            content_type = "pdf"
            # PDF text is plain text, not markup. Running the hyperlink
            # stripper over it would corrupt legitimate "[...](...)"
            # sequences found in tariff language, so hash it as-is.
            clean_content = extracted
        else:
            content_type = "markdown"
            extracted = html
            if mode != ExtractionMode.RAW_HTML:
                extracted = await extract_content(html, "readability", schema)

            # Sanitize so that link-target churn is not reported as a change.
            from app.core.diff_engine import strip_hyperlink_targets

            clean_content = strip_hyperlink_targets(extracted)

        # ─── Step 4: Reject empty extractions ───
        # A JS-rendered page fetched without a browser returns an empty shell.
        # Storing that as a valid snapshot is the worst failure mode: the hash
        # is perfectly stable, so the URL looks healthy forever while silently
        # never being able to report a change. Fail loudly instead.
        if _visible_text_length(extracted) < MIN_VISIBLE_CHARS:
            logger.error(
                f"Extraction for {url} produced no meaningful text "
                f"(engine={engine_used}); treating as a failure."
            )
            return ExtractionResult(
                url=url,
                status="error",
                content="",
                content_hash="",
                error=(
                    "Extracted content was empty or below the minimum of "
                    f"{MIN_VISIBLE_CHARS} visible characters "
                    f"(engine={engine_used}). The page most likely requires "
                    "JavaScript rendering."
                ),
                metadata={
                    "timestamp": datetime.now(UTC),
                    "status_code": 422,
                    "engine": engine_used,
                },
            )

        # A thin extraction from a large document is the quiet version of the
        # failure above: it clears the hard minimum, so it is stored and looks
        # healthy, but it only covers a fragment of the page and is blind to
        # changes everywhere else. Accept it, but make it findable in the logs.
        visible_chars = _visible_text_length(extracted)
        if (
            content_type != "pdf"
            and visible_chars < THIN_EXTRACTION_CHARS
            and len(html or "") > _SUBSTANTIAL_HTML_BYTES
        ):
            logger.warning(
                f"Thin extraction for {url}: {visible_chars} visible chars "
                f"recovered from {len(html or '')} bytes of HTML "
                f"(engine={engine_used}). The snapshot is stored but very "
                "likely covers only a fragment of the page."
            )

        # ─── Step 5: Hash ───
        content_hash = hashlib.sha256(clean_content.encode()).hexdigest()

        return ExtractionResult(
            url=url,
            status="completed",
            content=extracted,
            content_hash=content_hash,
            metadata={
                "title": title,
                "engine": engine_used,
                "content_type": content_type,
                "load_time_ms": round(load_time, 2),
                "content_length": len(extracted),
                "timestamp": datetime.now(UTC),
            },
        )

    async def supports_structured_extraction(self) -> bool:
        return False

    async def supports_ai_judging(self) -> bool:
        return False
