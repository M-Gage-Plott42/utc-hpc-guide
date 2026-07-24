#!/usr/bin/env python3
"""Validate PNG structure, decoding, and public asset hygiene."""

from __future__ import annotations

import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
KNOWN_CRITICAL_CHUNKS = {b"IHDR", b"PLTE", b"IDAT", b"IEND"}
ALLOWED_ANCILLARY_CHUNKS = {
    b"cHRM",
    b"gAMA",
    b"iCCP",
    b"sBIT",
    b"sRGB",
    b"bKGD",
    b"hIST",
    b"tRNS",
    b"pHYs",
    b"sPLT",
}
REJECTED_METADATA_CHUNKS = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME"}
MAX_DECODED_BYTES = 256 * 1024 * 1024
UNIQUE_ANCILLARY_CHUNKS = {
    b"cHRM",
    b"gAMA",
    b"iCCP",
    b"sBIT",
    b"sRGB",
    b"bKGD",
    b"hIST",
    b"tRNS",
    b"pHYs",
}
BEFORE_PLTE_AND_IDAT = {b"cHRM", b"gAMA", b"iCCP", b"sBIT", b"sRGB"}
BEFORE_IDAT = {b"bKGD", b"hIST", b"tRNS", b"pHYs", b"sPLT"}
VALID_BIT_DEPTHS = {
    0: {1, 2, 4, 8, 16},
    2: {8, 16},
    3: {1, 2, 4, 8},
    4: {8, 16},
    6: {8, 16},
}
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
ADAM7_PASSES = (
    (0, 0, 8, 8),
    (4, 0, 8, 8),
    (0, 4, 4, 8),
    (2, 0, 4, 4),
    (0, 2, 2, 4),
    (1, 0, 2, 2),
    (0, 1, 1, 2),
)


@dataclass(frozen=True)
class Chunk:
    chunk_type: bytes
    payload: bytes
    offset: int


@dataclass(frozen=True)
class ImageHeader:
    width: int
    height: int
    bit_depth: int
    color_type: int
    interlace: int


def chunk_name(chunk_type: bytes) -> str:
    return chunk_type.decode("ascii", errors="backslashreplace")


def parse_chunks(data: bytes) -> tuple[list[Chunk], list[str]]:
    failures: list[str] = []
    if not data.startswith(PNG_SIGNATURE):
        return [], ["invalid PNG signature"]

    chunks: list[Chunk] = []
    offset = len(PNG_SIGNATURE)
    saw_iend = False
    while offset < len(data):
        if saw_iend:
            failures.append("bytes or chunks found after IEND")
            break
        if len(data) - offset < 12:
            failures.append(f"truncated chunk framing at byte {offset}")
            break
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        if length > 2**31 - 1:
            failures.append(f"chunk length exceeds PNG limit at byte {offset}")
            break
        chunk_type = data[offset + 4:offset + 8]
        if len(chunk_type) != 4 or any(
            not (65 <= value <= 90 or 97 <= value <= 122)
            for value in chunk_type
        ):
            failures.append(f"invalid chunk type at byte {offset}")
            break
        if chunk_type[2] & 0x20:
            failures.append(
                f"{chunk_name(chunk_type)} uses a lowercase reserved chunk-type bit"
            )
        chunk_end = offset + 12 + length
        if chunk_end > len(data):
            failures.append(
                f"truncated {chunk_name(chunk_type)} chunk at byte {offset}"
            )
            break
        payload = data[offset + 8:offset + 8 + length]
        stored_crc = struct.unpack(">I", data[offset + 8 + length:chunk_end])[0]
        calculated_crc = zlib.crc32(chunk_type)
        calculated_crc = zlib.crc32(payload, calculated_crc) & 0xFFFFFFFF
        if stored_crc != calculated_crc:
            failures.append(
                f"{chunk_name(chunk_type)} CRC mismatch at byte {offset}"
            )
        chunks.append(Chunk(chunk_type, payload, offset))
        offset = chunk_end
        saw_iend = chunk_type == b"IEND"

    if not saw_iend:
        failures.append("missing IEND chunk")
    elif offset != len(data):
        failures.append("IEND is not the physical end of file")
    return chunks, failures


def parse_header(chunk: Chunk) -> tuple[ImageHeader | None, list[str]]:
    failures: list[str] = []
    if len(chunk.payload) != 13:
        return None, ["IHDR payload must be exactly 13 bytes"]
    (
        width,
        height,
        bit_depth,
        color_type,
        compression,
        filter_method,
        interlace,
    ) = struct.unpack(">IIBBBBB", chunk.payload)
    if width == 0 or height == 0 or width > 2**31 - 1 or height > 2**31 - 1:
        failures.append("IHDR width and height must be between 1 and 2^31-1")
    if color_type not in VALID_BIT_DEPTHS:
        failures.append(f"IHDR has invalid color type {color_type}")
    elif bit_depth not in VALID_BIT_DEPTHS[color_type]:
        failures.append(
            f"IHDR bit depth {bit_depth} is invalid for color type {color_type}"
        )
    if compression != 0:
        failures.append("IHDR compression method must be 0")
    if filter_method != 0:
        failures.append("IHDR filter method must be 0")
    if interlace not in {0, 1}:
        failures.append("IHDR interlace method must be 0 or 1")
    if failures:
        return None, failures
    return ImageHeader(width, height, bit_depth, color_type, interlace), []


