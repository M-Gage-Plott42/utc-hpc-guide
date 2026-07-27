#!/usr/bin/env python3
"""Reject angle-bracket placeholders where a shell could parse them."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ANGLE_PLACEHOLDER = re.compile(r"<[A-Za-z][A-Za-z0-9_-]*>")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*([A-Za-z0-9_-]*)")
SHELL_LANGUAGES = {"bash", "console", "sh", "shell", "sshconfig", "zsh"}


@dataclass(frozen=True)
class Finding:
    line: int
    value: str


def scan_sbatch(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in ANGLE_PLACEHOLDER.finditer(line):
            findings.append(Finding(line_number, match.group(0)))
    return findings


def scan_markdown(text: str) -> list[Finding]:
    findings: list[Finding] = []
    fence_character = ""
    fence_length = 0
    scan_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = FENCE.match(line)
        if not fence_character:
            if match:
                fence = match.group(1)
                fence_character = fence[0]
                fence_length = len(fence)
                scan_fence = match.group(2).casefold() in SHELL_LANGUAGES
            continue

        stripped = line.lstrip()
        closing_length = len(stripped) - len(stripped.lstrip(fence_character))
        if closing_length >= fence_length and not stripped[closing_length:].strip():
            fence_character = ""
            fence_length = 0
            scan_fence = False
            continue

        if scan_fence:
            for placeholder in ANGLE_PLACEHOLDER.finditer(line):
                findings.append(Finding(line_number, placeholder.group(0)))
    return findings


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md", "examples/*.sbatch"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    ]


def main() -> int:
    root_result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    root = Path(root_result.stdout.strip())
    findings: list[tuple[str, Finding]] = []
    for path in tracked_paths(root):
        text = (root / path).read_text(encoding="utf-8")
        file_findings = (
            scan_sbatch(text)
            if path.endswith(".sbatch")
            else scan_markdown(text)
        )
        findings.extend((path, finding) for finding in file_findings)

    if findings:
        for path, finding in findings:
            print(
                f"{path}:{finding.line}: unsafe shell placeholder: {finding.value}",
                file=sys.stderr,
            )
        print(
            f"ERROR: found {len(findings)} unsafe shell placeholder(s).",
            file=sys.stderr,
        )
        return 1

    print(f"shell_placeholders_clean scanned_files={len(tracked_paths(root))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
