#!/usr/bin/env python3
"""Build and inspect the isolated Regular/Bold Fira semantic fixture."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from .check_pdf import validate_fonts
    from .code_font import LockedCodeFont, fontspec_definition, load_code_font
    from .pdf_manifest import load_manifest
except ImportError:
    from check_pdf import validate_fonts
    from code_font import LockedCodeFont, fontspec_definition, load_code_font
    from pdf_manifest import load_manifest


AMBIGUOUS_GLYPHS = (
    "0 O o 1 l I | < > <= >= == != -> -- _ ~ \\ / ' \" ( ) [ ] { }"
)
EXTRACTION_LINES = (
    "EXTRACTION-PROOF-START",
    "root",
    "    indented child",
    "column-a  column-b",
    "EXTRACTION-PROOF-END",
)


def tool(name: str) -> str:
    result = shutil.which(name)
    if not result:
        raise RuntimeError(f"required code-font fixture tool is unavailable: {name}")
    return result


def fixture_tex(font: LockedCodeFont) -> str:
    """Return a small tagged document that exercises both selected faces."""
    definition = fontspec_definition(font, command="FixtureCodeFont")
    regular_lines = (
        "FIRA-REGULAR-START",
        "REGULAR AMBIGUOUS GLYPHS",
        AMBIGUOUS_GLYPHS,
        *EXTRACTION_LINES,
        "FIRA-REGULAR-END",
    )
    bold_lines = (
        "FIRA-BOLD-START",
        "BOLD AMBIGUOUS GLYPHS",
        AMBIGUOUS_GLYPHS,
        "FIRA-BOLD-END",
    )

    def verbatim_paragraphs(lines: tuple[str, ...]) -> str:
        return "\n".join(f"\\noindent\\verb+{line}+\\par" for line in lines)

    return f"""\
\\DocumentMetadata{{
  lang=en-US,
  pdfstandard=ua-2,
  pdfversion=2.0,
  testphase={{phase-III,title}}
}}
\\documentclass{{article}}
\\usepackage{{fontspec}}
\\usepackage{{hyperref}}
\\hypersetup{{
  pdftitle={{Fira Code Semantic Fixture}},
  pdfauthor={{UTC HPC Guide test suite}}
}}
{definition}
\\pagestyle{{empty}}
\\begin{{document}}
\\makeatletter
\\begingroup
\\def\\verbatim@font{{\\FixtureCodeFont\\fontsize{{{font.font_size_pt:g}}}{{{font.leading_pt:g}}}\\selectfont}}
{verbatim_paragraphs(regular_lines)}
\\endgroup
\\begingroup
\\def\\verbatim@font{{\\FixtureCodeFont\\bfseries\\fontsize{{{font.font_size_pt:g}}}{{{font.leading_pt:g}}}\\selectfont}}
{verbatim_paragraphs(bold_lines)}
\\endgroup
\\makeatother
\\end{{document}}
"""


def extract_unique_span(text: str) -> tuple[str, ...]:
    """Extract the marker-bounded fixed-pitch lines with relative spaces."""
    lines = [line.rstrip() for line in text.splitlines()]
    starts = [
        index
        for index, line in enumerate(lines)
        if line.lstrip() == EXTRACTION_LINES[0]
    ]
    if len(starts) != 1:
        raise RuntimeError(
            "fixture extraction start marker must occur exactly once; "
            f"found {len(starts)}"
        )
    start = starts[0]
    ends = [
        index
        for index in range(start, len(lines))
        if lines[index].lstrip() == EXTRACTION_LINES[-1]
    ]
    if len(ends) != 1:
        raise RuntimeError(
            "fixture extraction end marker must occur exactly once after the start"
        )
    margin = len(lines[start]) - len(lines[start].lstrip(" "))
    normalized: list[str] = []
    for line in lines[start : ends[0] + 1]:
        if not line.strip():
            continue
        if margin and not line.startswith(" " * margin):
            raise RuntimeError("fixture extraction changed the common left margin")
        normalized.append(line[margin:])
    return tuple(normalized)


def default_glyph_ids(path: Path, text: str) -> tuple[int, ...]:
    """Return each literal character's glyph ID from the default Unicode cmap."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError(
            "python3-fonttools is required for code-font glyph validation"
        ) from exc
    with TTFont(path, lazy=True) as font:
        cmap = font.getBestCmap()
        if cmap is None:
            raise RuntimeError(f"font has no usable Unicode cmap: {path}")
        glyph_ids: list[int] = []
        for character in text:
            glyph_name = cmap.get(ord(character))
            if glyph_name is None:
                raise RuntimeError(f"font cmap lacks {character!r}: {path}")
            glyph_ids.append(font.getGlyphID(glyph_name))
    return tuple(glyph_ids)


