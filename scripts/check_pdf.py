#!/usr/bin/env python3
"""Validate PDF structure, metadata, fonts, text, and rendering."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .build_pdf import assemble_markdown
    from .pdf_manifest import load_manifest, output_path
except ImportError:
    from build_pdf import assemble_markdown
    from pdf_manifest import load_manifest, output_path


FONT_FLAGS = re.compile(
    r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$",
    re.IGNORECASE,
)
EXPECTED_EMBEDDED_FONTS = {
    "NotoSans-Bold",
    "NotoSans-Regular",
    "DejaVuSansMono",
    "FiraCode-Regular",
}
# The guide inherits Pandoc's MatchLowercase default font feature, so its
# rendered Fira cell pitch differs from the unscaled standalone font fixture.
# This locked Poppler pitch reconstructs one source space per rendered cell.
GUIDE_CODE_EXTRACTION_PITCH = 4.5
CODE_FILTER_PROOF_LINES = (
    "RAIL-PROOF-START",
    "    indented child",
    "",
    "column-a  column-b",
    "RAIL-PROOF-END",
)
EXACT_CODE_EXTRACTION_SPANS = (
    (
        "for gpu in physical_gpus:",
        "    try:",
        "        tf.config.experimental.set_memory_growth(gpu, True)",
        "    except Exception as exc:",
        '        print("memory_growth_warning", gpu, type(exc).__name__, exc)',
    ),
    (
        "printf '%s  %s\\n' \"$INSTALLER_SHA256\" \"$INSTALLER\" | "
        "sha256sum --check -",
    ),
)
HEADING_FONT = "NotoSans-Bold"
TOC_FONTS = frozenset({"NotoSans-Bold", "NotoSans-Regular"})
BODY_FIRST_PHYSICAL_PAGE = 3


@dataclass(frozen=True)
class HeadingInfo:
    level: int
    text: str
    identifier: str


@dataclass(frozen=True)
class ChapterOpener:
    heading: HeadingInfo
    first_subheading: HeadingInfo


@dataclass(frozen=True)
class AppendixCodeHeading:
    heading: HeadingInfo
    first_source_line: str


@dataclass(frozen=True)
class HeadingContracts:
    headings: tuple[HeadingInfo, ...]
    chapters: tuple[ChapterOpener, ...]
    appendix_code: tuple[AppendixCodeHeading, ...]
    source_heading_code_count: int


@dataclass(frozen=True)
class TextBlock:
    page: int
    text: str
    fonts: frozenset[str]
    y0: float
    y1: float
    visual_lines: int


def run_text(command: list[str]) -> str:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def tool(name: str) -> str:
    result = shutil.which(name)
    if not result:
        raise RuntimeError(f"required PDF QA tool is not available: {name}")
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_info(text: str) -> dict[str, str]:
    info: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info


def validate_fonts(
    output: str,
    expected_fonts: set[str] | frozenset[str] = EXPECTED_EMBEDDED_FONTS,
) -> int:
    rows = [
        line
        for line in output.splitlines()[2:]
        if line.strip() and not set(line.strip()) <= {"-"}
    ]
    if not rows:
        raise RuntimeError("pdffonts reported no fonts")
    observed_fonts: set[str] = set()
    for row in rows:
        match = FONT_FLAGS.search(row)
        if not match:
            raise RuntimeError(f"could not parse pdffonts row: {row}")
        embedded, _subset, unicode_map = (value.casefold() for value in match.groups())
        if embedded != "yes":
            raise RuntimeError(f"font is not embedded: {row}")
        if unicode_map != "yes":
            raise RuntimeError(f"font lacks a Unicode map: {row}")
        font_name = row.split(maxsplit=1)[0]
        observed_fonts.add(font_name.split("+", 1)[-1])
    if observed_fonts != set(expected_fonts):
        raise RuntimeError(
            "PDF embedded font families changed: "
            f"observed {sorted(observed_fonts)}, "
            f"expected {sorted(expected_fonts)}"
        )
    return len(rows)


def extract_unique_fixed_span(text: str, expected: tuple[str, ...]) -> tuple[str, ...]:
    """Return one marker-bounded code span with its common margin removed."""
    lines = [line.rstrip() for line in text.splitlines()]
    starts = [
        index
        for index, line in enumerate(lines)
        if line.lstrip() == expected[0].lstrip()
    ]
    if len(starts) != 1:
        raise RuntimeError(
            "code extraction start marker must occur exactly once: "
            f"{expected[0]!r}; found {len(starts)}"
        )
    start = starts[0]
    end_markers = [
        index
        for index in range(start, len(lines))
        if lines[index].lstrip() == expected[-1].lstrip()
    ]
    if len(end_markers) != 1:
        raise RuntimeError(
            "code extraction end marker must occur exactly once after its start: "
            f"{expected[-1]!r}; found {len(end_markers)}"
        )
    margin = len(lines[start]) - len(lines[start].lstrip(" "))
    normalized: list[str] = []
    for line in lines[start : end_markers[0] + 1]:
        if not line.strip():
            continue
        if margin and not line.startswith(" " * margin):
            raise RuntimeError("code extraction changed the common left margin")
        normalized.append(line[margin:])
    return tuple(normalized)


def validate_exact_code_extraction(text: str) -> None:
    """Require representative indentation and interior spaces to survive."""
    for expected in EXACT_CODE_EXTRACTION_SPANS:
        observed = extract_unique_fixed_span(text, expected)
        if observed != expected:
            raise RuntimeError(
                f"code space extraction changed: {observed!r} != {expected!r}"
            )


def validate_code_filter_output(output: str) -> None:
    """Require one direct artifact rail for every real fixture source line."""
    expected_fragments = (
        "\\begin{GuideCode}\n\n"
        "\\leavevmode\\GuideCodeRail{}RAIL-PROOF-START",
        "\\leavevmode\\GuideCodeRail{}"
        "\\hspace*{\\dimexpr4\\fontcharwd\\font`0\\relax}"
        "indented child",
        "\\leavevmode\\GuideCodeRail{}\\strut",
        "\\leavevmode\\GuideCodeRail{}column-a "
        "\\hspace*{\\dimexpr1\\fontcharwd\\font`0\\relax}column-b",
        "\\leavevmode\\GuideCodeRail{}RAIL-PROOF-END",
    )
    if output.count("\\leavevmode\\GuideCodeRail{}") != len(
        CODE_FILTER_PROOF_LINES
    ):
        raise RuntimeError("code filter did not emit one rail per real source line")
    cursor = 0
    for fragment in expected_fragments:
        position = output.find(fragment, cursor)
        if position < 0:
            raise RuntimeError(f"code filter output is missing: {fragment}")
        cursor = position + len(fragment)
    if "\\everypar" in output:
        raise RuntimeError("code filter output unexpectedly uses everypar")


def validate_code_filter_contract(pandoc: str, filter_path: Path) -> None:
    """Exercise valid and invalid line boundaries with the locked Pandoc."""
    body = "\n".join(CODE_FILTER_PROOF_LINES)
    fixture = f"```text\n{body}\n```\n"
    command = [
        pandoc,
        "--from=markdown",
        "--to=latex",
        "--wrap=none",
        f"--lua-filter={filter_path}",
    ]
    result = subprocess.run(
        command,
        input=fixture,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"valid code-filter fixture failed: {result.stderr.strip()}")
    validate_code_filter_output(result.stdout)
    invalid_fixtures = (
        f"```text\n\n{body}\n```\n",
        f"```text\n{body}\n\n```\n",
    )
    for invalid in invalid_fixtures:
        rejected = subprocess.run(
            command,
            input=invalid,
            capture_output=True,
            text=True,
            check=False,
        )
        if rejected.returncode == 0:
            raise RuntimeError(
                "code filter accepted an invented leading or trailing blank line"
            )


def inline_text(inlines: list[dict[str, Any]]) -> str:
    """Return the literal visible text of supported Pandoc inline nodes."""
    parts: list[str] = []
    for inline in inlines:
        tag = inline.get("t")
        content = inline.get("c")
        if tag == "Str" and isinstance(content, str):
            parts.append(content)
        elif tag in {"Space", "SoftBreak", "LineBreak"}:
            parts.append(" ")
        elif tag in {"Code", "Math", "RawInline"}:
            if not (
                isinstance(content, list)
                and len(content) == 2
                and isinstance(content[1], str)
            ):
                raise RuntimeError(f"malformed Pandoc {tag} inline")
            parts.append(content[1])
        elif tag in {
            "Emph",
            "Strong",
            "Strikeout",
            "SmallCaps",
            "Superscript",
            "Subscript",
            "Cite",
        }:
            nested = content[1] if tag == "Cite" else content
            if not isinstance(nested, list):
                raise RuntimeError(f"malformed Pandoc {tag} inline")
            parts.append(inline_text(nested))
        elif tag in {"Link", "Image", "Span"}:
            if not (
                isinstance(content, list)
                and len(content) >= 2
                and isinstance(content[1], list)
            ):
                raise RuntimeError(f"malformed Pandoc {tag} inline")
            parts.append(inline_text(content[1]))
        elif tag == "Quoted":
            if not (
                isinstance(content, list)
                and len(content) == 2
                and isinstance(content[1], list)
            ):
                raise RuntimeError("malformed Pandoc Quoted inline")
            parts.append(inline_text(content[1]))
        elif tag == "Note":
            continue
        else:
            raise RuntimeError(f"unsupported Pandoc heading inline: {tag}")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def count_inline_tag(node: Any, target: str) -> int:
    if isinstance(node, dict):
        return (1 if node.get("t") == target else 0) + sum(
            count_inline_tag(value, target) for value in node.values()
        )
    if isinstance(node, list):
        return sum(count_inline_tag(value, target) for value in node)
    return 0


def load_heading_contracts(
    pandoc: str,
    root: Path,
    manifest: dict[str, Any],
) -> HeadingContracts:
    """Derive heading and opener contracts from the canonical assembled AST."""
    result = subprocess.run(
        [
            pandoc,
            "--from=markdown-implicit_figures+smart",
            "--to=json",
        ],
        input=assemble_markdown(root, manifest),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"canonical heading AST failed: {result.stderr.strip()}")
    document = json.loads(result.stdout)
    blocks = document.get("blocks")
    if not isinstance(blocks, list):
        raise RuntimeError("canonical Pandoc AST is missing its block list")

    headings_by_index: dict[int, HeadingInfo] = {}
    heading_inlines: dict[int, list[dict[str, Any]]] = {}
    for index, block in enumerate(blocks):
        if not isinstance(block, dict) or block.get("t") != "Header":
            continue
        content = block.get("c")
        if not (
            isinstance(content, list)
            and len(content) == 3
            and isinstance(content[0], int)
            and isinstance(content[1], list)
            and len(content[1]) == 3
            and isinstance(content[1][0], str)
            and isinstance(content[2], list)
        ):
            raise RuntimeError("canonical Pandoc AST contains a malformed Header")
        level = content[0]
        if level not in (1, 2):
            raise RuntimeError(f"canonical guide contains unsupported H{level}")
        heading = HeadingInfo(level, inline_text(content[2]), content[1][0])
        if not heading.text or not heading.identifier:
            raise RuntimeError("every canonical heading needs text and an identifier")
        headings_by_index[index] = heading
        heading_inlines[index] = content[2]

    headings = tuple(headings_by_index.values())
    identifiers = [heading.identifier for heading in headings]
    if len(set(identifiers)) != len(identifiers):
        raise RuntimeError("canonical heading identifiers must be unique")
    expected_h1 = (
        len(manifest["core_sources"])
        + len(manifest["site_appendices"])
        + 1
    )
    if sum(heading.level == 1 for heading in headings) != expected_h1:
        raise RuntimeError("canonical guide chapter count changed")

    chapters: list[ChapterOpener] = []
    appendix_code: list[AppendixCodeHeading] = []
    for index, heading in headings_by_index.items():
        if heading.level == 1:
            cursor = index + 1
            while cursor < len(blocks) and blocks[cursor].get("t") == "RawBlock":
                cursor += 1
            if cursor >= len(blocks) or blocks[cursor].get("t") != "Para":
                raise RuntimeError(
                    "chapter opener must begin with a short introductory paragraph: "
                    f"{heading.text}"
                )
            first_subheading = None
            while cursor < len(blocks):
                candidate = headings_by_index.get(cursor)
                if candidate and candidate.level == 1:
                    break
                if candidate and candidate.level == 2:
                    first_subheading = candidate
                    break
                cursor += 1
            if first_subheading is None:
                raise RuntimeError(
                    f"chapter opener has no first subsection: {heading.text}"
                )
            chapters.append(ChapterOpener(heading, first_subheading))

        if heading.level == 2 and heading.identifier.startswith("example-"):
            cursor = index + 1
            while cursor < len(blocks) and blocks[cursor].get("t") == "RawBlock":
                cursor += 1
            if cursor >= len(blocks) or blocks[cursor].get("t") != "CodeBlock":
                raise RuntimeError(
                    f"Appendix B heading is not followed by source: {heading.text}"
                )
            code_content = blocks[cursor].get("c")
            if not (
                isinstance(code_content, list)
                and len(code_content) == 2
                and isinstance(code_content[1], str)
            ):
                raise RuntimeError("Appendix B contains a malformed CodeBlock")
            source_lines = code_content[1].splitlines()
            if not source_lines or not source_lines[0].strip():
                raise RuntimeError("Appendix B source has no first nonblank line")
            appendix_code.append(AppendixCodeHeading(heading, source_lines[0]))

    if len(appendix_code) != len(manifest["examples"]):
        raise RuntimeError("Appendix B heading/source contract count changed")
    source_heading_code_count = sum(
        count_inline_tag(heading_inlines[index], "Code")
        for index in heading_inlines
    )
    if source_heading_code_count < len(appendix_code):
        raise RuntimeError("canonical source lost its literal code heading coverage")
    return HeadingContracts(
        headings,
        tuple(chapters),
        tuple(appendix_code),
        source_heading_code_count,
    )


def validate_heading_filter_output(output: str) -> None:
    """Require bounded openers, no-breaks, and literal PDF heading text."""
    if output.count("\\begin{samepage}") != 2:
        raise RuntimeError("heading filter did not open both bounded chapter fixtures")
    if output.count("\\end{samepage}") != 2:
        raise RuntimeError("heading filter did not close both bounded chapter fixtures")
    if output.count("\\nopagebreak[4]") != 2:
        raise RuntimeError("heading filter did not protect both first subsections")
    required = (
        "\\section{1. Chapter literal\\_name}\\label{chapter-id}",
        "\\subsection{1.1 First sub\\_name}\\label{first-id}",
        "\\section{2. Second Chapter}\\label{second-id}",
        "\\subsection{2.1 Second First}\\label{second-first-id}",
        "\\texttt{body\\_literal}",
    )
    for heading_code in ("literal\\_name", "sub\\_name"):
        if f"\\texttt{{{heading_code}}}" in output:
            raise RuntimeError("heading filter retained terminal styling in a heading")
    for fragment in required:
        if fragment not in output:
            raise RuntimeError(f"heading filter output is missing: {fragment}")
    first_open = output.find("\\begin{samepage}")
    first_section = output.find("\\section{1. Chapter")
    first_subsection = output.find("\\subsection{1.1 First")
    first_close = output.find("\\end{samepage}")
    first_no_break = output.find("\\nopagebreak[4]")
    first_body = output.find("First subsection body")
    if not (
        first_open
        < first_section
        < first_subsection
        < first_close
        < first_no_break
        < first_body
    ):
        raise RuntimeError("heading filter emitted an invalid opener boundary order")


def validate_heading_filter_contract(pandoc: str, filter_path: Path) -> None:
    """Exercise the PDF-only heading transformation and source-shape guard."""
    tick = "`"
    fixture = (
        f"# 1. Chapter {tick}literal_name{tick} {{#chapter-id}}\n\n"
        f"Intro with {tick}body_literal{tick}.\n\n"
        f"## 1.1 First {tick}sub_name{tick} {{#first-id}}\n\n"
        "First subsection body.\n\n"
        "# 2. Second Chapter {#second-id}\n\n"
        "Second intro.\n\n"
        "## 2.1 Second First {#second-first-id}\n\n"
        "Second subsection body.\n"
    )
    command = [
        pandoc,
        "--from=markdown",
        "--to=latex",
        "--wrap=none",
        f"--lua-filter={filter_path}",
    ]
    result = subprocess.run(
        command,
        input=fixture,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"valid heading-filter fixture failed: {result.stderr.strip()}"
        )
    validate_heading_filter_output(result.stdout)

    invalid_fixtures = (
        "# Missing Intro\n\n- list first\n\n## First Subsection\n\nBody.\n",
        "# Missing Subsection\n\nIntro.\n",
    )
    for invalid in invalid_fixtures:
        rejected = subprocess.run(
            command,
            input=invalid,
            capture_output=True,
            text=True,
            check=False,
        )
        if rejected.returncode == 0:
            raise RuntimeError("heading filter accepted an invalid chapter opener")


def canonical_text(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "", text).casefold()


def parse_stext(path: Path) -> tuple[TextBlock, ...]:
    """Parse MuPDF structured text into deterministic physical-page blocks."""
    root = ET.parse(path).getroot()
    blocks: list[TextBlock] = []
    for page_number, page in enumerate(root.findall("page"), start=1):
        for block in page.findall("block"):
            text = re.sub(
                r"\s+",
                " ",
                "".join(char.get("c", "") for char in block.iter("char")),
            ).strip()
            if not text:
                continue
            bbox = block.get("bbox", "").split()
            if len(bbox) != 4:
                raise RuntimeError("MuPDF structured text block has no bounding box")
            fonts = frozenset(
                font.get("name", "") for font in block.iter("font")
            )
            if "" in fonts:
                raise RuntimeError("MuPDF structured text contains an unnamed font")
            visual_rows = {
                round(float(line.get("bbox", "0 0 0 0").split()[1]), 1)
                for line in block.findall("line")
            }
            blocks.append(
                TextBlock(
                    page_number,
                    text,
                    fonts,
                    float(bbox[1]),
                    float(bbox[3]),
                    len(visual_rows),
                )
            )
    if not blocks:
        raise RuntimeError("MuPDF structured text contains no visible text blocks")
    return tuple(blocks)


def validate_outline(output: str, headings: tuple[HeadingInfo, ...]) -> None:
    """Require the source heading text, hierarchy, and unique destinations."""
    observed: list[tuple[int, str]] = []
    destinations: list[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        prefix = line[0]
        if prefix not in {"+", "|"}:
            raise RuntimeError(f"could not parse MuPDF outline entry: {line}")
        remainder = line[1:].lstrip()
        try:
            title, end = json.JSONDecoder().raw_decode(remainder)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"could not parse MuPDF outline entry: {line}"
            ) from exc
        tail = remainder[end:]
        if not tail or not tail[0].isspace() or tail != tail.rstrip():
            raise RuntimeError(f"could not parse MuPDF outline entry: {line}")
        suffix = tail.lstrip()
        destination_prefix = "#nameddest="
        if (
            not isinstance(title, str)
            or not suffix.startswith(destination_prefix)
        ):
            raise RuntimeError(f"could not parse MuPDF outline entry: {line}")
        destination = suffix[len(destination_prefix) :]
        if not destination or any(char.isspace() for char in destination):
            raise RuntimeError(f"could not parse MuPDF outline entry: {line}")
        level = 1 if prefix == "+" else 2
        observed.append((level, title))
        destinations.append(destination)
    expected = [(heading.level, heading.text) for heading in headings]
    if observed != expected:
        raise RuntimeError("PDF outline text or heading hierarchy changed")
    if len(set(destinations)) != len(destinations):
        raise RuntimeError("PDF outline destinations must be unique")


def validate_heading_layout(
    blocks: tuple[TextBlock, ...],
    contracts: HeadingContracts,
) -> None:
    """Require heading fonts, bounded pagination, and a compact Noto TOC."""
    observed: dict[str, TextBlock] = {}
    heading_keys = {canonical_text(heading.text) for heading in contracts.headings}
    for heading in contracts.headings:
        key = canonical_text(heading.text)
        matches = [
            block
            for block in blocks
            if block.page >= BODY_FIRST_PHYSICAL_PAGE
            and canonical_text(block.text) == key
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"heading must occur in exactly one body text block: {heading.text}; "
                f"found {len(matches)}"
            )
        block = matches[0]
        if block.fonts != frozenset({HEADING_FONT}):
            raise RuntimeError(
                f"heading did not use only {HEADING_FONT}: {heading.text}; "
                f"found {sorted(block.fonts)}"
            )
        observed[heading.identifier] = block

    if observed[contracts.chapters[0].heading.identifier].page != 3:
        raise RuntimeError("the two-column contents must remain one physical page")
    for chapter in contracts.chapters:
        heading_page = observed[chapter.heading.identifier].page
        subsection_page = observed[chapter.first_subheading.identifier].page
        if heading_page != subsection_page:
            raise RuntimeError(
                "chapter opener split across pages: "
                f"{chapter.heading.text} is on {heading_page}, "
                f"{chapter.first_subheading.text} is on {subsection_page}"
            )

    for appendix in contracts.appendix_code:
        heading_block = observed[appendix.heading.identifier]
        first_line = canonical_text(appendix.first_source_line)
        if not any(
            block.page == heading_block.page
            and canonical_text(block.text) == first_line
            for block in blocks
        ):
            raise RuntimeError(
                "Appendix B heading is separated from its first source line: "
                f"{appendix.heading.text}"
            )

    for heading in contracts.headings:
        heading_block = observed[heading.identifier]
        if not any(
            candidate.page == heading_block.page
            and candidate.y0 > heading_block.y1 + 0.5
            and candidate.y0 < 745
            and canonical_text(candidate.text) not in heading_keys
            for candidate in blocks
        ):
            raise RuntimeError(
                f"heading has no same-page semantic text below it: {heading.text}"
            )

    toc_blocks = [
        block for block in blocks if block.page == 2 and 45 <= block.y0 < 730
    ]
    if not toc_blocks:
        raise RuntimeError("MuPDF structured text did not find the contents page")
    toc_fonts = frozenset(font for block in toc_blocks for font in block.fonts)
    if not toc_fonts.issubset(TOC_FONTS):
        raise RuntimeError(
            "contents page retained terminal-style heading text: "
            f"{sorted(toc_fonts - TOC_FONTS)}"
        )
    three_line = [block.text for block in toc_blocks if block.visual_lines > 2]
    if three_line:
        raise RuntimeError(
            f"contents page contains a three-line entry: {three_line[0]}"
        )


def validate_pdf(pdf: Path, manifest: dict[str, Any], root: Path) -> None:
    qpdf = tool("qpdf")
    pdfinfo = tool("pdfinfo")
    pdftotext = tool("pdftotext")
    pdffonts = tool("pdffonts")
    pdftoppm = tool("pdftoppm")
    pandoc = tool("pandoc")
    mutool = tool("mutool")

    filter_path = root / manifest["code_filter_source"]
    validate_code_filter_contract(pandoc, filter_path)
    validate_heading_filter_contract(pandoc, filter_path)
    heading_contracts = load_heading_contracts(pandoc, root, manifest)

    subprocess.run([qpdf, "--check", str(pdf)], check=True)
    info = parse_info(run_text([pdfinfo, str(pdf)]))
    if info.get("Title") != manifest["title"]:
        raise RuntimeError(f"unexpected PDF title: {info.get('Title')}")
    if info.get("Author") != manifest["author"]:
        raise RuntimeError(f"unexpected PDF author: {info.get('Author')}")
    if info.get("Encrypted", "").casefold() != "no":
        raise RuntimeError("PDF must not be encrypted")
    pages = int(info.get("Pages", "0"))
    if pages < 10:
        raise RuntimeError(f"PDF is unexpectedly short: {pages} pages")
    page_size = info.get("Page size", "")
    if "612 x 792 pts" not in page_size:
        raise RuntimeError(f"PDF is not US Letter size: {page_size}")

    font_count = validate_fonts(run_text([pdffonts, str(pdf)]))
    validate_outline(
        run_text([mutool, "show", str(pdf), "outline"]),
        heading_contracts.headings,
    )
    with tempfile.TemporaryDirectory(prefix="utc-hpc-pdf-qa-") as temp:
        temp_path = Path(temp)
        text_path = temp_path / "guide.txt"
        subprocess.run(
            [pdftotext, "-layout", str(pdf), str(text_path)],
            check=True,
        )
        extracted = text_path.read_text(encoding="utf-8")
        for required in manifest["required_pdf_text"]:
            if required not in extracted:
                raise RuntimeError(f"required PDF text is missing: {required}")
        if re.search(r"/scratch/\$USER|/home/[A-Za-z0-9._-]+", extracted):
            raise RuntimeError("PDF contains a prohibited concrete user storage path")

        fixed_text_path = temp_path / "guide-fixed.txt"
        subprocess.run(
            [
                pdftotext,
                "-fixed",
                f"{GUIDE_CODE_EXTRACTION_PITCH:.2f}",
                "-nopgbrk",
                str(pdf),
                str(fixed_text_path),
            ],
            check=True,
        )
        validate_exact_code_extraction(
            fixed_text_path.read_text(encoding="utf-8")
        )

        stext_path = temp_path / "guide-stext.xml"
        subprocess.run(
            [
                mutool,
                "draw",
                "-q",
                "-F",
                "stext",
                "-o",
                str(stext_path),
                str(pdf),
            ],
            check=True,
        )
        validate_heading_layout(parse_stext(stext_path), heading_contracts)

        render_prefix = temp_path / "page"
        subprocess.run(
            [
                pdftoppm,
                "-png",
                "-r",
                "36",
                str(pdf),
                str(render_prefix),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        rendered = sorted(temp_path.glob("page-*.png"))
        if len(rendered) != pages or any(path.stat().st_size == 0 for path in rendered):
            raise RuntimeError(
                f"expected {pages} rendered pages, found {len(rendered)}"
            )

    print(
        "pdf_qa_passed "
        f"pages={pages} fonts={font_count} "
        f"headings={len(heading_contracts.headings)} "
        f"chapter_openers={len(heading_contracts.chapters)} "
        f"heading_code_literals={heading_contracts.source_heading_code_count} "
        f"sha256={sha256(pdf)}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("pdf/guide_manifest.json"),
    )
    parser.add_argument("--pdf", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = Path(
            subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        manifest_path = args.manifest
        if not manifest_path.is_absolute():
            manifest_path = root / manifest_path
        manifest = load_manifest(manifest_path)
        pdf = args.pdf or output_path(root, manifest)
        if not pdf.is_absolute():
            pdf = root / pdf
        validate_pdf(pdf, manifest, root)
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ERROR: PDF QA failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
