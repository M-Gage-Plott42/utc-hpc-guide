from __future__ import annotations

import json
import shutil
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.check_code_font_fixture import (
    AMBIGUOUS_GLYPHS,
    EXTRACTION_LINES,
    extract_unique_span,
    fixture_tex,
    validate_glyph_trace,
)
from scripts.code_font import (
    REQUIRED_LIGATURES,
    REQUIRED_RAW_FEATURES,
    _postscript_names,
    fontspec_definition,
    load_code_font,
)


ROOT = Path(__file__).resolve().parents[1]


def minimal_name_font(
    name: str,
    *,
    platform: int = 3,
    version: int = 0,
) -> bytes:
    """Build the smallest bounded sfnt needed for a name-ID-6 unit test."""
    encoded = name.encode("mac_roman" if platform == 1 else "utf-16-be")
    name_table = (
        struct.pack(">HHH", version, 1, 18)
        + struct.pack(">HHHHHH", platform, 1, 0x0409, 6, len(encoded), 0)
        + encoded
    )
    table_offset = 28
    return (
        b"\x00\x01\x00\x00"
        + struct.pack(">HHHH", 1, 0, 0, 0)
        + struct.pack(">4sIII", b"name", 0, table_offset, len(name_table))
        + name_table
    )


class CheckedInCodeFontTests(unittest.TestCase):
    def test_reads_postscript_name_without_release_only_dependencies(self) -> None:
        self.assertEqual(
            _postscript_names(
                minimal_name_font("FiraCode-Regular"),
                label="fixture",
            ),
            {"FiraCode-Regular"},
        )
        self.assertEqual(
            _postscript_names(
                minimal_name_font("FiraCode-Bold", platform=1),
                label="fixture",
            ),
            {"FiraCode-Bold"},
        )

    def test_rejects_malformed_or_unsupported_name_tables(self) -> None:
        with self.assertRaisesRegex(ValueError, "not a readable OpenType font"):
            _postscript_names(b"not-a-font", label="fixture")
        with self.assertRaisesRegex(ValueError, "not a readable OpenType font"):
            _postscript_names(
                minimal_name_font("FiraCode-Regular", version=2),
                label="fixture",
            )

    def test_loads_only_the_selected_fira_source_and_exact_provenance(self) -> None:
        font = load_code_font(ROOT)
        self.assertEqual(font.source_id, "fira-code-6.2")
        self.assertEqual(font.source["release_tag"], "6.2")
        self.assertEqual(
            font.source["release_commit"],
            "eee6db993696aba61ff4eef03698e2987d79910c",
        )
        self.assertEqual(font.source["archive_size"], 2462987)
        self.assertEqual(
            font.source["archive_sha256"],
            "0949915ba8eb24d89fd93d10a7ff623f42830d7c5ffc3ecbf960e4ecad3e3e79",
        )
        self.assertEqual(font.regular.postscript_name, "FiraCode-Regular")
        self.assertEqual(font.bold.postscript_name, "FiraCode-Bold")
        self.assertEqual(font.font_size_pt, 9.1)
        self.assertEqual(font.leading_pt, 11.5)
        self.assertEqual(font.prose_family, "NotoSans")
        self.assertEqual(font.inline_code_family, "DejaVuSansMono")

    def test_canonical_lock_pins_required_host_font_inspection_tools(self) -> None:
        lock = json.loads(
            (ROOT / "pdf/toolchain.lock.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            lock["ubuntu_24_04_qa_packages"]["mupdf-tools"],
            "1.23.10+ds1-1build3",
        )
        self.assertEqual(
            lock["ubuntu_24_04_qa_packages"]["python3-fonttools"],
            "4.46.0-1build2",
        )
        self.assertEqual(
            lock["qa_tools"]["mutool"]["version_line"],
            "mutool version 1.23.10",
        )

    def test_fontspec_definition_contains_the_complete_exact_denylist(self) -> None:
        definition = fontspec_definition(load_code_font(ROOT))
        for feature in REQUIRED_LIGATURES:
            self.assertEqual(definition.count(f"Ligatures={feature}"), 1)
        for feature in REQUIRED_RAW_FEATURES:
            self.assertEqual(definition.count(f"RawFeature={feature}"), 1)
        self.assertIn("UprightFont=*Regular", definition)
        self.assertIn("BoldFont=*Bold", definition)

    def test_fixture_is_isolated_and_exercises_both_faces_and_spaces(self) -> None:
        source = fixture_tex(load_code_font(ROOT))
        self.assertEqual(source.count(AMBIGUOUS_GLYPHS), 2)
        self.assertIn(r"\bfseries", source)
        self.assertIn("    indented child", source)
        self.assertIn("column-a  column-b", source)
        self.assertNotIn("UTC_HPC_Guide", source)

    def test_extracts_exact_indentation_and_interior_spaces(self) -> None:
        text = "\n".join(f"      {line}" for line in EXTRACTION_LINES)
        self.assertEqual(extract_unique_span(text), EXTRACTION_LINES)

    def glyph_trace(self) -> tuple[str, dict[str, tuple[int, ...]]]:
        root = ET.Element("page")
        expected: dict[str, tuple[int, ...]] = {}
        for font_name in ("FiraCode-Regular", "FiraCode-Bold"):
            span = ET.SubElement(root, "span", font=f"PREFIX+{font_name}")
            glyph_ids = tuple(range(1, len(AMBIGUOUS_GLYPHS) + 1))
            expected[font_name] = glyph_ids
            for character, glyph_id in zip(AMBIGUOUS_GLYPHS, glyph_ids):
                ET.SubElement(
                    span,
                    "g",
                    unicode=character,
                    glyph=str(glyph_id),
                )
        return ET.tostring(root, encoding="unicode"), expected

    def test_glyph_trace_requires_one_default_glyph_per_character(self) -> None:
        trace, expected = self.glyph_trace()
        validate_glyph_trace(trace, expected)

        root = ET.fromstring(trace)
        bold = root.findall("span")[1]
        bold.findall("g")[4].set("glyph", "999")
        with self.assertRaisesRegex(RuntimeError, "contextual alternate"):
            validate_glyph_trace(
                ET.tostring(root, encoding="unicode"),
                expected,
            )

    def test_glyph_trace_rejects_multi_character_substitution(self) -> None:
        trace, expected = self.glyph_trace()
        root = ET.fromstring(trace)
        regular = root.findall("span")[0]
        glyphs = regular.findall("g")
        glyphs[0].set(
            "unicode",
            (glyphs[0].get("unicode") or "")
            + (glyphs[1].get("unicode") or ""),
        )
        regular.remove(glyphs[1])
        with self.assertRaisesRegex(RuntimeError, "multiple characters"):
            validate_glyph_trace(
                ET.tostring(root, encoding="unicode"),
                expected,
            )


class CodeFontFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        target = self.root / "pdf"
        target.mkdir()
        shutil.copy2(ROOT / "pdf/toolchain.lock.json", target)
        shutil.copytree(
            ROOT / "pdf/fonts/fira-code-6.2",
            target / "fonts/fira-code-6.2",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def lock_path(self) -> Path:
        return self.root / "pdf/toolchain.lock.json"

    def read_lock(self) -> dict[str, object]:
        return json.loads(self.lock_path.read_text(encoding="utf-8"))

    def write_lock(self, lock: dict[str, object]) -> None:
        self.lock_path.write_text(
            json.dumps(lock, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_rejects_an_incomplete_ligature_or_raw_feature_denylist(self) -> None:
        for key, removed, message in (
            ("fontspec_ligatures", "ContextualOff", "full denylist"),
            ("raw_features", "-calt", "full denylist"),
        ):
            with self.subTest(key=key):
                lock = self.read_lock()
                config = lock["code_font"]
                assert isinstance(config, dict)
                values = config[key]
                assert isinstance(values, list)
                values.remove(removed)
                self.write_lock(lock)
                with self.assertRaisesRegex(ValueError, message):
                    load_code_font(self.root)
                shutil.copy2(ROOT / "pdf/toolchain.lock.json", self.lock_path)

    def test_rejects_tampered_or_link_replaced_font_bytes(self) -> None:
        regular = self.root / "pdf/fonts/fira-code-6.2/FiraCode-Regular.ttf"
        regular.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "size mismatch"):
            load_code_font(self.root)

        shutil.copy2(
            ROOT / "pdf/fonts/fira-code-6.2/FiraCode-Regular.ttf",
            regular,
        )
        external = self.root / "external.ttf"
        shutil.copy2(regular, external)
        regular.unlink()
        regular.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "without symbolic links"):
            load_code_font(self.root)


if __name__ == "__main__":
    unittest.main()
