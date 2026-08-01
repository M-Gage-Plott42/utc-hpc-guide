from __future__ import annotations

import unittest

from scripts.check_pdf import (
    AMBIGUOUS_GLYPH_PROOF,
    extract_unique_fixed_span,
    validate_one_glyph_per_character,
    validate_proof_extraction,
)


class FixedPitchExtractionTests(unittest.TestCase):
    def passing_text(self) -> str:
        return """\
 page prose
 Host hpc
     HostName REPLACE_WITH_LOGIN_HOST
     User REPLACE_WITH_USERNAME
     IdentityFile ~/.ssh/id_ed25519
     ServerAliveInterval 60
     ServerAliveCountMax 120

 curl --fail --location --output "$INSTALLER" "$INSTALLER_URL"
 printf '%s  %s\\n' "$INSTALLER_SHA256" "$INSTALLER" | sha256sum --check -
 bash "$INSTALLER" -b -p "$INSTALL_ROOT"

 EXTRACTION-PROOF-START
 root
     indented child
 column-a  column-b
 EXTRACTION-PROOF-END
"""

    def test_accepts_exact_relative_indentation_and_interior_spaces(self) -> None:
        validate_proof_extraction(self.passing_text())

    def test_discards_blank_layout_rows_and_common_left_margin(self) -> None:
        text = """\
   START

       child
   END
"""
        self.assertEqual(
            extract_unique_fixed_span(text, "START", "END"),
            ("START", "    child", "END"),
        )

    def test_rejects_changed_indentation(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "fidelity changed"):
            validate_proof_extraction(
                self.passing_text().replace(
                    "     HostName",
                    "      HostName",
                )
            )

    def test_rejects_changed_interior_spaces(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "fidelity changed"):
            validate_proof_extraction(
                self.passing_text().replace("column-a  column-b", "column-a column-b")
            )

    def test_rejects_missing_or_duplicate_anchor(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "must occur once"):
            validate_proof_extraction(
                self.passing_text().replace("EXTRACTION-PROOF-START", "MISSING")
            )
        with self.assertRaisesRegex(RuntimeError, "must occur once"):
            validate_proof_extraction(
                self.passing_text() + "\nEXTRACTION-PROOF-START\n"
            )


class GlyphTraceTests(unittest.TestCase):
    def trace(self, regular_glyphs: str, bold_glyphs: str) -> str:
        return (
            "<document><span font='ABCDEF+FiraCode-Regular'>"
            f"{regular_glyphs}</span>"
            "<span font='ABCDEF+FiraCode-Bold'>"
            f"{bold_glyphs}</span></document>"
        )

    def glyphs(self, text: str, glyph_ids: tuple[int, ...]) -> str:
        import xml.sax.saxutils

        self.assertEqual(len(text), len(glyph_ids))
        return "".join(
            f"<g unicode={xml.sax.saxutils.quoteattr(character)} "
            f"glyph={xml.sax.saxutils.quoteattr(str(glyph_id))}/>"
            for character, glyph_id in zip(text, glyph_ids, strict=True)
        )

    def expected(self) -> dict[str, tuple[int, ...]]:
        count = len(AMBIGUOUS_GLYPH_PROOF)
        return {
            "FiraCode-Regular": tuple(range(1, count + 1)),
            "FiraCode-Bold": tuple(range(101, 101 + count)),
        }

    def test_accepts_one_glyph_per_character_in_both_weights(self) -> None:
        expected = self.expected()
        validate_one_glyph_per_character(
            self.trace(
                self.glyphs(AMBIGUOUS_GLYPH_PROOF, expected["FiraCode-Regular"]),
                self.glyphs(AMBIGUOUS_GLYPH_PROOF, expected["FiraCode-Bold"]),
            ),
            expected,
        )

    def test_rejects_contextual_multi_character_glyph(self) -> None:
        expected = self.expected()
        regular = self.glyphs(
            AMBIGUOUS_GLYPH_PROOF,
            expected["FiraCode-Regular"],
        )
        pair_start = AMBIGUOUS_GLYPH_PROOF.index("!=")
        pair = self.glyphs(
            "!=",
            expected["FiraCode-Regular"][pair_start : pair_start + 2],
        )
        ligated = regular.replace(pair, '<g unicode="!=" glyph="999"/>')
        with self.assertRaisesRegex(RuntimeError, "multiple typed characters"):
            validate_one_glyph_per_character(
                self.trace(
                    ligated,
                    self.glyphs(
                        AMBIGUOUS_GLYPH_PROOF,
                        expected["FiraCode-Bold"],
                    ),
                ),
                expected,
            )

    def test_rejects_one_character_contextual_alternate(self) -> None:
        expected = self.expected()
        regular = self.glyphs(
            AMBIGUOUS_GLYPH_PROOF,
            expected["FiraCode-Regular"],
        ).replace('unicode="&lt;" glyph="15"', 'unicode="&lt;" glyph="999"', 1)
        with self.assertRaisesRegex(RuntimeError, "contextual alternate"):
            validate_one_glyph_per_character(
                self.trace(
                    regular,
                    self.glyphs(
                        AMBIGUOUS_GLYPH_PROOF,
                        expected["FiraCode-Bold"],
                    ),
                ),
                expected,
            )

    def test_rejects_missing_or_wrong_weight_row(self) -> None:
        expected = self.expected()
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            validate_one_glyph_per_character(
                self.trace(
                    self.glyphs(
                        AMBIGUOUS_GLYPH_PROOF,
                        expected["FiraCode-Regular"],
                    ),
                    "",
                ),
                expected,
            )


if __name__ == "__main__":
    unittest.main()
