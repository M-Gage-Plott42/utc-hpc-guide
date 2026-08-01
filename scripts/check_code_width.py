"""Validate printable fenced-code line lengths without changing source text."""

from __future__ import annotations

import re


FENCE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")


def overlong_fenced_code_lines(
    markdown: str,
    *,
    limit: int = 80,
) -> list[tuple[int, int, str]]:
    """Return line number, expanded width, and text for code lines over limit."""
    if limit < 1:
        raise ValueError("fenced-code width limit must be positive")
    marker: str | None = None
    marker_length = 0
    failures: list[tuple[int, int, str]] = []
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        fence = FENCE.match(line)
        if marker is None:
            if fence:
                token = fence.group(1)
                marker = token[0]
                marker_length = len(token)
            continue
        if fence:
            token = fence.group(1)
            if token[0] == marker and len(token) >= marker_length:
                marker = None
                marker_length = 0
                continue
        width = len(line.expandtabs(4))
        if width > limit:
            failures.append((line_number, width, line))
    if marker is not None:
        raise ValueError("assembled Markdown contains an unclosed code fence")
    return failures


def validate_fenced_code_width(markdown: str, *, limit: int = 80) -> None:
    failures = overlong_fenced_code_lines(markdown, limit=limit)
    if failures:
        details = "; ".join(
            f"line {line_number}: {width} characters"
            for line_number, width, _line in failures
        )
        raise ValueError(
            f"printable fenced code exceeds {limit} characters: {details}"
        )