def validate_chunk_policy(
    chunks: list[Chunk],
) -> tuple[ImageHeader | None, bytes, list[str]]:
    failures: list[str] = []
    if not chunks:
        return None, b"", failures
    types = [chunk.chunk_type for chunk in chunks]
    if types[0] != b"IHDR":
        failures.append("IHDR must be the first chunk")
    if types.count(b"IHDR") != 1:
        failures.append("IHDR must appear exactly once")
    if types.count(b"IEND") != 1:
        failures.append("IEND must appear exactly once")
    if types[-1] != b"IEND":
        failures.append("IEND must be the final chunk")
    for chunk in chunks:
        chunk_type = chunk.chunk_type
        if not (chunk_type[0] & 0x20) and chunk_type not in KNOWN_CRITICAL_CHUNKS:
            failures.append(f"unknown critical chunk {chunk_name(chunk_type)}")
        if chunk_type in REJECTED_METADATA_CHUNKS:
            failures.append(f"privacy metadata chunk {chunk_name(chunk_type)} is forbidden")
        elif (chunk_type[0] & 0x20) and chunk_type not in ALLOWED_ANCILLARY_CHUNKS:
            failures.append(f"ancillary chunk {chunk_name(chunk_type)} is not allowlisted")
    for chunk in chunks:
        if chunk.chunk_type == b"IEND" and chunk.payload:
            failures.append("IEND payload must be empty")
    for chunk_type in UNIQUE_ANCILLARY_CHUNKS:
        if types.count(chunk_type) > 1:
            failures.append(f"{chunk_name(chunk_type)} must not appear more than once")
    if b"iCCP" in types and b"sRGB" in types:
        failures.append("iCCP and sRGB must not both appear")

    header: ImageHeader | None = None
    if types and types[0] == b"IHDR":
        header, header_failures = parse_header(chunks[0])
        failures.extend(header_failures)

    plte_indices = [index for index, value in enumerate(types) if value == b"PLTE"]
    idat_indices = [index for index, value in enumerate(types) if value == b"IDAT"]
    if len(plte_indices) > 1:
        failures.append("PLTE must not appear more than once")
    if not idat_indices:
        failures.append("at least one IDAT chunk is required")
    elif idat_indices != list(range(idat_indices[0], idat_indices[-1] + 1)):
        failures.append("IDAT chunks must be consecutive")
    if plte_indices and idat_indices and plte_indices[0] > idat_indices[0]:
        failures.append("PLTE must appear before IDAT")
    first_palette_or_data = min(
        plte_indices[:1] + idat_indices[:1],
        default=len(chunks),
    )
    for index, chunk_type in enumerate(types):
        if chunk_type in BEFORE_PLTE_AND_IDAT and index > first_palette_or_data:
            failures.append(
                f"{chunk_name(chunk_type)} must appear before PLTE and IDAT"
            )
        if chunk_type in BEFORE_IDAT and idat_indices and index > idat_indices[0]:
            failures.append(f"{chunk_name(chunk_type)} must appear before IDAT")

    palette_entries: int | None = None
    if plte_indices:
        palette = chunks[plte_indices[0]].payload
        if not palette or len(palette) % 3 or len(palette) > 768:
            failures.append("PLTE length must be 3 to 768 bytes and divisible by 3")
        else:
            palette_entries = len(palette) // 3
    for dependent in (b"bKGD", b"hIST"):
        dependent_indices = [
            index for index, value in enumerate(types) if value == dependent
        ]
        if dependent_indices and plte_indices and dependent_indices[0] < plte_indices[0]:
            failures.append(
                f"{chunk_name(dependent)} must appear after PLTE when PLTE is present"
            )
    if b"hIST" in types and not plte_indices:
        failures.append("hIST requires PLTE")
    if header:
        if header.color_type == 3 and not plte_indices:
            failures.append("indexed-color PNG requires PLTE")
        if header.color_type in {0, 4} and plte_indices:
            failures.append("grayscale PNG must not contain PLTE")
        if (
            header.color_type == 3
            and palette_entries is not None
            and palette_entries > 2**header.bit_depth
        ):
            failures.append("PLTE has too many entries for indexed-color bit depth")

    trns_indices = [index for index, value in enumerate(types) if value == b"tRNS"]
    if len(trns_indices) > 1:
        failures.append("tRNS must not appear more than once")
    if trns_indices:
        trns_index = trns_indices[0]
        if idat_indices and trns_index > idat_indices[0]:
            failures.append("tRNS must appear before IDAT")
        payload_length = len(chunks[trns_index].payload)
        if header:
            if header.color_type == 0 and payload_length != 2:
                failures.append("grayscale tRNS payload must be 2 bytes")
            elif header.color_type == 2 and payload_length != 6:
                failures.append("truecolor tRNS payload must be 6 bytes")
            elif header.color_type == 3:
                if not plte_indices or plte_indices[0] > trns_index:
                    failures.append("indexed-color tRNS must follow PLTE")
                if palette_entries is not None and payload_length > palette_entries:
                    failures.append("indexed-color tRNS exceeds the palette size")
            elif header.color_type in {4, 6}:
                failures.append("alpha-channel PNG must not contain tRNS")

    compressed = b"".join(
        chunk.payload for chunk in chunks if chunk.chunk_type == b"IDAT"
    )
    return header, compressed, failures


