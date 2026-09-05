"""PDF text extraction for the self-hosted backend.

Several monitored sources (notably the PG&E tariff book) publish their
canonical documents as PDFs rather than HTML. Feeding raw PDF bytes through
the readability/lxml HTML pipeline raises
``ValueError: All strings must be XML compatible`` and the URL is recorded as
a permanent failure, so PDFs need their own extraction path.

Extraction is intentionally deterministic: the same PDF bytes must always
produce the same text, otherwise every poll would register as a spurious
content change.
"""

import io
import logging
import re

logger = logging.getLogger(__name__)

# Byte signature every PDF file starts with (allowing for leading junk that
# some generators emit before the header).
PDF_MAGIC = b"%PDF-"

# Content-Type values that indicate a PDF payload.
PDF_CONTENT_TYPES = (
    "application/pdf",
    "application/x-pdf",
    "application/acrobat",
    "applications/vnd.pdf",
    "text/pdf",
    "text/x-pdf",
)


def looks_like_pdf(
    content: bytes | None = None,
    content_type: str | None = None,
    url: str | None = None,
) -> bool:
    """Best-effort detection of a PDF payload.

    Checks are ordered from most to least reliable: magic bytes beat the
    declared Content-Type, which beats the URL extension.
    """
    # Some servers prepend whitespace/BOM before the header.
    if content and content[:1024].lstrip()[: len(PDF_MAGIC)] == PDF_MAGIC:
        return True

    if content_type:
        base = content_type.split(";", 1)[0].strip().lower()
        if base in PDF_CONTENT_TYPES:
            return True

    if url:
        path = url.split("?", 1)[0].split("#", 1)[0]
        if path.lower().endswith(".pdf"):
            return True

    return False


def _normalize_whitespace(text: str) -> str:
    """Collapse extraction noise that would otherwise look like a diff.

    pypdf can emit trailing spaces and variable blank-line runs depending on
    internal glyph ordering. Normalizing keeps the content hash stable so we
    only alert on genuine document changes.
    """
    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing whitespace on each line.
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    # Collapse 3+ blank lines down to a maximum of two.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(data: bytes, max_pages: int | None = 200) -> str:
    """Extract plain text from PDF bytes.

    Args:
        data: Raw PDF file bytes.
        max_pages: Safety cap so a pathologically large document cannot stall
            a Celery worker. ``None`` disables the cap.

    Returns:
        Normalized plain text.

    Raises:
        RuntimeError: If pypdf is unavailable or the PDF cannot be parsed.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency is pinned
        raise RuntimeError(
            "pypdf is not installed; cannot extract PDF content"
        ) from exc

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise RuntimeError(f"Could not parse PDF: {exc}") from exc

    if getattr(reader, "is_encrypted", False):
        # Many published PDFs are "encrypted" with an empty owner password,
        # which pypdf can open transparently.
        try:
            reader.decrypt("")
        except Exception as exc:
            raise RuntimeError(f"PDF is password protected: {exc}") from exc

    pages = reader.pages
    total_pages = len(pages)
    if max_pages is not None and total_pages > max_pages:
        logger.warning(
            "PDF has %s pages; truncating extraction to the first %s.",
            total_pages,
            max_pages,
        )
        pages = pages[:max_pages]

    chunks: list[str] = []
    for index, page in enumerate(pages):
        try:
            chunks.append(page.extract_text() or "")
        except Exception as exc:
            # A single malformed page should not void the whole document.
            logger.warning("Failed to extract page %s of PDF: %s", index + 1, exc)
            chunks.append("")

    text = _normalize_whitespace("\n\n".join(chunks))

    if not text:
        raise RuntimeError(
            "PDF contained no extractable text "
            f"({total_pages} page(s); likely a scanned image requiring OCR)"
        )

    logger.info(
        "Extracted %s characters from %s-page PDF.", len(text), total_pages
    )
    return text
