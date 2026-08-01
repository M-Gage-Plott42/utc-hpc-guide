from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_font_proofs import (
    proof_profile_ids,
    run_logged,
    sha256,
    verify_qa_packages,
    write_bundle_sums,
)


class FontProofOrchestratorTests(unittest.TestCase):
    def test_bundle_sums_use_downloaded_artifact_root_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "dist/proof.pdf"
            record = root / "dist/font-proofs/profile/record.txt"
            pdf.parent.mkdir()
            record.parent.mkdir(parents=True)
            pdf.write_bytes(b"pdf")
            record.write_bytes(b"record")

            sums = write_bundle_sums(root, [record, pdf])

            self.assertEqual(
                sums.read_text(encoding="utf-8"),
                "".join(
                    (
                        f"{sha256(record)}  font-proofs/profile/record.txt\n",
                        f"{sha256(pdf)}  proof.pdf\n",
                    )
                ),
            )

    def test_bundle_sums_reject_artifact_outside_dist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "dist").mkdir()
            outside = root / "outside.pdf"
            outside.write_bytes(b"pdf")
            with self.assertRaisesRegex(RuntimeError, "escaped"):
                write_bundle_sums(root, [outside])

    def test_profile_ids_preserve_review_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "proofs.json"
            config.write_text(
                json.dumps(
                    {
                        "profiles": {
                            "dejavu-large": {},
                            "cascadia-mono": {},
                            "fira-code": {},
                        }
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                proof_profile_ids(config),
                ("dejavu-large", "cascadia-mono", "fira-code"),
            )

    def test_rejects_empty_profile_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "proofs.json"
            config.write_text('{"profiles": {}}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nonempty"):
                proof_profile_ids(config)

    @patch("scripts.check_font_proofs.command_output")
    def test_verifies_exact_qa_package_pins(self, command_output_mock) -> None:
        versions = {
            "mupdf-tools": "1.23.10+ds1-1build3",
            "python3-fonttools": "4.46.0-1build2",
        }
        command_output_mock.side_effect = (
            lambda command, **_kwargs: versions[command[-1]]
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pdf").mkdir()
            lock = root / "pdf/font_proofs.lock.json"
            lock.write_text(
                json.dumps(
                    {
                        "ubuntu_24_04_qa_packages": {
                            "mupdf-tools": "1.23.10+ds1-1build3",
                            "python3-fonttools": "4.46.0-1build2",
                        }
                    }
                ),
                encoding="utf-8",
            )
            config = root / "pdf/font_proofs.json"
            config.write_text(
                '{"font_lock": "pdf/font_proofs.lock.json"}\n',
                encoding="utf-8",
            )
            path, digest = verify_qa_packages(root, config)
            self.assertEqual(path, "pdf/font_proofs.lock.json")
            self.assertEqual(digest, sha256(lock))

    @patch("scripts.check_font_proofs.command_output")
    def test_rejects_qa_package_drift(self, command_output_mock) -> None:
        command_output_mock.side_effect = (
            lambda command, **_kwargs: (
                "different"
                if command[-1] == "mupdf-tools"
                else "4.46.0-1build2"
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pdf").mkdir()
            (root / "pdf/font_proofs.lock.json").write_text(
                json.dumps(
                    {
                        "ubuntu_24_04_qa_packages": {
                            "mupdf-tools": "1.23.10+ds1-1build3",
                            "python3-fonttools": "4.46.0-1build2",
                        }
                    }
                ),
                encoding="utf-8",
            )
            config = root / "pdf/font_proofs.json"
            config.write_text(
                '{"font_lock": "pdf/font_proofs.lock.json"}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "package mismatch"):
                verify_qa_packages(root, config)

    @patch("scripts.check_font_proofs.subprocess.Popen")
    @patch("scripts.check_font_proofs.sys.stdout")
    def test_logged_command_failure_is_not_allowlisted(
        self,
        _stdout_mock,
        popen_mock,
    ) -> None:
        process = popen_mock.return_value
        process.communicate.return_value = ("partial output\n", "failure\n")
        process.returncode = 2
        log: list[str] = []
        with self.assertRaisesRegex(RuntimeError, "status 2"):
            run_logged(["false"], root=Path.cwd(), log=log)
        self.assertEqual(log, ["partial output\nfailure\n"])

    @patch("scripts.check_font_proofs.time.monotonic", side_effect=(10.0, 31.0))
    @patch("scripts.check_font_proofs.subprocess.Popen")
    @patch("scripts.check_font_proofs.sys.stdout")
    def test_logged_command_emits_heartbeat_without_losing_output(
        self,
        _stdout_mock,
        popen_mock,
        _monotonic_mock,
    ) -> None:
        process = popen_mock.return_value
        process.communicate.side_effect = (
            subprocess.TimeoutExpired(["python", "slow.py"], 20),
            ("complete output\n", ""),
        )
        process.returncode = 0
        log: list[str] = []
        with patch("builtins.print") as print_mock:
            run_logged(["python", "slow.py"], root=Path.cwd(), log=log)
        self.assertEqual(log, ["complete output\n"])
        self.assertIn("elapsed_seconds=21", print_mock.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
