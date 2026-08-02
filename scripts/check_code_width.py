"""Validate printable fenced-code widths with one exact canonical exception."""

from __future__ import annotations

import re


FENCE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")
CANONICAL_WIDTH_LIMIT = 80
MINICONDA_DIGEST_LINE = (
    'INSTALLER_SHA256="ecb43ee4ae30a7a5af87737e9548ceb21'
    'f0a10ec55b8dc40d247aa925b80bfec"'
)
CANONICAL_WIDTH_EXCEPTIONS = ((83, MINICONDA_DIGEST_LINE),)


def overlong_fenced_code_lines(
    markdown: str,
    *,
    limit: int = CANONICAL_WIDTH_LIMIT,
) -> list[tuple[int, int, str]]:
    """Return line number, expanded width, and text for overlong code lines."""
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


def validate_fenced_code_width(
    markdown: str,
    *,
    allowed: tuple[tuple[int, str], ...] = (),
    limit: int = CANONICAL_WIDTH_LIMIT,
) -> None:
    """Require overlong fenced lines to match the exact ordered allowlist."""
    failures = overlong_fenced_code_lines(markdown, limit=limit)
    observed = tuple((width, line) for _number, width, line in failures)
    if observed == allowed:
        return
    details = "; ".join(
        f"line {line_number}: {width} characters"
        for line_number, width, _line in failures
    ) or "none"
    raise ValueError(
        "printable fenced-code width exceptions changed: "
        f"observed {details}; expected {len(allowed)} exact exception(s)"
    )
