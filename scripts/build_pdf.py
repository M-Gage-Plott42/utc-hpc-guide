#!/usr/bin/env python3
"""Build the printable guide from its tracked source manifest."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from .pdf_manifest import load_manifest, output_path, workflow_metadata
except ImportError:
    from pdf_manifest import load_manifest, output_path, workflow_metadata


TOP_HEADING = re.compile(r"^# (?:[0-9]{2} )?(.+)$", re.MULTILINE)
SECOND_LEVEL_HEADING = re.compile(
    r"^## (?:[0-9]+(?:\.[0-9]+)?[.)]? )?(.+)$",
    re.MULTILINE,
)
LOCK_STAMP_NAME = "lock-attestation.txt"


def normalize_chapter(
    text: str,
    title: str | None = None,
    chapter_label: str | None = None,
) -> str:
    match = TOP_HEADING.search(text)
    if not match:
        raise ValueError("PDF Markdown source is missing a level-one heading")
    normalized_title = title or match.group(1)
    if chapter_label and not normalized_title.startswith("Appendix "):
        normalized_title = f"{chapter_label}. {normalized_title}"
    normalized = text[:match.start()] + f"# {normalized_title}" + text[match.end():]
    if not chapter_label:
        return normalized

    subsection_number = 0

    def replace_subheading(subheading: re.Match[str]) -> str:
        nonlocal subsection_number
        subsection_number += 1
        return f"## {chapter_label}.{subsection_number} {subheading.group(1)}"

    return SECOND_LEVEL_HEADING.sub(replace_subheading, normalized)


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
    core_sections: list[str] = []
    for chapter_number, path in enumerate(manifest["core_sources"], start=1):
        text = (root / path).read_text(encoding="utf-8")
        core_sections.append(
            normalize_chapter(
                rewrite_example_links(text, examples),
                chapter_label=str(chapter_number),
            )
        )

    appendix_sections: list[str] = []
    for appendix in manifest["site_appendices"]:
        text = (root / appendix["path"]).read_text(encoding="utf-8")
        appendix_sections.append(
            normalize_chapter(
                rewrite_example_links(text, examples),
                appendix["title"],
                "A",
            )
        )

    example_sections = ["# Appendix B: Runnable Slurm Templates"]
    example_sections.append(
        "These tracked templates intentionally use `REPLACE_WITH_*` markers. "
        "Replace every marker with site-approved values before submission."
    )
    for index, path in enumerate(examples):
        source = (root / path).read_text(encoding="utf-8").rstrip()
        anchor = example_anchor(path)
        example_sections.extend(
            (
                f"## B.{index + 1} `{Path(path).name}` {{#{anchor}}}",
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


def cover_variables(manifest: dict[str, Any]) -> dict[str, str]:
    if manifest["release_status"] == "candidate":
        release_label = f"Release candidate for v{manifest['release_target']}"
        identifier_label = "Candidate identifier"
    else:
        release_label = f"Version {manifest['document_version']}"
        identifier_label = "Document identifier"
    return {
        "cover-release-label": release_label,
        "cover-identifier-label": identifier_label,
        "document-version": manifest["document_version"],
    }


def command_path(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise RuntimeError(f"required PDF tool is not available: {name}")
    return resolved


def attested_texmf_dist(root: Path, kpsewhich: str) -> Path:
    result = subprocess.run(
        [kpsewhich, "--var-value=TEXMFDIST"],
        check=True,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if not value or "\n" in value:
        raise RuntimeError("kpsewhich returned an invalid TEXMFDIST path")
    texmf_dist = Path(value).resolve()
    if not texmf_dist.is_dir():
        raise RuntimeError(f"locked TEXMFDIST is unavailable: {texmf_dist}")

    texlive_root = texmf_dist.parent
    executable = Path(kpsewhich).resolve()
    if not executable.is_relative_to(texlive_root / "bin"):
        raise RuntimeError(
            "kpsewhich is not contained in the locked TeX Live tree: "
            f"{executable}"
        )

    lock_path = root / "pdf/toolchain.lock.json"
    stamp = texlive_root.parent / LOCK_STAMP_NAME
    if (
        not lock_path.is_file()
        or lock_path.is_symlink()
        or not stamp.is_file()
        or stamp.is_symlink()
        or stamp.read_text(encoding="utf-8")
        != f"lock_sha256={sha256(lock_path)}\n"
    ):
        raise RuntimeError(
            "font-resolving TeX Live tree is not attested to the current lock"
        )
    return texmf_dist


def locked_font_variables(root: Path) -> list[str]:
    kpsewhich = command_path("kpsewhich")
    texmf_dist = attested_texmf_dist(root, kpsewhich)
    variables: list[str] = []

    def add_family(
        variable: str,
        family: str,
        upright_suffix: str | None,
        italic_suffix: str,
        bold_italic_suffix: str,
        scale: str,
    ) -> None:
        upright_filename = (
            f"{family}-{upright_suffix}.ttf"
            if upright_suffix
            else f"{family}.ttf"
        )
        required_files = (
            upright_filename,
            f"{family}-Bold.ttf",
            f"{family}-{italic_suffix}.ttf",
            f"{family}-{bold_italic_suffix}.ttf",
        )
        resolved: list[Path] = []
        for filename in required_files:
            result = subprocess.run(
                [kpsewhich, filename],
                check=True,
                capture_output=True,
                text=True,
            )
            value = result.stdout.strip()
            if not value or "\n" in value:
                raise RuntimeError(
                    f"kpsewhich returned an invalid path for locked font: {filename}"
                )
            path = Path(value)
            if not path.is_file() or path.is_symlink():
                raise RuntimeError(f"locked PDF font is unavailable: {filename}")
            resolved_path = path.resolve()
            if not resolved_path.is_relative_to(texmf_dist):
                raise RuntimeError(
                    "locked PDF font resolved outside the attested TEXMFDIST: "
                    f"{filename} -> {resolved_path}"
                )
            resolved.append(resolved_path)
        font_directories = {path.parent.resolve() for path in resolved}
        if len(font_directories) != 1:
            raise RuntimeError(
                f"locked PDF font family resolved from multiple directories: {family}"
            )
        font_directory = font_directories.pop().as_posix() + "/"
        upright_option = f"*-{upright_suffix}" if upright_suffix else "*"
        for value in (
            f"{variable}={family}",
            f"{variable}options=Path={font_directory}",
            f"{variable}options=Extension=.ttf",
            f"{variable}options=Scale={scale}",
            f"{variable}options=UprightFont={upright_option}",
            f"{variable}options=BoldFont=*-Bold",
            f"{variable}options=ItalicFont=*-{italic_suffix}",
            f"{variable}options=BoldItalicFont=*-{bold_italic_suffix}",
        ):
            variables.extend(("--variable", value))

    add_family(
        "mainfont",
        "NotoSans",
        "Regular",
        "Italic",
        "BoldItalic",
        "MatchLowercase",
    )
    add_family(
        "sansfont",
        "NotoSans",
        "Regular",
        "Italic",
        "BoldItalic",
        "MatchLowercase",
    )
    add_family(
        "monofont",
        "DejaVuSansMono",
        None,
        "Oblique",
        "BoldOblique",
        "0.88",
    )
    return variables


def build_once(
    root: Path,
    manifest: dict[str, Any],
    output: Path,
    work_dir: Path,
) -> None:
    pandoc = command_path("pandoc")
    lualatex = command_path("lualatex")
    assembled = work_dir / "UTC_HPC_Guide_assembled.md"
    assembled.write_text(assemble_markdown(root, manifest), encoding="utf-8")
    header = work_dir / "header.tex"
    header_text = (root / manifest["header_source"]).read_text(encoding="utf-8")
    header_text = header_text.replace(
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
    cover = cover_variables(manifest)
    command = [
        pandoc,
        str(assembled),
        "--from=markdown-implicit_figures+smart",
        "--standalone",
        "--toc",
        "--toc-depth=2",
        "--syntax-highlighting=none",
        f"--pdf-engine={lualatex}",
        f"--template={root / manifest['template_source']}",
        f"--lua-filter={root / manifest['code_filter_source']}",
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
        f"lang={manifest['language']}",
        "--metadata",
        "subject=Practical SLURM, Open OnDemand, SSH, Python, and GPU onboarding",
        "--variable",
        "papersize=letter",
        "--variable",
        "classoption=titlepage",
        "--variable",
        f"pdfstandard={manifest['pdf_standard']}",
        "--variable",
        (
            "pdf-trailer-id="
            f"<{manifest['pdf_trailer_id']}> <{manifest['pdf_trailer_id']}>"
        ),
        "--variable",
        f"pdf-random-seed={manifest['source_date_epoch']}",
        "--variable",
        "geometry:margin=0.72in",
        "--variable",
        "geometry:headheight=20pt",
        "--variable",
        "geometry:headsep=14pt",
        "--variable",
        "geometry:footskip=28pt",
        "--variable",
        "fontsize=10pt",
        *(
            item
            for key, value in cover.items()
            for item in ("--variable", f"{key}={value}")
        ),
        *locked_font_variables(root),
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
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-reproducible", action="store_true")
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument("--print-output-path", action="store_true")
    output_mode.add_argument("--print-workflow-metadata", action="store_true")
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
    try:
        manifest = load_manifest(
            manifest_path,
            root=root,
            validate_sources=True,
        )
        expected_output = output_path(root, manifest)
        if args.print_output_path:
            print(expected_output.relative_to(root).as_posix())
            return 0
        if args.print_workflow_metadata:
            for key, value in workflow_metadata(root, manifest).items():
                print(f"{key}={value}")
            return 0
        output = args.output or expected_output
        if not output.is_absolute():
            output = root / output
        if output.resolve() != expected_output.resolve():
            raise ValueError(
                "output path must match manifest-derived output path: "
                f"{expected_output.relative_to(root)}"
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
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ERROR: PDF build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
