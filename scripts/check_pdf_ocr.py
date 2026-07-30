#!/usr/bin/env python3
"""Render every PDF page and verify that its visible text survives OCR."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

try:
    from .pdf_manifest import load_manifest, output_path
except ImportError:
    from pdf_manifest import load_manifest, output_path


def tool(name: str) -> str:
    result = shutil.which(name)
    if not result:
        raise RuntimeError(f"required PDF OCR tool is not available: {name}")
    return result


def normalize_ocr_text(text: str) -> str:
    """Normalize OCR output for resilient phrase comparisons."""
    decomposed = unicodedata.normalize("NFKD", text).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", decomposed))


def validate_ocr_pages(
    page_texts: list[str],
    required_text: list[str],
    min_page_alnum: int,
) -> None:
    if not page_texts:
        raise RuntimeError("OCR produced no pages")
    for page_number, page_text in enumerate(page_texts, start=1):
        alnum_count = sum(character.isalnum() for character in page_text)
        if alnum_count < min_page_alnum:
            raise RuntimeError(
                "OCR found too little text on "
                f"page {page_number}: {alnum_count} alphanumeric characters "
                f"(minimum {min_page_alnum})"
            )

    combined = normalize_ocr_text("\n".join(page_texts))
    for required in required_text:
        normalized_required = normalize_ocr_text(required)
        if not normalized_required:
            raise ValueError("required_ocr_text entries must contain letters or digits")
        if normalized_required not in combined:
            raise RuntimeError(f"required OCR text is missing: {required}")


def rendered_page_number(path: Path) -> int:
    match = re.search(r"-(\d+)\.png$", path.name)
    if not match:
        raise RuntimeError(f"unexpected rendered page name: {path.name}")
    return int(match.group(1))


def validate_pdf_ocr(pdf: Path, manifest: dict[str, Any]) -> None:
    pdftoppm = tool("pdftoppm")
    tesseract = tool("tesseract")
    dpi = manifest.get("ocr_dpi")
    min_page_alnum = manifest.get("ocr_min_alnum_per_page")
    required_text = manifest.get("required_ocr_text")

    if not isinstance(dpi, int) or not 72 <= dpi <= 600:
        raise ValueError("ocr_dpi must be an integer from 72 through 600")
    if not isinstance(min_page_alnum, int) or min_page_alnum < 1:
        raise ValueError("ocr_min_alnum_per_page must be a positive integer")
    if (
        not isinstance(required_text, list)
        or not required_text
        or not all(isinstance(item, str) for item in required_text)
    ):
        raise ValueError("required_ocr_text must be a nonempty list of strings")

    with tempfile.TemporaryDirectory(prefix="utc-hpc-pdf-ocr-") as temp:
        render_prefix = Path(temp) / "page"
        subprocess.run(
            [
                pdftoppm,
                "-png",
                "-r",
                str(dpi),
                str(pdf),
                str(render_prefix),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        rendered = sorted(
            Path(temp).glob("page-*.png"),
            key=rendered_page_number,
        )
        if not rendered:
            raise RuntimeError("pdftoppm rendered no pages for OCR")

        page_texts: list[str] = []
        for page in rendered:
            result = subprocess.run(
                [
                    tesseract,
                    str(page),
                    "stdout",
                    "--dpi",
                    str(dpi),
                    "-l",
                    "eng",
                    "--psm",
                    "3",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            page_texts.append(result.stdout)

    validate_ocr_pages(page_texts, required_text, min_page_alnum)
    print(
        "pdf_ocr_passed "
        f"pages={len(page_texts)} dpi={dpi} "
        f"min_page_alnum={min_page_alnum}"
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
        validate_pdf_ocr(pdf, manifest)
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ERROR: PDF OCR failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
