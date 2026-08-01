from __future__ import annotations

import shlex
import subprocess
import unittest
from pathlib import Path

from scripts.build_pdf import assemble_markdown, proof_font_definition
from scripts.check_code_width import overlong_fenced_code_lines
from scripts.font_proofs import effective_manifest, load_proof_context


ROOT = Path(__file__).resolve().parents[1]


class FontProofAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_proof_context(
            ROOT,
            ROOT / "pdf/font_proofs.json",
            "cascadia-mono",
            ROOT / "pdf/guide_manifest.json",
        )
        cls.manifest = effective_manifest(cls.context.base_manifest, cls.context)
        cls.assembled = assemble_markdown(ROOT, cls.manifest, cls.context)

    def transform(self, path: str) -> list[tuple[str, str]]:
        return [
            (item.original, item.replacement)
            for item in self.context.source_transforms
            if item.path == path
        ]

    def test_proof_wraps_only_assembly_and_keeps_every_code_line_at_80(self) -> None:
        self.assertEqual(overlong_fenced_code_lines(self.assembled), [])
        for transform in self.context.source_transforms:
            self.assertNotIn(transform.original, self.assembled)
            self.assertIn(transform.replacement, self.assembled)
            canonical = (ROOT / transform.path).read_text(encoding="utf-8")
            self.assertIn(transform.original, canonical)
            self.assertNotIn(transform.replacement, canonical)

    def test_wrapped_checksum_evaluates_to_the_original_digest(self) -> None:
        original, replacement = self.transform("docs/05-python-envs.md")[0]
        expected = original.split('="', 1)[1][:-1]
        result = subprocess.run(
            ["bash", "-c", replacement + '; printf %s "$INSTALLER_SHA256"'],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout, expected)

    def test_wrapped_slurm_fields_and_pip_tokens_are_semantically_equal(self) -> None:
        slurm_original, slurm_replacement = self.transform(
            "docs/03-slurm-basics.md"
        )[0]
        expected_fields = slurm_original.split("--format=", 1)[1]
        assignments = "\n".join(slurm_replacement.splitlines()[:2])
        result = subprocess.run(
            ["bash", "-c", assignments + '; printf %s "$SACCT_FIELDS"'],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout, expected_fields)

        pip_original, pip_replacement = self.transform("docs/05-python-envs.md")[1]
        self.assertEqual(
            shlex.split(pip_replacement.replace("\\\n", "")),
            shlex.split(pip_original),
        )

    def test_proof_font_definition_denies_every_ligature_feature(self) -> None:
        definition = proof_font_definition(ROOT, self.context)
        self.assertIn("CascadiaMono-", definition)
        self.assertIn(
            "Path="
            + (ROOT / "pdf/fonts/cascadia-mono-2407.24").as_posix()
            + "/",
            definition,
        )
        for setting in self.context.fontspec_ligatures:
            self.assertEqual(definition.count(f"Ligatures={setting}"), 1)
        for feature in self.context.raw_features:
            self.assertEqual(definition.count(f"RawFeature={feature}"), 1)


if __name__ == "__main__":
    unittest.main()
