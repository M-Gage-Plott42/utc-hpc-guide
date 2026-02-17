#!/usr/bin/env python3
"""Validate PNG asset hygiene for public release."""

from __future__ import annotations

import struct
import sys
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
METADATA_CHUNKS = {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}


def png_metadata_chunks(path: Path) -> list[str]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        return ["invalid_png_signature"]

    chunks: list[str] = []
    idx = len(PNG_SIGNATURE)

    while idx + 8 <= len(data):
        length = struct.unpack(">I", data[idx : idx + 4])[0]
        chunk_type = data[idx + 4 : idx + 8]
        idx += 8

        if idx + length + 4 > len(data):
            chunks.append("truncated_png_chunk")
            break

        idx += length  # chunk payload
        idx += 4  # CRC

        if chunk_type in METADATA_CHUNKS:
            chunks.append(chunk_type.decode("ascii"))

        if chunk_type == b"IEND":
            break

    return chunks


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    asset_root = repo_root / "assets"
    pngs = sorted(asset_root.rglob("*.png"))

    if not pngs:
        print("no_png_assets_found")
        return 0

    failures: list[str] = []

    for path in pngs:
        rel = path.relative_to(repo_root)
        if not path.name.endswith("_sanitized.png"):
            failures.append(
                f"{rel}: filename must end with '_sanitized.png' for public assets"
            )

        metadata = png_metadata_chunks(path)
        if metadata:
            failures.append(
                f"{rel}: metadata/non-clean PNG chunks detected: {', '.join(metadata)}"
            )

    if failures:
        print("asset_policy_failures_detected")
        for item in failures:
            print(f"- {item}")
        return 1

    print("asset_policy_clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
