"""Diff computation engine for self-hosted fallback."""

import difflib
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Result of a diff computation."""

    unified_diff: str = ""
    semantic_changes: list[dict] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0
    diff_size: int = 0


async def compute_diff(
    previous_text: str,
    current_text: str,
) -> DiffResult:
    """Compute a diff between two text snapshots."""
    # Line-level unified diff
    line_diff = list(
        difflib.unified_diff(
            previous_text.splitlines(),
            current_text.splitlines(),
            lineterm="",
        )
    )

    unified_diff = "\n".join(line_diff)
    lines_added = len([l for l in line_diff if l.startswith("+") and not l.startswith("+++")])
    lines_removed = len([l for l in line_diff if l.startswith("-") and not l.startswith("---")])

    # Semantic extraction
    semantic_changes = await extract_semantic_changes(previous_text, current_text)

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
        changes.append({
            "type": "price",
            "removed": list(prev_prices - curr_prices),
            "added": list(curr_prices - prev_prices),
        })

    # Date patterns
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    prev_dates = set(date_pattern.findall(previous))
    curr_dates = set(date_pattern.findall(current))
    if prev_dates != curr_dates:
        changes.append({
            "type": "date",
            "removed": list(prev_dates - curr_dates),
            "added": list(curr_dates - prev_dates),
        })

    return changes
