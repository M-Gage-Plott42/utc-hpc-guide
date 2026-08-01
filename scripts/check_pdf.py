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
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    from .build_pdf import locked_tex_font_paths
    from .font_proofs import (
        effective_manifest,
        load_proof_context,
        proof_output_path,
    )
    from .pdf_manifest import load_manifest, output_path
except ImportError:
    from build_pdf import locked_tex_font_paths
    from font_proofs import (
        effective_manifest,
        load_proof_context,
        proof_output_path,
    )
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
}
PROOF_EXTRACTION_SPANS = (
    (
        "Host hpc",
        "    ServerAliveCountMax 120",
        (
            "Host hpc",
            "    HostName REPLACE_WITH_LOGIN_HOST",
            "    User REPLACE_WITH_USERNAME",
            "    IdentityFile ~/.ssh/id_ed25519",
            "    ServerAliveInterval 60",
            "    ServerAliveCountMax 120",
        ),
    ),
    (
        'curl --fail --location --output "$INSTALLER" "$INSTALLER_URL"',
        'bash "$INSTALLER" -b -p "$INSTALL_ROOT"',
        (
            'curl --fail --location --output "$INSTALLER" "$INSTALLER_URL"',
            "printf '%s  %s\\n' \"$INSTALLER_SHA256\" \"$INSTALLER\" | sha256sum --check -",
            'bash "$INSTALLER" -b -p "$INSTALL_ROOT"',
        ),
    ),
    (
        "EXTRACTION-PROOF-START",
        "EXTRACTION-PROOF-END",
        (
            "EXTRACTION-PROOF-START",
            "root",
            "    indented child",
            "column-a  column-b",
            "EXTRACTION-PROOF-END",
        ),
    ),
)
AMBIGUOUS_GLYPH_PROOF = (
    "0 O o 1 l I | < > <= >= == != -> -- _ ~ \\ / ' \" ( ) [ ] { }"
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


def extract_unique_fixed_span(
    extracted: str,
    start: str,
    end: str,
) -> tuple[str, ...]:
    """Return one marker-bounded span while retaining relative ASCII spaces."""
    lines = [line.rstrip() for line in extracted.splitlines()]
    normalized_start = start.lstrip(" ")
    normalized_end = end.lstrip(" ")
    starts = [
        index
        for index, line in enumerate(lines)
        if line.lstrip(" ") == normalized_start
    ]
    if len(starts) != 1:
        raise RuntimeError(
            f"fixed-pitch extraction anchor must occur once: {start!r} "
            f"(found {len(starts)})"
        )
    start_index = starts[0]
    ends = [
        index
        for index in range(start_index, len(lines))
        if lines[index].lstrip(" ") == normalized_end
    ]
    if len(ends) != 1:
        raise RuntimeError(
            f"fixed-pitch extraction anchor must occur once after {start!r}: "
            f"{end!r} (found {len(ends)})"
        )
    margin = len(lines[start_index]) - len(lines[start_index].lstrip(" "))
    normalized: list[str] = []
    for line in lines[start_index : ends[0] + 1]:
        if not line.strip():
            continue
        prefix = " " * margin
        if margin and not line.startswith(prefix):
            raise RuntimeError(
                "fixed-pitch extraction changed the common code-block margin"
            )
        normalized.append(line[margin:])
    return tuple(normalized)


def validate_proof_extraction(extracted: str) -> None:
    """Check exact Poppler fixed-pitch extraction for meaningful spaces."""
    for start, end, expected in PROOF_EXTRACTION_SPANS:
        observed = extract_unique_fixed_span(extracted, start, end)
        if observed != expected:
            raise RuntimeError(
                "fixed-pitch extraction fidelity changed for "
                f"{start!r}: observed {observed!r}, expected {expected!r}"
            )


def default_glyph_ids(font_path: Path, text: str) -> tuple[int, ...]:
    """Return each character's default cmap glyph ID from one pinned TTF."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError(
            "python3-fonttools is required for default-glyph validation"
        ) from exc
    try:
        with TTFont(font_path, lazy=True) as font:
            cmap = font.getBestCmap()
            if cmap is None:
                raise RuntimeError(f"font has no usable Unicode cmap: {font_path}")
            glyph_ids: list[int] = []
            for character in text:
                glyph_name = cmap.get(ord(character))
                if glyph_name is None:
                    raise RuntimeError(
                        f"font cmap lacks {character!r}: {font_path}"
                    )
                glyph_ids.append(font.getGlyphID(glyph_name))
            return tuple(glyph_ids)
    except (OSError, KeyError) as exc:
        raise RuntimeError(f"could not read pinned font: {font_path}") from exc


def validate_one_glyph_per_character(
    trace_xml: str,
    expected_glyphs: dict[str, tuple[int, ...]],
) -> None:
    """Require one default cmap glyph for each character in both proof rows."""
    if len(expected_glyphs) != 2 or any(
        len(glyphs) != len(AMBIGUOUS_GLYPH_PROOF)
        for glyphs in expected_glyphs.values()
    ):
        raise ValueError("exactly two complete default-glyph sequences are required")
    try:
        root = ET.fromstring(trace_xml)
    except ET.ParseError as exc:
        raise RuntimeError("MuPDF glyph trace is malformed XML") from exc
    matches: dict[str, int] = dict.fromkeys(expected_glyphs, 0)
    for span in root.iter("span"):
        font = span.get("font", "").split("+", 1)[-1]
        if font not in matches:
            continue
        glyphs = list(span.findall("g"))
        characters = [glyph.get("unicode") for glyph in glyphs]
        if any(character is None for character in characters):
            raise RuntimeError("MuPDF glyph trace contains a glyph without Unicode")
        text = "".join(character or "" for character in characters)
        if text != AMBIGUOUS_GLYPH_PROOF:
            continue
        if len(glyphs) != len(AMBIGUOUS_GLYPH_PROOF) or any(
            len(character or "") != 1 for character in characters
        ):
            raise RuntimeError(
                "font proof substituted multiple typed characters into one glyph"
            )
        try:
            observed_glyphs = tuple(
                int(glyph_id)
                for glyph in glyphs
                if (glyph_id := glyph.get("glyph")) is not None
            )
        except ValueError as exc:
            raise RuntimeError(
                "MuPDF glyph trace lacks numeric glyph identifiers"
            ) from exc
        if len(observed_glyphs) != len(glyphs):
            raise RuntimeError(
                "MuPDF glyph trace lacks numeric glyph identifiers"
            )
        if observed_glyphs != expected_glyphs[font]:
            raise RuntimeError(
                "font proof used a contextual alternate instead of the default "
                f"cmap glyph sequence for {font}"
            )
        matches[font] += 1
    if matches != dict.fromkeys(expected_glyphs, 1):
        raise RuntimeError(
            "font proof must contain exactly one one-glyph-per-character row "
            f"in each pinned face; observed {matches}"
        )


def validate_pdf(
    pdf: Path,
    manifest: dict[str, Any],
    *,
    expected_fonts: set[str] | frozenset[str] = EXPECTED_EMBEDDED_FONTS,
    extraction_pitch: float | None = None,
    glyph_fonts: tuple[tuple[str, Path], tuple[str, Path]] | None = None,
) -> None:
    qpdf = tool("qpdf")
    pdfinfo = tool("pdfinfo")
    pdftotext = tool("pdftotext")
    pdffonts = tool("pdffonts")
    pdftoppm = tool("pdftoppm")

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

    font_count = validate_fonts(
        run_text([pdffonts, str(pdf)]),
        expected_fonts,
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

        if extraction_pitch is not None:
            if not 3.0 <= extraction_pitch <= 10.0:
                raise ValueError("proof extraction pitch must be from 3 through 10")
            fixed_text_path = temp_path / "guide-fixed.txt"
            subprocess.run(
                [
                    pdftotext,
                    "-fixed",
                    f"{extraction_pitch:.2f}",
                    "-nopgbrk",
                    str(pdf),
                    str(fixed_text_path),
                ],
                check=True,
            )
            validate_proof_extraction(
                fixed_text_path.read_text(encoding="utf-8")
            )
            if glyph_fonts is None:
                raise ValueError("proof glyph font names are required")
            mutool = tool("mutool")
            trace = run_text(
                [
                    mutool,
                    "draw",
                    "-q",
                    "-F",
                    "trace",
                    "-o",
                    "-",
                    str(pdf),
                    str(pages),
                ]
            )
            expected_glyphs = {
                postscript: default_glyph_ids(path, AMBIGUOUS_GLYPH_PROOF)
                for postscript, path in glyph_fonts
            }
            validate_one_glyph_per_character(trace, expected_glyphs)

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
    parser.add_argument(
        "--proof-config",
        type=Path,
        default=Path("pdf/font_proofs.json"),
    )
    parser.add_argument("--proof-profile")
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
        base_manifest = load_manifest(manifest_path)
        expected_fonts = set(EXPECTED_EMBEDDED_FONTS)
        extraction_pitch: float | None = None
        glyph_fonts: tuple[tuple[str, Path], tuple[str, Path]] | None = None
        if args.proof_profile:
            proof_config = args.proof_config
            if not proof_config.is_absolute():
                proof_config = root / proof_config
            proof = load_proof_context(
                root,
                proof_config,
                args.proof_profile,
                manifest_path,
            )
            manifest = effective_manifest(base_manifest, proof)
            default_pdf = proof_output_path(root, proof)
            expected_fonts.update(
                {
                    proof.profile.regular_postscript,
                    proof.profile.bold_postscript,
                }
            )
            extraction_pitch = proof.profile.extraction_pitch
            if proof.regular_font_path is None or proof.bold_font_path is None:
                regular_path, bold_path = locked_tex_font_paths(
                    root,
                    ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf"),
                )
            else:
                regular_path = proof.regular_font_path
                bold_path = proof.bold_font_path
            glyph_fonts = (
                (proof.profile.regular_postscript, regular_path),
                (proof.profile.bold_postscript, bold_path),
            )
        else:
            manifest = base_manifest
            default_pdf = output_path(root, manifest)
        pdf = args.pdf or default_pdf
        if not pdf.is_absolute():
            pdf = root / pdf
        if pdf.resolve() != default_pdf.resolve():
            raise ValueError(
                "PDF path must match the manifest/profile-derived output path"
            )
        validate_pdf(
            pdf,
            manifest,
            expected_fonts=expected_fonts,
            extraction_pitch=extraction_pitch,
            glyph_fonts=glyph_fonts,
        )
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
