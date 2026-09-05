"""Tests for PDF detection and text extraction."""

import io

import pytest

from app.core.pdf_parser import extract_pdf_text, looks_like_pdf


def _blank_pdf() -> bytes:
    """Build a valid single-page PDF that contains no text at all."""
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _text_pdf(text: str) -> bytes:
    """Hand-roll a minimal PDF whose single page renders `text`.

    Written by hand rather than with a generator library so the test has no
    extra dependency beyond pypdf itself.
    """
    stream = f"BT /F1 12 Tf 20 100 Td ({text}) Tj ET".encode()

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream
        + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return bytes(out)


class TestLooksLikePdf:
    def test_detects_by_magic_bytes(self):
        assert looks_like_pdf(content=b"%PDF-1.4\n...") is True

    def test_detects_magic_bytes_with_leading_whitespace(self):
        assert looks_like_pdf(content=b"\n  %PDF-1.7 rest") is True

    def test_detects_by_content_type(self):
        assert looks_like_pdf(content_type="application/pdf") is True

    def test_detects_content_type_with_charset(self):
        assert looks_like_pdf(content_type="application/pdf; charset=binary") is True

    def test_detects_by_url_extension(self):
        assert (
            looks_like_pdf(
                url="https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-1.pdf"
            )
            is True
        )

    def test_detects_url_extension_with_query_string(self):
        assert looks_like_pdf(url="https://example.com/doc.pdf?v=2#page=3") is True

    def test_rejects_html(self):
        assert (
            looks_like_pdf(
                content=b"<!doctype html><html>",
                content_type="text/html; charset=utf-8",
                url="https://www.pge.com/tariffs/en.html",
            )
            is False
        )

    def test_rejects_pdf_substring_in_hostname(self):
        # "pdf" appearing in the path but not as the extension must not match.
        assert looks_like_pdf(url="https://example.com/pdf/viewer.html") is False

    def test_no_signals_returns_false(self):
        assert looks_like_pdf() is False


class TestExtractPdfText:
    def test_raises_on_non_pdf_bytes(self):
        with pytest.raises(RuntimeError):
            extract_pdf_text(b"<html><body>not a pdf</body></html>")

    def test_raises_when_no_extractable_text(self):
        """A blank/scanned PDF must fail loudly rather than hash empty text.

        Silently returning "" would make every scanned document hash
        identically and mask real changes.
        """
        with pytest.raises(RuntimeError, match="no extractable text"):
            extract_pdf_text(_blank_pdf())

    def test_extracts_text_and_is_deterministic(self):
        """Same bytes must yield identical text, else every poll is a false diff."""
        data = _text_pdf("ELECTRIC SCHEDULE E-1")
        first = extract_pdf_text(data)
        second = extract_pdf_text(data)
        assert "ELECTRIC SCHEDULE E-1" in first
        assert first == second

    def test_normalizes_trailing_whitespace(self):
        """Trailing spaces/blank-line runs must not leak into the hash."""
        text = extract_pdf_text(_text_pdf("Sheet 1"))
        assert not any(line != line.rstrip() for line in text.split("\n"))
        assert "\n\n\n" not in text