def validate_glyph_trace(
    trace_xml: str,
    expected: dict[str, tuple[int, ...]],
) -> None:
    """Require one default glyph per literal character in each Fira face."""
    if set(expected) != {"FiraCode-Regular", "FiraCode-Bold"}:
        raise ValueError("fixture requires exactly the Fira Regular and Bold faces")
    try:
        root = ET.fromstring(trace_xml)
    except ET.ParseError as exc:
        raise RuntimeError("MuPDF fixture trace is malformed XML") from exc
    matches = dict.fromkeys(expected, 0)
    for span in root.iter("span"):
        font_name = span.get("font", "").split("+", 1)[-1]
        if font_name not in expected:
            continue
        glyphs = list(span.findall("g"))
        characters = [glyph.get("unicode") for glyph in glyphs]
        if any(character is None for character in characters):
            raise RuntimeError("MuPDF fixture trace contains a glyph without Unicode")
        if "".join(character or "" for character in characters) != AMBIGUOUS_GLYPHS:
            continue
        if len(glyphs) != len(AMBIGUOUS_GLYPHS) or any(
            len(character or "") != 1 for character in characters
        ):
            raise RuntimeError("fixture substituted multiple characters into one glyph")
        try:
            observed = tuple(int(glyph.get("glyph", "")) for glyph in glyphs)
        except ValueError as exc:
            raise RuntimeError("MuPDF fixture trace lacks numeric glyph IDs") from exc
        if observed != expected[font_name]:
            raise RuntimeError(
                "fixture used a contextual alternate instead of the default cmap "
                f"sequence for {font_name}"
            )
        matches[font_name] += 1
    if matches != {"FiraCode-Regular": 1, "FiraCode-Bold": 1}:
        raise RuntimeError(
            "fixture must contain exactly one literal glyph row in each face; "
            f"observed {matches}"
        )


def check_fixture(root: Path) -> None:
    font = load_code_font(root)
    manifest = load_manifest(root / "pdf/guide_manifest.json")
    lualatex = tool("lualatex")
    qpdf = tool("qpdf")
    pdffonts = tool("pdffonts")
    pdftotext = tool("pdftotext")
    mutool = tool("mutool")
    verapdf = tool("verapdf")
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(manifest["source_date_epoch"])
    env["TZ"] = "UTC"
    with tempfile.TemporaryDirectory(prefix="utc-hpc-fira-fixture-") as temporary:
        work = Path(temporary)
        source = work / "fira-code-semantic-fixture.tex"
        source.write_text(fixture_tex(font), encoding="utf-8")
        subprocess.run(
            [
                lualatex,
                "--interaction=nonstopmode",
                "--halt-on-error",
                source.name,
            ],
            cwd=work,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        pdf = source.with_suffix(".pdf")
        subprocess.run([qpdf, "--check", str(pdf)], check=True, capture_output=True)
        fonts = subprocess.run(
            [pdffonts, str(pdf)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        validate_fonts(fonts, {font.regular.postscript_name, font.bold.postscript_name})
        extracted = work / "fixture.txt"
        subprocess.run(
            [
                pdftotext,
                "-fixed",
                f"{font.extraction_pitch:.2f}",
                "-nopgbrk",
                str(pdf),
                str(extracted),
            ],
            check=True,
        )
        observed = extract_unique_span(extracted.read_text(encoding="utf-8"))
        if observed != EXTRACTION_LINES:
            raise RuntimeError(
                f"fixture space extraction changed: {observed!r} != {EXTRACTION_LINES!r}"
            )
        trace = subprocess.run(
            [mutool, "draw", "-q", "-F", "trace", "-o", "-", str(pdf)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        validate_glyph_trace(
            trace,
            {
                font.regular.postscript_name: default_glyph_ids(
                    font.regular.path,
                    AMBIGUOUS_GLYPHS,
                ),
                font.bold.postscript_name: default_glyph_ids(
                    font.bold.path,
                    AMBIGUOUS_GLYPHS,
                ),
            },
        )
        report = subprocess.run(
            [verapdf, "--format", "xml", "--flavour", "ua2", str(pdf)],
            check=True,
            capture_output=True,
        ).stdout
        try:
            report_root = ET.fromstring(report)
        except ET.ParseError as exc:
            raise RuntimeError("fixture veraPDF report is malformed XML") from exc
        validations = report_root.findall(".//validationReport")
        summaries = report_root.findall(".//batchSummary")
        if (
            len(validations) != 1
            or validations[0].get("isCompliant") != "true"
            or len(summaries) != 1
            or summaries[0].get("veraExceptions") != "0"
        ):
            raise RuntimeError("fixture did not pass one clean veraPDF ua2 job")
    print(
        "code_font_fixture_passed "
        f"regular={font.regular.postscript_name} bold={font.bold.postscript_name} "
        f"glyphs_per_row={len(AMBIGUOUS_GLYPHS)} verapdf_profile=ua2"
    )


def main() -> int:
    try:
        root = Path(
            subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        check_fixture(root)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: code-font fixture failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
