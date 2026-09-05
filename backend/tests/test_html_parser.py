"""Tests for the HTML extraction strategy.

Guards DEVOPS_GUIDELINES.md Lesson 16: readability alone collapses modern
component-rendered marketing pages down to a few hundred characters. The
resulting snapshot hashes stably, so the URL looks perfectly healthy while
being blind to any change outside the fragment that survived extraction.
"""

import pytest

from app.core.html_parser import (
    _extract_readability,
    _extract_trafilatura,
    extract_content,
    visible_text_length,
)

# A page shaped like a modern marketing site: a large decorative shell (nav,
# scripts, footer) wrapped around the real body copy. readability latches onto
# the wrong container here, which is precisely the production failure.
_BODY_PARAGRAPHS = "".join(
    f"<p>Pricing detail paragraph number {i}. "
    f"Integrated per-transaction pricing with no setup fees, no monthly fees, "
    f"and no hidden fees for section {i} of the pricing table.</p>"
    for i in range(40)
)

COMPONENT_RENDERED_PAGE = f"""
<html>
  <head>
    <title>Pricing</title>
    <script>{"var padding = 'x';" * 500}</script>
    <style>{".cls {{ color: red; }}" * 200}</style>
  </head>
  <body>
    <nav class="Header"><a href="/a">A</a><a href="/b">B</a></nav>
    <div class="Copy__body"><p>Short teaser sentence that readability loves.</p></div>
    <main>
      <section class="PricingTable">{_BODY_PARAGRAPHS}</section>
    </main>
    <footer><a href="/z">Z</a></footer>
  </body>
</html>
"""


class TestVisibleTextLength:
    def test_counts_plain_text(self):
        assert visible_text_length("hello world") == 11

    def test_ignores_markup(self):
        assert visible_text_length("<p><b>hi</b></p>") == 2

    def test_ignores_script_and_style_bodies(self):
        html = (
            "<html><head><style>body{color:red}</style>"
            "<script>var x = 'a very long string of javascript';</script>"
            "</head><body>ok</body></html>"
        )
        assert visible_text_length(html) == 2

    def test_handles_none_and_empty(self):
        assert visible_text_length("") == 0
        assert visible_text_length(None) == 0


class TestExtractionQuality:
    @pytest.mark.asyncio
    async def test_recovers_body_copy_from_component_rendered_page(self):
        """The default strategy must recover the real body, not a teaser."""
        extracted = await extract_content(COMPONENT_RENDERED_PAGE)
        length = visible_text_length(extracted)

        # The body copy is several thousand characters; a fragment is ~50.
        assert length > 2000, (
            f"Only recovered {length} visible chars. The extractor collapsed "
            "the page to a fragment (Lesson 16 regression)."
        )
        assert "paragraph number 39" in extracted

    @pytest.mark.asyncio
    async def test_beats_readability_alone_on_this_shape(self):
        """Documents the concrete defect the strategy exists to fix."""
        strategy = visible_text_length(await extract_content(COMPONENT_RENDERED_PAGE))
        readability_only = visible_text_length(
            await extract_content(COMPONENT_RENDERED_PAGE, "readability_only")
        )
        assert strategy >= readability_only

    @pytest.mark.asyncio
    async def test_short_page_still_extracts(self):
        """Genuinely short pages must not be broken by the new strategy."""
        html = (
            "<html><body><article><h1>Notice</h1>"
            "<p>This service will be discontinued on 1 January.</p>"
            "</article></body></html>"
        )
        extracted = await extract_content(html)
        assert "discontinued" in extracted

    @pytest.mark.asyncio
    async def test_empty_html_does_not_crash(self):
        assert await extract_content("") == ""

    @pytest.mark.asyncio
    async def test_garbage_input_does_not_raise(self):
        result = await extract_content("<<<not really html>>>")
        assert isinstance(result, str)

    def test_trafilatura_returns_empty_not_raw_html_when_isolated(self):
        """Isolated mode must not mask failure by echoing the input back."""
        assert _extract_trafilatura("<html><body></body></html>", _fallback=False) == ""

    def test_readability_never_raises(self):
        assert isinstance(_extract_readability("<html>"), str)


class TestExtractionMethods:
    @pytest.mark.asyncio
    async def test_raw_passthrough_for_unknown_method(self):
        html = "<html><body>hi</body></html>"
        assert await extract_content(html, "something_else") == html

    @pytest.mark.asyncio
    async def test_custom_xpath(self):
        html = "<html><body><h1>Title</h1></body></html>"
        out = await extract_content(html, "custom_xpath", {"heading": "//h1"})
        assert "Title" in out
