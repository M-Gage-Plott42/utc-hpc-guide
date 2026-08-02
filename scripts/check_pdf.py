#!/usr/bin/env python3
"""Validate PDF structure, metadata, fonts, text, and rendering."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from .pdf_manifest import load_manifest, output_path
except ImportError:
    from pdf_manifest import load_manifest, output_path


FONT_FLAGS = re.compile(
    r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$",
    re.IGNORECASE,
)
EXPECTED_EMBEDDED_FONTS = {
    "NotoSans-Bold",
    "NotoSans-Regular",
    "DejaVuSansMono",
    "DejaVuSansMono-Bold",
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


def validate_pdf(pdf: Path, manifest: dict[str, Any], root: Path) -> None:
    qpdf = tool("qpdf")
    pdfinfo = tool("pdfinfo")
    pdftotext = tool("pdftotext")
    pdffonts = tool("pdffonts")
    pdftoppm = tool("pdftoppm")
    pandoc = tool("pandoc")

    validate_code_filter_contract(pandoc, root / manifest["code_filter_source"])

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
