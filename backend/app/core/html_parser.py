"""HTML content extraction for self-hosted fallback."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


async def extract_content(
    html: str,
    extraction_method: str = "readability",
    schema: Optional[dict] = None,
) -> str:
    """Extract readable content from HTML."""
    if extraction_method == "readability":
        return _extract_readability(html)
    elif extraction_method == "trafilatura":
        return _extract_trafilatura(html)
    elif extraction_method == "custom_xpath" and schema:
        return _extract_xpath(html, schema)
    else:
        return html


def _extract_readability(html: str) -> str:
    """Extract readable content using readability algorithm."""
    try:
        from readability import readability
        doc = readability.Document(html)
        return doc.summary()
    except ImportError:
        logger.warning("readability not installed, returning raw HTML")
        return html


def _extract_trafilatura(html: str) -> str:
    """Extract content using trafilatura."""
    try:
        import trafilatura
        result = trafilatura.extract(html)
        return result or html
    except ImportError:
        logger.warning("trafilatura not installed, falling back to readability")
        return _extract_readability(html)


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
