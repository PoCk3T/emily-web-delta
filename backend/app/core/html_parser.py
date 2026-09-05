"""HTML content extraction for self-hosted fallback.

Extraction quality directly determines monitoring quality. An extractor that
silently returns a fragment of the page produces a snapshot that hashes
stably, looks healthy forever, and can never report a change outside that
fragment. See DEVOPS_GUIDELINES.md Lesson 16.

The default ``"readability"`` method is therefore a *strategy*, not a single
library: it runs trafilatura and readability and keeps whichever recovers more
visible text. On modern component-rendered marketing pages (Stripe pricing,
for example) readability alone collapses a ~1 MB document down to a couple of
hundred characters, while trafilatura recovers the full body copy.
"""

import logging
import re

logger = logging.getLogger(__name__)

# A page that yields fewer than this many visible characters is treated as a
# suspect extraction and triggers a cross-check against the other engine.
_SUSPECT_VISIBLE_CHARS = 1000

_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def visible_text_length(content: str | None) -> int:
    """Count human-visible characters, ignoring markup, scripts and styles."""
    if not content:
        return 0
    stripped = _SCRIPT_STYLE_RE.sub(" ", content)
    stripped = _TAG_RE.sub(" ", stripped)
    return len(_WS_RE.sub(" ", stripped).strip())


async def extract_content(
    html: str,
    extraction_method: str = "readability",
    schema: dict | None = None,
) -> str:
    """Extract readable content from HTML."""
    if extraction_method == "readability":
        return _extract_best_effort(html)
    elif extraction_method == "readability_only":
        return _extract_readability(html)
    elif extraction_method == "trafilatura":
        return _extract_trafilatura(html)
    elif extraction_method == "custom_xpath" and schema:
        return _extract_xpath(html, schema)
    else:
        return html


def _extract_best_effort(html: str) -> str:
    """Run both extractors and keep the one that recovers the most text.

    Trafilatura is tried first because it handles component-rendered markup far
    better. Readability is still consulted whenever trafilatura comes back
    empty or suspiciously short, so pages where readability genuinely wins are
    not regressed.
    """
    if not html:
        return html

    trafi = _extract_trafilatura(html, _fallback=False)
    trafi_len = visible_text_length(trafi)

    # A healthy trafilatura extraction is accepted immediately.
    if trafi_len >= _SUSPECT_VISIBLE_CHARS:
        return trafi

    read = _extract_readability(html)
    read_len = visible_text_length(read)

    if trafi_len == 0 and read_len == 0:
        # Both engines failed. Return raw HTML and let the caller's minimum
        # visible-character guard decide whether this is a usable snapshot.
        logger.warning("Both trafilatura and readability extracted no text.")
        return html

    if read_len > trafi_len:
        return read
    return trafi


def _extract_readability(html: str) -> str:
    """Extract readable content using the readability algorithm."""
    try:
        from readability import readability

        doc = readability.Document(html)
        return doc.summary()
    except ImportError:
        logger.warning("readability not installed, returning raw HTML")
        return html
    except Exception as e:
        logger.warning(f"readability extraction failed: {e}")
        return ""


def _extract_trafilatura(html: str, _fallback: bool = True) -> str:
    """Extract content using trafilatura."""
    try:
        import trafilatura

        result = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
        )
        if result:
            return result
        return html if _fallback else ""
    except ImportError:
        logger.warning("trafilatura not installed, falling back to readability")
        return _extract_readability(html) if _fallback else ""
    except Exception as e:
        logger.warning(f"trafilatura extraction failed: {e}")
        return _extract_readability(html) if _fallback else ""


def _extract_xpath(html: str, schema: dict) -> str:
    """Extract content using custom XPath/CSS selectors."""
    from lxml import html as lxml_html

    tree = lxml_html.fromstring(html)
    extracted = {}

    for key, selector in schema.items():
        try:
            elements = tree.xpath(selector)
            extracted[key] = [e.text_content().strip() for e in elements if e.text_content()]
        except Exception as e:
            logger.warning(f"XPath extraction failed for {key}: {e}")

    return str(extracted)
