#!/usr/bin/env python3
"""Build the printable guide from its tracked source manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


TOP_HEADING = re.compile(r"^# (?:[0-9]{2} )?(.+)$", re.MULTILINE)


def load_manifest(root: Path, path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("PDF manifest schema_version must be 1")
    for key in (
        "title",
        "subtitle",
        "author",
        "date",
        "release_target",
        "document_version",
        "source_date_epoch",
        "pdf_trailer_id",
        "output_filename",
        "header_source",
        "core_sources",
        "site_appendices",
        "examples",
        "required_pdf_text",
    ):
        if key not in manifest:
            raise ValueError(f"PDF manifest is missing {key}")

    if not re.fullmatch(r"[0-9a-f]{32}", manifest["pdf_trailer_id"]):
        raise ValueError("pdf_trailer_id must be exactly 32 lowercase hex characters")

    source_paths = [manifest["header_source"], *manifest["core_sources"]]
    source_paths.extend(item["path"] for item in manifest["site_appendices"])
    source_paths.extend(manifest["examples"])
    for raw_path in source_paths:
        normalized = PurePosixPath(raw_path)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError(f"PDF source must stay inside the repository: {raw_path}")
        if not (root / normalized).is_file():
            raise ValueError(f"PDF source does not exist: {raw_path}")
    return manifest


def normalize_chapter(text: str, title: str | None = None) -> str:
    match = TOP_HEADING.search(text)
    if not match:
        raise ValueError("PDF Markdown source is missing a level-one heading")
    replacement = f"# {title or match.group(1)}"
    return text[:match.start()] + replacement + text[match.end():]


def example_anchor(path: str) -> str:
    return "example-" + re.sub(r"[^a-z0-9]+", "-", Path(path).stem.casefold()).strip("-")


def rewrite_example_links(text: str, examples: list[str]) -> str:
    for path in examples:
        filename = Path(path).name
        anchor = example_anchor(path)
        text = text.replace(f"(examples/{filename})", f"(#{anchor})")
        text = text.replace(f"(../../examples/{filename})", f"(#{anchor})")
    return text


def assemble_markdown(root: Path, manifest: dict[str, Any]) -> str:
    examples = list(manifest["examples"])
    core_sections = [
        (
            f"**Version {manifest['document_version']}**  \n"
            f"Document identifier: `v{manifest['document_version']}`  \n"
            "Canonical source: tracked repository chapters, site appendix, "
            "examples, and `pdf/guide_manifest.json`  \n"
            "Repository: <https://github.com/M-Gage-Plott42/utc-hpc-guide>\n\n"
            "This guide is a practical baseline, not official cluster policy. "
            "Verify site-specific limits, software, storage, and access rules "
            "against current institutional documentation and live scheduler commands."
        )
    ]
    for path in manifest["core_sources"]:
        text = (root / path).read_text(encoding="utf-8")
        core_sections.append(normalize_chapter(rewrite_example_links(text, examples)))

    appendix_sections: list[str] = []
    for appendix in manifest["site_appendices"]:
        text = (root / appendix["path"]).read_text(encoding="utf-8")
        appendix_sections.append(
            normalize_chapter(
                rewrite_example_links(text, examples),
                appendix["title"],
            )
        )

    example_sections = ["# Appendix B: Runnable Slurm Templates"]
    example_sections.append(
        "These tracked templates intentionally use `REPLACE_WITH_*` markers. "
        "Replace every marker with site-approved values before submission."
    )
    example_sections.append("\\lstset{basicstyle=\\ttfamily\\scriptsize}")
    for index, path in enumerate(examples):
        if index:
            example_sections.append("\\newpage")
        source = (root / path).read_text(encoding="utf-8").rstrip()
        anchor = example_anchor(path)
        example_sections.extend(
            (
                f"## `{Path(path).name}` {{#{anchor}}}",
                "```bash",
                source,
                "```",
            )
        )
    document = "\n\n".join(section.strip() for section in core_sections)
    for appendix in appendix_sections:
        document += "\n\n\\newpage\n\n" + appendix.strip()
    document += "\n\n\\newpage\n\n" + "\n\n".join(example_sections)
    return document + "\n"


def command_path(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise RuntimeError(f"required PDF tool is not available: {name}")
    return resolved


def build_once(
    root: Path,
    manifest: dict[str, Any],
    output: Path,
    work_dir: Path,
) -> None:
    pandoc = command_path("pandoc")
    xelatex = command_path("xelatex")
    assembled = work_dir / "UTC_HPC_Guide_assembled.md"
    assembled.write_text(assemble_markdown(root, manifest), encoding="utf-8")
    header = work_dir / "header.tex"
    header_text = (root / manifest["header_source"]).read_text(encoding="utf-8")
    header_text = header_text.replace(
        "@PDF_TRAILER_ID@",
        manifest["pdf_trailer_id"],
    ).replace(
        "@DOCUMENT_VERSION@",
        manifest["document_version"],
    )
    if re.search(r"@[A-Z][A-Z0-9_]+@", header_text):
        raise ValueError("PDF header contains an unresolved manifest token")
    header.write_text(header_text, encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(manifest["source_date_epoch"])
    env["TZ"] = "UTC"
    command = [
        pandoc,
        str(assembled),
        "--from=markdown+smart",
        "--standalone",
        "--toc",
        "--toc-depth=2",
        "--listings",
        f"--pdf-engine={xelatex}",
        f"--resource-path={root}:{root / 'docs'}",
        f"--include-in-header={header}",
        "--metadata",
        f"title={manifest['title']}",
        "--metadata",
        f"subtitle={manifest['subtitle']}",
        "--metadata",
        f"author={manifest['author']}",
        "--metadata",
        f"date={manifest['date']}",
        "--metadata",
        "lang=en-US",
        "--metadata",
        "subject=Practical SLURM, Open OnDemand, SSH, Python, and GPU onboarding",
        "--variable",
        "papersize=letter",
        "--variable",
        "geometry:margin=0.72in",
        "--variable",
        "fontsize=10pt",
        "--variable",
        "mainfont=DejaVu Serif",
        "--variable",
        "sansfont=DejaVu Sans",
        "--variable",
        "monofont=DejaVu Sans Mono",
        "--output",
        str(output),
    ]
    subprocess.run(command, cwd=root, env=env, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("pdf/guide_manifest.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-reproducible", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    output = args.output
    if not output.is_absolute():
        output = root / output

    try:
        manifest = load_manifest(root, manifest_path)
        if output.name != manifest["output_filename"]:
            raise ValueError(
                "output filename must match manifest output_filename: "
                f"{manifest['output_filename']}"
            )
        with tempfile.TemporaryDirectory(prefix="utc-hpc-pdf-") as first_temp:
            first = Path(first_temp) / output.name
            build_once(root, manifest, first, Path(first_temp))
            if args.verify_reproducible:
                with tempfile.TemporaryDirectory(prefix="utc-hpc-pdf-") as second_temp:
                    second = Path(second_temp) / output.name
                    build_once(root, manifest, second, Path(second_temp))
                    first_hash = sha256(first)
                    second_hash = sha256(second)
                    if first_hash != second_hash:
                        raise RuntimeError(
                            "PDF build is not reproducible: "
                            f"{first_hash} != {second_hash}"
                        )
                    print(f"pdf_reproducible sha256={first_hash}")
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(first, output)
        print(f"pdf_built path={output} sha256={sha256(output)}")
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ERROR: PDF build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
