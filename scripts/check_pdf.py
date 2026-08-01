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
}


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


def validate_fonts(output: str) -> int:
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
    if observed_fonts != EXPECTED_EMBEDDED_FONTS:
        raise RuntimeError(
            "PDF embedded font families changed: "
            f"observed {sorted(observed_fonts)}, "
            f"expected {sorted(EXPECTED_EMBEDDED_FONTS)}"
        )
    return len(rows)


def validate_pdf(pdf: Path, manifest: dict[str, Any]) -> None:
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
        validate_pdf(pdf, manifest)
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
