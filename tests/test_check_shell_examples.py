from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"syntax": "check-shell-syntax", "lint": "check-shell-lint"}


class ShellTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "checker.jsonl"
        self.make = shutil.which("make")
        self.git = shutil.which("git")
        self.assertIsNotNone(self.make)
        self.assertIsNotNone(self.git)
        (self.root / "scripts").mkdir()
        shutil.copyfile(ROOT / "Makefile", self.root / "Makefile")
        shutil.copyfile(
            ROOT / "scripts/check_shell_examples.py",
            self.root / "scripts/check_shell_examples.py",
        )
        (self.bin / "python3").symlink_to(sys.executable)
        (self.bin / "git").symlink_to(self.git)
        for checker in ("bash", "shellcheck"):
            self.executable(checker, '''import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ["CHECKER_LOG"]).open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(args) + "\\n")
if args[-1] in json.loads(os.environ.get("FAIL_FILES", "[]")):
    print("injected checker failure", file=sys.stderr)
    sys.exit(7)
''')
        self.env = {**os.environ, "PATH": str(self.bin), "CHECKER_LOG": str(self.log)}
        # Real git creates the index; only the command under test uses stubs.
        subprocess.run([self.git, "init", "-q", str(self.root)], check=True)

    def executable(self, name: str, body: str) -> None:
        path = self.bin / name
        path.unlink(missing_ok=True)
        path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        path.chmod(0o755)

    def track(self, names: list[str]) -> None:
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
        subprocess.run([self.git, "add", "--", *names], cwd=self.root, check=True)

    def run_target(self, mode: str, failures: list[str] | None = None):
        self.log.unlink(missing_ok=True)
        return subprocess.run(
            [self.make, "--no-print-directory", TARGETS[mode]],
            cwd=self.root,
            env={**self.env, "FAIL_FILES": json.dumps(failures or [])},
            capture_output=True,
            text=True,
            check=False,
        )

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def assert_failed(self, result) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("_clean", result.stdout)
        self.assertNotIn("No tracked", result.stdout)

    def test_healthy_and_unusual_filenames_remain_separate_arguments(self) -> None:
        names = [
            "examples/a space.sbatch",
            "examples/b'quote.sbatch",
            "examples/c\nnewline.sbatch",
            "examples/d;literal.sbatch",
            "examples/é.sbatch",
        ]
        self.track(names)
        (self.root / "examples/untracked.sbatch").write_text("not included")
        for mode in TARGETS:
            with self.subTest(mode=mode):
                result = self.run_target(mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"shell_{mode}_clean files=5", result.stdout)
                options = ["-n", "--"] if mode == "syntax" else ["-s", "bash", "--"]
                self.assertEqual(self.calls(), [[*options, name] for name in names])

    def test_first_last_and_all_checker_failures_fail_make(self) -> None:
        names = ["examples/first.sbatch", "examples/last.sbatch"]
        self.track(names)
        for mode in TARGETS:
            for failures in ([names[0]], [names[-1]], names):
                with self.subTest(mode=mode, failures=failures):
                    result = self.run_target(mode, failures)
                    self.assert_failed(result)
                    self.assertIn("injected checker failure", result.stderr)
                    expected = names[: names.index(failures[0]) + 1]
                    self.assertEqual([call[-1] for call in self.calls()], expected)

    def test_failed_enumeration_rejects_even_partial_output(self) -> None:
        self.track(["examples/first.sbatch"])
        for partial in (b"", b"examples/first.sbatch\0"):
            self.executable("git", f'''import sys
sys.stdout.buffer.write({partial!r})
print("injected enumeration failure", file=sys.stderr)
sys.exit(9)
''')
            for mode in TARGETS:
                with self.subTest(mode=mode, partial=partial):
                    result = self.run_target(mode)
                    self.assert_failed(result)
                    self.assertIn("injected enumeration failure", result.stderr)
                    self.assertEqual(self.calls(), [])

    def test_empty_index_is_an_explicit_success(self) -> None:
        for mode in TARGETS:
            with self.subTest(mode=mode):
                result = self.run_target(mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("No tracked sbatch examples found.", result.stdout)
                self.assertNotIn("_clean", result.stdout)
                self.assertEqual(self.calls(), [])

    def test_missing_shellcheck_fails_even_with_no_examples(self) -> None:
        (self.bin / "shellcheck").unlink()
        result = self.run_target("lint")
        self.assert_failed(result)
        self.assertIn("shellcheck' not found", result.stderr)

    def test_real_bash_rejects_invalid_syntax(self) -> None:
        self.track(["examples/broken.sbatch"])
        (self.root / "examples/broken.sbatch").write_text("if true; then\n")
        (self.bin / "bash").unlink()
        (self.bin / "bash").symlink_to("/bin/bash")
        self.assert_failed(self.run_target("syntax"))


if __name__ == "__main__":
    unittest.main()
