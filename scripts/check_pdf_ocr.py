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
    from .font_proofs import (
        effective_manifest,
        load_proof_context,
        proof_output_path,
    )
    from .pdf_manifest import load_manifest, output_path
except ImportError:
    from font_proofs import (
        effective_manifest,
        load_proof_context,
        proof_output_path,
    )
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
    required_page_text: dict[int, list[str]] | None = None,
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

    for page_number, phrases in (required_page_text or {}).items():
        if not 1 <= page_number <= len(page_texts):
            raise RuntimeError(
                "page-specific OCR requirement references missing "
                f"page {page_number}"
            )
        normalized_page = normalize_ocr_text(page_texts[page_number - 1])
        for phrase in phrases:
            normalized_phrase = normalize_ocr_text(phrase)
            if not normalized_phrase:
                raise ValueError(
                    "required_page_ocr_text entries must contain letters or digits"
                )
            if normalized_phrase not in normalized_page:
                raise RuntimeError(
                    "required OCR text is missing from "
                    f"page {page_number}: {phrase}"
                )


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
    raw_required_page_text = manifest.get("required_page_ocr_text")

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
    if (
        not isinstance(raw_required_page_text, dict)
        or not raw_required_page_text
    ):
        raise ValueError("required_page_ocr_text must be a nonempty object")
    required_page_text: dict[int, list[str]] = {}
    for raw_page, phrases in raw_required_page_text.items():
        if (
            not isinstance(raw_page, str)
            or re.fullmatch(r"[1-9][0-9]*", raw_page) is None
            or not isinstance(phrases, list)
            or not phrases
            or not all(isinstance(phrase, str) for phrase in phrases)
        ):
            raise ValueError(
                "required_page_ocr_text must map positive page-number "
                "strings to nonempty string lists"
            )
        required_page_text[int(raw_page)] = phrases

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

    validate_ocr_pages(
        page_texts,
        required_text,
        min_page_alnum,
        required_page_text,
    )
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
