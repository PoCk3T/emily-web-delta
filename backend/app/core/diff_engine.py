"""Diff computation engine for self-hosted fallback."""

import difflib
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Result of a diff computation."""

    unified_diff: str = ""
    semantic_changes: list[dict] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0
    diff_size: int = 0


def strip_hyperlink_targets(content: str) -> str:
    """Strips underlying hyperlink targets, keeping only the visible anchor text.

    Acts on both HTML anchor tags and Markdown links:
      - Markdown: [OpenAI Privacy Policy](https://openai.com/privacy) -> OpenAI Privacy Policy
      - HTML: <a href="https://openai.com/privacy">Privacy Policy</a> -> Privacy Policy
    """
    if not content:
        return ""

    # 1. HTML anchor tags: replace <a href="...">text</a> with text
    content = re.sub(
        r"<a\s+[^>]*>(.*?)</a>", r"\1", content, flags=re.IGNORECASE | re.DOTALL
    )

    # 2. Markdown link syntax: replace [text](url) with text
    content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)

    return content


async def compute_diff(
    previous_text: str,
    current_text: str,
) -> DiffResult:
    """Compute a diff between two text snapshots."""
    # Strip hyperlink targets to ignore raw link differences
    clean_prev = strip_hyperlink_targets(previous_text)
    clean_curr = strip_hyperlink_targets(current_text)

    # Line-level unified diff
    line_diff = list(
        difflib.unified_diff(
            clean_prev.splitlines(),
            clean_curr.splitlines(),
            lineterm="",
        )
    )

    unified_diff = "\n".join(line_diff)
    lines_added = len(
        [
            line
            for line in line_diff
            if line.startswith("+") and not line.startswith("+++")
        ]
    )
    lines_removed = len(
        [
            line
            for line in line_diff
            if line.startswith("-") and not line.startswith("---")
        ]
    )

    # Semantic extraction
    semantic_changes = await extract_semantic_changes(clean_prev, clean_curr)

    return DiffResult(
        unified_diff=unified_diff,
        semantic_changes=semantic_changes,
        lines_added=lines_added,
        lines_removed=lines_removed,
        diff_size=len(unified_diff),
    )


async def extract_semantic_changes(
    previous: str,
    current: str,
) -> list[dict]:
    """Extract semantic changes (prices, dates, stock levels)."""
    changes = []

    # Price patterns
    price_pattern = re.compile(r"\$[\d,]+(?:\.\d{2})?")
    prev_prices = set(price_pattern.findall(previous))
    curr_prices = set(price_pattern.findall(current))
    if prev_prices != curr_prices:
        changes.append(
            {
                "type": "price",
                "removed": list(prev_prices - curr_prices),
                "added": list(curr_prices - prev_prices),
            }
        )

    # Date patterns
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    prev_dates = set(date_pattern.findall(previous))
    curr_dates = set(date_pattern.findall(current))
    if prev_dates != curr_dates:
        changes.append(
            {
                "type": "date",
                "removed": list(prev_dates - curr_dates),
                "added": list(curr_dates - prev_dates),
            }
        )

    return changes
