"""Tests for the self-hosted extraction backend."""

import pytest

from app.core.backends.selfhosted_backend import (
    MIN_VISIBLE_CHARS,
    _visible_text_length,
)


class TestVisibleTextLength:
    def test_counts_plain_text(self):
        assert _visible_text_length("hello world") == 11

    def test_ignores_markup(self):
        assert _visible_text_length("<p><b>hi</b></p>") == 2

    def test_ignores_script_and_style_bodies(self):
        html = (
            "<html><head><style>body{color:red}</style>"
            "<script>var x = 'a very long string of javascript';</script>"
            "</head><body>ok</body></html>"
        )
        assert _visible_text_length(html) == 2

    def test_empty_spa_shell_is_below_threshold(self):
        """The exact shape returned by a JS-only page fetched over httpx."""
        shell = (
            '<body id="readabilityBody">\n    \n\n    \n    \n\n    \n'
            '<p id="ember-basic-dropdown-wormhole"></p>\n\n    \n  </body>\n'
        )
        assert _visible_text_length(shell) < MIN_VISIBLE_CHARS

    def test_handles_none_and_empty(self):
        assert _visible_text_length("") == 0
        assert _visible_text_length(None) == 0


@pytest.mark.asyncio
async def test_empty_extraction_is_reported_as_error(monkeypatch):
    """An empty render must fail loudly, not be stored as a stable snapshot.

    Storing an empty shell is the most dangerous outcome: its hash never
    changes, so the URL appears healthy while being incapable of ever
    reporting a real change.
    """
    from app.core.backends import selfhosted_backend as mod

    class _Resp:
        status_code = 200
        headers = {"content-type": "text/html; charset=utf-8"}
        content = b"<html><body><div id='app'></div></body></html>"
        text = "<html><body><div id='app'></div></body></html>"

        def raise_for_status(self):
            return None

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            return _Resp()

    monkeypatch.setattr(mod.httpx, "AsyncClient", _Client)

    backend = mod.SelfHostedBackend(use_cloakbrowser=False)
    result = await backend.extract("https://example.com/spa")

    assert result.status == "error"
    assert result.content_hash == ""
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_pdf_url_skips_cloakbrowser_and_extracts_text(monkeypatch):
    """PDF URLs must take the httpx+pypdf path, not the browser path."""
    from app.core.backends import selfhosted_backend as mod
    from tests.test_pdf_parser import _text_pdf

    pdf_bytes = _text_pdf(
        "ELECTRIC SCHEDULE E-1 RESIDENTIAL SERVICES - Pacific Gas and "
        "Electric Company - Revised Cal. P.U.C. Sheet No. 61362-E"
    )

    class _Resp:
        status_code = 200
        headers = {"content-type": "application/pdf"}
        content = pdf_bytes
        text = "should not be used"

        def raise_for_status(self):
            return None

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            return _Resp()

    monkeypatch.setattr(mod.httpx, "AsyncClient", _Client)

    def _boom(*a, **k):  # pragma: no cover - must never run for a PDF
        raise AssertionError("CloakBrowser must not be used for PDF URLs")

    monkeypatch.setattr(mod, "extract_content", _boom)

    backend = mod.SelfHostedBackend(use_cloakbrowser=True)
    result = await backend.extract(
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-1.pdf"
    )

    assert result.status == "completed"
    assert result.metadata["content_type"] == "pdf"
    assert result.metadata["engine"] == "httpx+pdf"
    assert "ELECTRIC SCHEDULE E-1" in result.content
    assert result.content_hash
