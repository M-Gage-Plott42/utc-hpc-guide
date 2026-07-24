#!/usr/bin/env python3
"""Parse Markdown and HTML links and validate local paths and anchors."""

from __future__ import annotations

import html
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


REFERENCE_DEFINITION = re.compile(
    r"^[ \t]{0,3}\[([^\]]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))",
    re.MULTILINE,
)
ATX_HEADING = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+(.+?)[ \t]*$", re.MULTILINE)
SETEXT_UNDERLINE = re.compile(r"^[ \t]{0,3}(?:=+|-+)[ \t]*$")
FENCE_START = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")


@dataclass(frozen=True)
class Link:
    destination: str
    line: int
    kind: str


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    message: str


class LinkHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[Link] = []
        self.anchors: set[str] = set()

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self._handle_attributes(tag, attrs)

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self._handle_attributes(tag, attrs)

    def _handle_attributes(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        for name, value in attrs:
            if value is None:
                continue
            lowered = name.casefold()
            if lowered in {"href", "src"}:
                self.links.append(Link(value, self.getpos()[0], f"html-{tag}-{lowered}"))
            if lowered in {"id", "name"} and value:
                self.anchors.add(value)


def blank_content(value: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in value)


def mask_code(markdown: str) -> str:
    lines = markdown.splitlines(keepends=True)
    masked_lines: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in lines:
        if fence_character:
            stripped = line.lstrip(" ")
            run = len(stripped) - len(stripped.lstrip(fence_character))
            masked_lines.append(blank_content(line))
            if run >= fence_length and not stripped[run:].strip():
                fence_character = ""
                fence_length = 0
            continue
        match = FENCE_START.match(line)
        if match:
            fence = match.group(1)
            fence_character = fence[0]
            fence_length = len(fence)
            masked_lines.append(blank_content(line))
            continue
        if line.startswith("    ") or line.startswith("\t"):
            masked_lines.append(blank_content(line))
            continue
        masked_lines.append(line)

    masked = list("".join(masked_lines))
    index = 0
    while index < len(masked):
        if masked[index] != "`":
            index += 1
            continue
        run_end = index
        while run_end < len(masked) and masked[run_end] == "`":
            run_end += 1
        delimiter = "`" * (run_end - index)
        closing = "".join(masked).find(delimiter, run_end)
        if closing == -1:
            index = run_end
            continue
        for position in range(index, closing + len(delimiter)):
            if masked[position] != "\n":
                masked[position] = " "
        index = closing + len(delimiter)
    return "".join(masked)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def normalize_reference(label: str) -> str:
    return " ".join(label.split()).casefold()


def find_closing_bracket(text: str, start: int) -> int | None:
    depth = 1
    index = start
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "[":
            depth += 1
        elif text[index] == "]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def find_closing_parenthesis(text: str, start: int) -> int | None:
    depth = 1
    in_angle = False
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "<" and depth == 1:
            in_angle = True
        elif char == ">" and in_angle:
            in_angle = False
        elif not in_angle and char == "(":
            depth += 1
        elif not in_angle and char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def markdown_unescape(value: str) -> str:
    return re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])", r"\1", value)


def inline_destination(content: str) -> str:
    content = content.lstrip()
    if content.startswith("<"):
        closing = content.find(">")
        return markdown_unescape(content[1:closing]) if closing >= 0 else ""
    depth = 0
    result: list[str] = []
    index = 0
    while index < len(content):
        char = content[index]
        if char == "\\" and index + 1 < len(content):
            result.extend((char, content[index + 1]))
            index += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char.isspace() and depth == 0:
            break
        result.append(char)
        index += 1
    return markdown_unescape("".join(result))


def parse_markdown_links(
    text: str,
) -> tuple[list[Link], list[Finding], dict[str, Link]]:
    definitions: dict[str, Link] = {}
    findings: list[Finding] = []
    definition_spans: list[tuple[int, int]] = []
    for match in REFERENCE_DEFINITION.finditer(text):
        label = normalize_reference(match.group(1))
        destination = match.group(2) or match.group(3)
        link = Link(markdown_unescape(destination), line_number(text, match.start()), "reference-definition")
        if label in definitions:
            findings.append(
                Finding("", link.line, f"duplicate reference definition: {match.group(1)}")
            )
        else:
            definitions[label] = link
        line_end = text.find("\n", match.start())
        definition_spans.append((match.start(), len(text) if line_end < 0 else line_end))

    scan_text = list(text)
    for start, end in definition_spans:
        for index in range(start, end):
            scan_text[index] = " "
    scan = "".join(scan_text)

    links = list(definitions.values())
    index = 0
    while index < len(scan):
        label_start = index + 1 if scan[index:index + 2] == "![" else index
        if label_start >= len(scan) or scan[label_start] != "[":
            index += 1
            continue
        label_end = find_closing_bracket(scan, label_start + 1)
        if label_end is None:
            index += 1
            continue
        label = scan[label_start + 1:label_end]
        following = label_end + 1
        line = line_number(scan, label_start)
        if following < len(scan) and scan[following] == "(":
            closing = find_closing_parenthesis(scan, following + 1)
            if closing is None:
                findings.append(Finding("", line, "unclosed inline link destination"))
                index = label_end + 1
                continue
            destination = inline_destination(scan[following + 1:closing])
            if not destination:
                findings.append(Finding("", line, "empty or invalid inline link destination"))
            else:
                links.append(Link(destination, line, "markdown-inline"))
            index = closing + 1
            continue
        if following < len(scan) and scan[following] == "[":
            reference_end = find_closing_bracket(scan, following + 1)
            if reference_end is None:
                findings.append(Finding("", line, "unclosed reference label"))
                index = label_end + 1
                continue
            explicit = scan[following + 1:reference_end]
            reference = normalize_reference(explicit or label)
            if reference not in definitions:
                findings.append(Finding("", line, f"missing reference definition: {explicit or label}"))
            else:
                links.append(
                    Link(definitions[reference].destination, line, "markdown-reference")
                )
            index = reference_end + 1
            continue
        shortcut = normalize_reference(label)
        if shortcut in definitions:
            links.append(Link(definitions[shortcut].destination, line, "markdown-shortcut-reference"))
        index = label_end + 1
    return links, findings, definitions


