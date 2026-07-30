from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from scripts.check_assets import validate_asset_tree, validate_png_bytes


def png_chunk(chunk_type: bytes, payload: bytes, crc_delta: int = 0) -> bytes:
    checksum = zlib.crc32(chunk_type)
    checksum = (zlib.crc32(payload, checksum) + crc_delta) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", checksum)
    )


def valid_png(
    *,
    before_idat: tuple[bytes, ...] = (),
    idat_payload: bytes | None = None,
    iend_payload: bytes = b"",
) -> bytes:
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    image_data = zlib.compress(b"\x00\x00\x00\x00")
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            png_chunk(b"IHDR", header),
            *before_idat,
            png_chunk(b"IDAT", image_data if idat_payload is None else idat_payload),
            png_chunk(b"IEND", iend_payload),
        )
    )


class AssetCheckerTests(unittest.TestCase):
    def test_accepts_minimal_decodable_png(self) -> None:
        self.assertEqual(validate_png_bytes(valid_png()), [])

    def test_rejects_crc_mismatch(self) -> None:
        header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        data = (
            b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", header, crc_delta=1)
            + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
            + png_chunk(b"IEND", b"")
        )
        self.assertTrue(any("CRC mismatch" in item for item in validate_png_bytes(data)))

    def test_rejects_duplicate_ihdr_and_nonconsecutive_idat(self) -> None:
        header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        data = (
            b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", header)
            + png_chunk(b"IHDR", header)
            + png_chunk(b"IDAT", zlib.compress(b"\x00\x00"))
            + png_chunk(b"pHYs", struct.pack(">IIB", 1, 1, 0))
            + png_chunk(b"IDAT", zlib.compress(b"\x00\x00"))
            + png_chunk(b"IEND", b"")
        )
        failures = validate_png_bytes(data)
        self.assertIn("IHDR must appear exactly once", failures)
        self.assertIn("IDAT chunks must be consecutive", failures)

    def test_rejects_nonempty_iend_and_trailing_bytes(self) -> None:
        failures = validate_png_bytes(valid_png(iend_payload=b"x") + b"trailing")
        self.assertIn("IEND payload must be empty", failures)
        self.assertIn("IEND is not the physical end of file", failures)

    def test_rejects_privacy_metadata_and_unknown_ancillary_chunks(self) -> None:
        failures = validate_png_bytes(
            valid_png(
                before_idat=(
                    png_chunk(b"tEXt", b"Author\x00Example"),
                    png_chunk(b"vpAg", b"x"),
                )
            )
        )
        self.assertIn("privacy metadata chunk tEXt is forbidden", failures)
        self.assertIn("ancillary chunk vpAg is not allowlisted", failures)

    def test_rejects_invalid_zlib_and_filter_streams(self) -> None:
        zlib_failures = validate_png_bytes(valid_png(idat_payload=b"not-zlib"))
        self.assertTrue(any("zlib stream is invalid" in item for item in zlib_failures))
        filter_failures = validate_png_bytes(
            valid_png(idat_payload=zlib.compress(b"\x05\x00\x00\x00"))
        )
        self.assertIn("invalid PNG filter type 5", filter_failures)

    def test_rejects_empty_idat_and_oversized_decoded_image(self) -> None:
        self.assertIn("IDAT payload is empty", validate_png_bytes(valid_png(idat_payload=b"")))
        header = struct.pack(">IIBBBBB", 20000, 20000, 8, 6, 0, 0, 0)
        data = (
            b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", header)
            + png_chunk(b"IDAT", zlib.compress(b"\x00"))
            + png_chunk(b"IEND", b"")
        )
        self.assertIn(
            "decoded image exceeds the 256 MiB public-asset validation limit",
            validate_png_bytes(data),
        )

    def test_rejects_duplicate_and_misordered_ancillary_chunks(self) -> None:
        gamma = png_chunk(b"gAMA", struct.pack(">I", 45455))
        physical = png_chunk(b"pHYs", struct.pack(">IIB", 1, 1, 0))
        data = valid_png(before_idat=(gamma, gamma))
        self.assertIn("gAMA must not appear more than once", validate_png_bytes(data))

        header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        data = (
            b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", header)
            + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
            + physical
            + png_chunk(b"IEND", b"")
        )
        self.assertIn("pHYs must appear before IDAT", validate_png_bytes(data))

    def test_asset_tree_allows_documented_sanitized_pngs_and_readme(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset_dir = root / "assets" / "ood"
            asset_dir.mkdir(parents=True)
            (asset_dir / "README.md").write_text("Asset notes.\n", encoding="utf-8")
            image = asset_dir / "example_sanitized.png"
            image.write_bytes(valid_png())

            pngs, failures = validate_asset_tree(root)

            self.assertEqual(pngs, [image])
            self.assertEqual(failures, [])

    def test_asset_tree_rejects_uppercase_and_unexpected_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset_dir = root / "assets" / "ood"
            asset_dir.mkdir(parents=True)
            (asset_dir / "upper_sanitized.PNG").write_bytes(valid_png())
            (asset_dir / "vector_sanitized.svg").write_text("<svg/>\n", encoding="utf-8")

            pngs, failures = validate_asset_tree(root)

            self.assertEqual(pngs, [])
            self.assertEqual(len(failures), 2)
            self.assertTrue(any("upper_sanitized.PNG" in item for item in failures))
            self.assertTrue(any("vector_sanitized.svg" in item for item in failures))

    def test_asset_tree_rejects_unexpected_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset_dir = root / "assets" / "ood"
            asset_dir.mkdir(parents=True)
            (asset_dir / "NOTES.md").write_text("Not allowlisted.\n", encoding="utf-8")

            _, failures = validate_asset_tree(root)

            self.assertEqual(len(failures), 1)
            self.assertIn("assets/ood/NOTES.md", failures[0])


if __name__ == "__main__":
    unittest.main()