def pass_dimensions(
    width: int,
    height: int,
    start_x: int,
    start_y: int,
    step_x: int,
    step_y: int,
) -> tuple[int, int]:
    pass_width = 0 if width <= start_x else (width - start_x + step_x - 1) // step_x
    pass_height = (
        0 if height <= start_y else (height - start_y + step_y - 1) // step_y
    )
    return pass_width, pass_height


def scanline_layout(header: ImageHeader) -> list[tuple[int, int]]:
    bits_per_pixel = header.bit_depth * CHANNELS[header.color_type]
    layouts: list[tuple[int, int]] = []
    if header.interlace == 0:
        row_bytes = (header.width * bits_per_pixel + 7) // 8
        return [(header.height, row_bytes)]
    for start_x, start_y, step_x, step_y in ADAM7_PASSES:
        pass_width, pass_height = pass_dimensions(
            header.width,
            header.height,
            start_x,
            start_y,
            step_x,
            step_y,
        )
        if pass_width and pass_height:
            row_bytes = (pass_width * bits_per_pixel + 7) // 8
            layouts.append((pass_height, row_bytes))
    return layouts


def validate_decoded_image(header: ImageHeader, compressed: bytes) -> list[str]:
    failures: list[str] = []
    layouts = scanline_layout(header)
    expected_size = sum(rows * (row_bytes + 1) for rows, row_bytes in layouts)
    if expected_size > MAX_DECODED_BYTES:
        return [
            "decoded image exceeds the 256 MiB public-asset validation limit"
        ]
    if not compressed:
        return ["IDAT payload is empty"]
    decoder = zlib.decompressobj()
    try:
        decoded = decoder.decompress(compressed, expected_size + 1)
        if decoder.unconsumed_tail:
            failures.append("decoded image data exceeds expected scanline size")
        decoded += decoder.flush(max(1, expected_size + 1 - len(decoded)))
    except zlib.error as exc:
        return [f"IDAT zlib stream is invalid: {exc}"]
    if not decoder.eof:
        failures.append("IDAT zlib stream did not reach end-of-stream")
    if decoder.unused_data:
        failures.append("IDAT contains bytes after the zlib stream")
    if len(decoded) != expected_size:
        failures.append(
            f"decoded scanline size is {len(decoded)} bytes; expected {expected_size}"
        )
        return failures

    offset = 0
    for rows, row_bytes in layouts:
        for _ in range(rows):
            filter_type = decoded[offset]
            if filter_type > 4:
                failures.append(f"invalid PNG filter type {filter_type}")
            offset += row_bytes + 1
    return failures


def validate_png_bytes(data: bytes) -> list[str]:
    chunks, failures = parse_chunks(data)
    header, compressed, policy_failures = validate_chunk_policy(chunks)
    failures.extend(policy_failures)
    if header and any(chunk.chunk_type == b"IDAT" for chunk in chunks):
        failures.extend(validate_decoded_image(header, compressed))
    return failures


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    asset_root = repo_root / "assets"
    pngs = sorted(asset_root.rglob("*.png"))
    if not pngs:
        print("no_png_assets_found")
        return 0

    failures: list[str] = []
    for path in pngs:
        relative = path.relative_to(repo_root)
        if not path.name.endswith("_sanitized.png"):
            failures.append(
                f"{relative}: filename must end with '_sanitized.png' for public assets"
            )
        for failure in validate_png_bytes(path.read_bytes()):
            failures.append(f"{relative}: {failure}")

    if failures:
        print("asset_policy_failures_detected")
        for item in failures:
            print(f"- {item}")
        return 1
    print(f"asset_policy_clean png_files={len(pngs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
