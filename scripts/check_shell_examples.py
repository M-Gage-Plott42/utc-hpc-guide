#!/usr/bin/env python3
"""Check every tracked sbatch example, failing on enumeration or checker errors."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("syntax", "lint"))
    args = parser.parse_args()
    checker = "bash" if args.mode == "syntax" else "shellcheck"
    if shutil.which(checker) is None:
        print(f"Required checker {checker!r} not found; install it and retry.", file=sys.stderr)
        return 1
    try:
        # Collect output only after git succeeds; partial output is not a file list.
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "examples/*.sbatch"],
            stdout=subprocess.PIPE,
            check=True,
        )
        shell_files = [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]
        if not shell_files:
            print("No tracked sbatch examples found.")
            return 0
        options = ["-n"] if args.mode == "syntax" else ["-s", "bash"]
        for shell_file in shell_files:
            subprocess.run([checker, *options, "--", shell_file], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Shell {args.mode} check failed: {exc}", file=sys.stderr)
        return 1
    print(f"shell_{args.mode}_clean files={len(shell_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
