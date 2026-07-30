from __future__ import annotations

import unittest

from scripts.check_shell_placeholders import scan_markdown, scan_sbatch


class ShellPlaceholderTests(unittest.TestCase):
    def test_rejects_angle_placeholder_in_bash_fence(self) -> None:
        findings = scan_markdown(
            "```bash\n"
            "JOB_ID=<jobid>\n"
            "sacct -j <jobid>\n"
            "```\n"
        )
        self.assertEqual([item.line for item in findings], [2, 3])

    def test_allows_narrative_and_quoted_replacement_marker(self) -> None:
        findings = scan_markdown(
            "Replace `<jobid>` before use.\n\n"
            "```bash\n"
            'JOB_ID="REPLACE_WITH_JOB_ID"\n'
            'sacct -j "$JOB_ID"\n'
            "```\n"
        )
        self.assertEqual(findings, [])

    def test_ignores_non_shell_fence(self) -> None:
        findings = scan_markdown("```text\n<username>@<host>\n```\n")
        self.assertEqual(findings, [])

    def test_rejects_shell_session_fence(self) -> None:
        findings = scan_markdown(
            "```shell-session\n"
            "$ ssh <username>@<login-host>\n"
            "```\n"
        )
        self.assertEqual([item.value for item in findings], ["<username>", "<login-host>"])

    def test_rejects_pandoc_attribute_shell_fences(self) -> None:
        findings = scan_markdown(
            "```{.bash .numberLines}\n"
            "squeue -u <username>\n"
            "```\n\n"
            "~~~{.shell}\n"
            "cd <project-path>\n"
            "~~~\n"
        )
        self.assertEqual(
            [item.value for item in findings],
            ["<username>", "<project-path>"],
        )

    def test_conservatively_ignores_indented_code_blocks(self) -> None:
        findings = scan_markdown(
            "Indented examples remain manual-review scope:\n\n"
            "    ssh <username>@<login-host>\n"
        )
        self.assertEqual(findings, [])

    def test_rejects_sbatch_directive_placeholder(self) -> None:
        findings = scan_sbatch("#SBATCH --partition=<gpu-partition>\n")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].value, "<gpu-partition>")


if __name__ == "__main__":
    unittest.main()