def heading_slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = value.strip().rstrip("#").strip().casefold()
    characters: list[str] = []
    for char in value:
        if char.isspace():
            characters.append("-")
        elif char in {"-", "_"} or char.isalnum():
            characters.append(char)
        elif not unicodedata.category(char).startswith(("P", "S")):
            characters.append(char)
    return re.sub(r"-+", "-", "".join(characters))


def document_anchors(text: str, html_anchors: set[str]) -> set[str]:
    anchors = set(html_anchors)
    counts: dict[str, int] = {}
    lines = text.splitlines()
    heading_values: list[str] = []
    for index, line in enumerate(lines):
        match = re.match(r"^[ \t]{0,3}#{1,6}[ \t]+(.+?)[ \t]*$", line)
        if match:
            heading_values.append(match.group(1))
            continue
        if (
            index + 1 < len(lines)
            and line.strip()
            and SETEXT_UNDERLINE.match(lines[index + 1])
        ):
            heading_values.append(line.strip())
    for value in heading_values:
        base = heading_slug(value)
        count = counts.get(base, 0)
        anchor = base if count == 0 else f"{base}-{count}"
        counts[base] = count + 1
        anchors.add(anchor)
    return anchors


def parse_document(text: str) -> tuple[list[Link], list[Finding], set[str]]:
    masked = mask_code(text)
    links, findings, _ = parse_markdown_links(masked)
    html_parser = LinkHTMLParser()
    html_parser.feed(masked)
    links.extend(html_parser.links)
    return links, findings, document_anchors(masked, html_parser.anchors)


def tracked_markdown_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        root / item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    ]


def validate_destination(
    root: Path,
    source: Path,
    link: Link,
    anchor_map: dict[Path, set[str]],
) -> Finding | None:
    destination = html.unescape(link.destination.strip())
    if destination.startswith("//"):
        return None
    parsed = urlsplit(destination)
    if parsed.scheme:
        return None
    raw_path = unquote(parsed.path)
    fragment = unquote(parsed.fragment)
    if raw_path.startswith("/"):
        target = root / raw_path.lstrip("/")
    elif raw_path:
        target = source.parent / raw_path
    else:
        target = source
    target = target.resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return Finding(
            source.relative_to(root).as_posix(),
            link.line,
            f"local link escapes repository: {link.destination}",
        )
    if not target.exists():
        return Finding(
            source.relative_to(root).as_posix(),
            link.line,
            f"missing local target: {link.destination}",
        )
    if fragment and target.suffix.casefold() == ".md":
        anchors = anchor_map.get(target)
        if anchors is None:
            anchors = parse_document(target.read_text(encoding="utf-8"))[2]
            anchor_map[target] = anchors
        if fragment not in anchors:
            return Finding(
                source.relative_to(root).as_posix(),
                link.line,
                f"missing Markdown anchor #{fragment} in {target.relative_to(root)}",
            )
    return None


def validate_repository(root: Path, markdown_paths: list[Path]) -> list[Finding]:
    documents: dict[Path, tuple[list[Link], list[Finding], set[str]]] = {}
    findings: list[Finding] = []
    for path in markdown_paths:
        resolved = path.resolve()
        parsed = parse_document(path.read_text(encoding="utf-8"))
        documents[resolved] = parsed
        for finding in parsed[1]:
            findings.append(
                Finding(path.relative_to(root).as_posix(), finding.line, finding.message)
            )
    anchor_map = {path: parsed[2] for path, parsed in documents.items()}
    for path, parsed in documents.items():
        for link in parsed[0]:
            finding = validate_destination(root, path, link, anchor_map)
            if finding:
                findings.append(finding)
    return findings


def main() -> int:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    root = Path(result.stdout.strip()).resolve()
    markdown_paths = tracked_markdown_paths(root)
    findings = validate_repository(root, markdown_paths)
    if findings:
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.message}", file=sys.stderr)
        print(f"ERROR: link validation failed with {len(findings)} finding(s).", file=sys.stderr)
        return 1
    print(f"all_local_links_and_anchors_resolve markdown_files={len(markdown_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
