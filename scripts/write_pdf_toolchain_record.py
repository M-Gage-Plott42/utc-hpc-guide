#!/usr/bin/env python3
"""Write a fail-closed PDF build and validation traceability record."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from .check_pdf_accessibility import (
        extract_metadata_stream,
        find_catalog,
        load_qpdf_document,
        metadata_reference,
        parse_info,
        parse_verapdf_report,
        qpdf_objects,
        qpdf_text,
        resolve_reference,
        validate_pdfinfo,
        validate_qpdf_document,
    )
    from .pdf_manifest import load_manifest, output_path
except ImportError:
    from check_pdf_accessibility import (
        extract_metadata_stream,
        find_catalog,
        load_qpdf_document,
        metadata_reference,
        parse_info,
        parse_verapdf_report,
        qpdf_objects,
        qpdf_text,
        resolve_reference,
        validate_pdfinfo,
        validate_qpdf_document,
    )
    from pdf_manifest import load_manifest, output_path


HEX_SHA256 = r"[0-9a-f]{64}"
LOCK_STAMP_NAME = "lock-attestation.txt"
FONT_FILES = (
    "DejaVuSerif.ttf",
    "DejaVuSerif-Bold.ttf",
    "DejaVuSerif-Italic.ttf",
    "DejaVuSerif-BoldItalic.ttf",
    "DejaVuSans.ttf",
    "DejaVuSans-Bold.ttf",
    "DejaVuSans-Oblique.ttf",
    "DejaVuSans-BoldOblique.ttf",
    "DejaVuSansMono.ttf",
    "DejaVuSansMono-Bold.ttf",
    "DejaVuSansMono-Oblique.ttf",
    "DejaVuSansMono-BoldOblique.ttf",
)
CI_ENVIRONMENT = (
    "GITHUB_SHA",
    "GITHUB_REPOSITORY",
    "GITHUB_WORKFLOW",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_RUN_ID",
    "GITHUB_RUN_NUMBER",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_SERVER_URL",
    "RUNNER_OS",
    "RUNNER_ARCH",
    "ImageOS",
    "ImageVersion",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_regular_file(path: Path, label: str) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as exc:
        raise RuntimeError(f"{label} is missing: {path}") from exc
    if not stat.S_ISREG(mode):
        raise RuntimeError(f"{label} must be a regular file: {path}")


def run(
    command: list[str | Path],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(
        [str(item) for item in command],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return (result.stdout + result.stderr).strip()


def first_line(output: str, label: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"{label} returned no version output")
    return lines[0]


def require_exact_line(output: str, expected_line: str, label: str) -> None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if expected_line not in lines:
        observed = lines[0] if lines else "no output"
        raise RuntimeError(
            f"{label} version mismatch; expected exact line "
            f"{expected_line!r}, observed {observed!r}"
        )


def matching_line(output: str, expected_line: str, label: str) -> str:
    require_exact_line(output, expected_line, label)
    return expected_line


def one_marker(
    lines: list[str],
    prefix: str,
    pattern: re.Pattern[str],
) -> re.Match[str]:
    matches = [line for line in lines if line.startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(
            f"PDF check log must contain exactly one {prefix.strip()} marker; "
            f"found {len(matches)}"
        )
    parsed = pattern.fullmatch(matches[0])
    if parsed is None:
        raise RuntimeError(f"malformed PDF check marker: {matches[0]}")
    return parsed


def parse_check_log(
    text: str,
    *,
    pdf: Path,
    pdf_sha256: str,
) -> dict[str, str]:
    """Require every successful check marker and bind it to the final PDF."""
    lines = [line.strip() for line in text.splitlines()]
    reproducible = one_marker(
        lines,
        "pdf_reproducible ",
        re.compile(rf"pdf_reproducible sha256=({HEX_SHA256})"),
    )
    built = one_marker(
        lines,
        "pdf_built ",
        re.compile(rf"pdf_built path=(.+) sha256=({HEX_SHA256})"),
    )
    qa = one_marker(
        lines,
        "pdf_qa_passed ",
        re.compile(
            rf"pdf_qa_passed pages=([1-9][0-9]*) "
            rf"fonts=([1-9][0-9]*) sha256=({HEX_SHA256})"
        ),
    )
    ocr = one_marker(
        lines,
        "pdf_ocr_passed ",
        re.compile(
            r"pdf_ocr_passed pages=([1-9][0-9]*) "
            r"dpi=([1-9][0-9]*) min_page_alnum=([1-9][0-9]*)"
        ),
    )
    accessibility = one_marker(
        lines,
        "pdf_accessibility_qa_passed ",
        re.compile(
            r"pdf_accessibility_qa_passed "
            r"structure_roles=([1-9][0-9]*) figures=3 "
            r"verapdf_profile=ua2 verapdf_jobs=1"
        ),
    )

    hashes = (reproducible.group(1), built.group(2), qa.group(3))
    if any(value != pdf_sha256 for value in hashes):
        raise RuntimeError(
            "PDF check markers do not match the final PDF SHA-256"
        )
    if Path(built.group(1)).resolve() != pdf.resolve():
        raise RuntimeError(
            "PDF build marker path does not match the manifest-derived output"
        )
    if qa.group(1) != ocr.group(1):
        raise RuntimeError("structural/render and OCR checks disagree on page count")

    return {
        "reproducibility": "passed",
        "structural": "passed",
        "render": "passed",
        "ocr": "passed",
        "accessibility": "passed",
        "verapdf": "passed",
        "pages": qa.group(1),
        "fonts": qa.group(2),
        "ocr_dpi": ocr.group(2),
        "structure_roles": accessibility.group(1),
    }


def parse_tlmgr_details(output: str) -> dict[str, str]:
    details: dict[str, str] = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            details[key.strip()] = value.strip()
    return details


def package_version(name: str) -> str:
    return run(["dpkg-query", "-W", "-f=${Version}", name])


def ci_context(
    commit: str,
    *,
    require_github_context: bool,
) -> dict[str, str]:
    missing = [name for name in CI_ENVIRONMENT if not os.environ.get(name)]
    if require_github_context and missing:
        raise RuntimeError(
            "required GitHub Actions context is missing: " + ", ".join(missing)
        )
    if os.environ.get("GITHUB_SHA") and os.environ["GITHUB_SHA"] != commit:
        raise RuntimeError("GITHUB_SHA does not match the checked-out commit")

    values = {name: os.environ.get(name, "unavailable") for name in CI_ENVIRONMENT}
    if not require_github_context:
        values["GITHUB_SHA"] = values["GITHUB_SHA"].replace("unavailable", commit)
        values["GITHUB_REF"] = values["GITHUB_REF"].replace(
            "unavailable", "local-worktree"
        )
        values["RUNNER_OS"] = values["RUNNER_OS"].replace(
            "unavailable", platform.system()
        )
        values["RUNNER_ARCH"] = values["RUNNER_ARCH"].replace(
            "unavailable", platform.machine()
        )
    return values


def record_value(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())


def write_record(
    *,
    root: Path,
    manifest_path: Path,
    lock_path: Path,
    toolchain_root: Path,
    report_path: Path,
    check_log_path: Path,
    destination: Path,
    require_github_context: bool,
) -> None:
    for path, label in (
        (manifest_path, "PDF manifest"),
        (lock_path, "PDF toolchain lock"),
        (report_path, "veraPDF report"),
        (check_log_path, "PDF check log"),
    ):
        require_regular_file(path, label)

    manifest = load_manifest(
        manifest_path,
        root=root,
        validate_sources=True,
    )
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("schema_version") != 1:
        raise ValueError("PDF toolchain lock schema_version must be 1")
    if lock.get("platform") != "linux-x86_64":
        raise ValueError("PDF toolchain lock platform must be linux-x86_64")
    host_lock = lock.get("host")
    if (
        not isinstance(host_lock, dict)
        or host_lock.get("os_id") != "ubuntu"
        or host_lock.get("version_id") != "24.04"
    ):
        raise ValueError("PDF toolchain lock host must be Ubuntu 24.04")
    lock_digest = sha256(lock_path)
    stamp = toolchain_root / LOCK_STAMP_NAME
    require_regular_file(stamp, "PDF toolchain lock attestation")
    if stamp.read_text(encoding="utf-8") != (
        f"lock_sha256={lock_digest}\n"
    ):
        raise RuntimeError(
            "PDF toolchain lock attestation does not match the current lock"
        )

    pdf = output_path(root, manifest)
    require_regular_file(pdf, "manifest-derived PDF")
    pdf_digest = sha256(pdf)
    checks = parse_check_log(
        check_log_path.read_text(encoding="utf-8"),
        pdf=pdf,
        pdf_sha256=pdf_digest,
    )
    vera = parse_verapdf_report(report_path.read_bytes())
    if (
        vera.total_jobs != 1
        or vera.compliant_jobs != 1
        or "PDF/UA-2" not in vera.profile
        or lock["verapdf"].get("profile") != "ua2"
    ):
        raise RuntimeError("veraPDF report or locked profile is not PDF/UA-2")

    binary_dir = toolchain_root / "bin"
    required_commands = (
        "pandoc",
        "lualatex",
        "tlmgr",
        "kpsewhich",
        "java",
        "verapdf",
        *lock["qa_tools"],
    )
    for name in required_commands:
        if not (binary_dir / name).is_file():
            raise RuntimeError(f"locked PDF tool is missing: {binary_dir / name}")
    tool_env = os.environ.copy()
    tool_env["PATH"] = (
        f"{binary_dir}{os.pathsep}{tool_env.get('PATH', '')}"
    )

    pandoc_output = run(
        [binary_dir / "pandoc", "--version"],
        env=tool_env,
    )
    require_exact_line(
        pandoc_output,
        lock["pandoc"]["version_line"],
        "Pandoc",
    )
    lualatex_output = run(
        [binary_dir / "lualatex", "--version"],
        env=tool_env,
    )
    require_exact_line(
        lualatex_output,
        lock["texlive"]["lualatex_version_line"],
        "LuaLaTeX",
    )
    tlmgr_output = run(
        [binary_dir / "tlmgr", "--version"],
        env=tool_env,
    )
    require_exact_line(
        tlmgr_output,
        f"TeX Live (https://tug.org/texlive) version "
        f"{lock['texlive']['release']}",
        "TeX Live",
    )
    java_output = run(
        [binary_dir / "java", "-version"],
        env=tool_env,
    )
    require_exact_line(java_output, lock["java"]["version_line"], "Java")
    require_exact_line(
        java_output,
        lock["java"]["runtime_line"],
        "Java runtime",
    )
    verapdf_output = run(
        [binary_dir / "verapdf", "--version"],
        env=tool_env,
    )
    require_exact_line(
        verapdf_output,
        lock["verapdf"]["version_line"],
        "veraPDF",
    )

    with tempfile.TemporaryDirectory(prefix="utc-hpc-record-kernel-") as temporary:
        kernel_output = run(
            [
                binary_dir / "lualatex",
                "--interaction=nonstopmode",
                "--halt-on-error",
                "--jobname=kernel-version",
                (
                    "\\documentclass{article}\\begin{document}\\makeatletter"
                    "\\typeout{RECORD-LATEX-KERNEL=\\fmtversion}"
                    "\\end{document}"
                ),
            ],
            cwd=Path(temporary),
            env=tool_env,
        )
    require_exact_line(
        kernel_output,
        f"RECORD-LATEX-KERNEL={lock['texlive']['latex_kernel']}",
        "LaTeX kernel",
    )

    texlive_packages: dict[str, dict[str, str]] = {}
    for package, expected in lock["texlive"]["packages"].items():
        details = parse_tlmgr_details(
            run(
                [
                    binary_dir / "tlmgr",
                    "info",
                    "--only-installed",
                    package,
                ],
                env=tool_env,
            )
        )
        if (
            details.get("installed") != "Yes"
            or details.get("revision") != expected["revision"]
            or details.get("cat-version") != expected["version"]
        ):
            raise RuntimeError(
                f"installed TeX Live package does not match lock: {package}"
            )
        texlive_packages[package] = details
    font_package = texlive_packages["dejavu"]
    font_hashes: dict[str, str] = {}
    for filename in FONT_FILES:
        resolved = run(
            [binary_dir / "kpsewhich", filename],
            env=tool_env,
        )
        if "\n" in resolved or not resolved:
            raise RuntimeError(f"unexpected font resolution for {filename}")
        path = Path(resolved)
        require_regular_file(path, f"locked font {filename}")
        if path.name != filename:
            raise RuntimeError(f"locked font resolved to an unexpected file: {path}")
        font_hashes[filename] = sha256(path)

    qa_versions: dict[str, str] = {}
    for name, specification in lock["qa_tools"].items():
        output = run(
            [binary_dir / name, *specification["arguments"]],
            env=tool_env,
        )
        require_exact_line(output, specification["version_line"], name)
        qa_versions[name] = matching_line(
            output,
            specification["version_line"],
            name,
        )

    host_packages: dict[str, str] = {}
    for name, expected in lock["ubuntu_24_04_qa_packages"].items():
        observed = package_version(name)
        if observed != expected:
            raise RuntimeError(
                f"host QA package mismatch for {name}: "
                f"{observed!r} != {expected!r}"
            )
        host_packages[name] = observed

    qpdf = str(binary_dir / "qpdf")
    pdfinfo_output = run([binary_dir / "pdfinfo", pdf], env=tool_env)
    info = parse_info(pdfinfo_output)
    validate_pdfinfo(info, manifest)
    document = load_qpdf_document(qpdf, pdf)
    metadata = metadata_reference(document)
    xmp = extract_metadata_stream(qpdf, pdf, metadata)
    structure = validate_qpdf_document(document, manifest, xmp)
    objects = qpdf_objects(document)
    catalog = find_catalog(objects)
    mark_info = resolve_reference(
        catalog.get("/MarkInfo"),
        objects,
        description="catalog MarkInfo",
    )
    structure_root = resolve_reference(
        catalog.get("/StructTreeRoot"),
        objects,
        description="catalog StructTreeRoot",
    )
    language = qpdf_text(
        catalog.get("/Lang"),
        description="catalog Lang",
    )
    if not isinstance(mark_info, dict) or mark_info.get("/Marked") is not True:
        raise RuntimeError("catalog MarkInfo is not marked")
    if (
        not isinstance(structure_root, dict)
        or structure_root.get("/Type") != "/StructTreeRoot"
    ):
        raise RuntimeError("catalog StructTreeRoot is absent")

    commit = run(["git", "rev-parse", "HEAD"], cwd=root)
    context = ci_context(
        commit,
        require_github_context=require_github_context,
    )
    run_url = "unavailable"
    if all(
        context[name] != "unavailable"
        for name in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")
    ):
        run_url = (
            f"{context['GITHUB_SERVER_URL']}/"
            f"{context['GITHUB_REPOSITORY']}/actions/runs/"
            f"{context['GITHUB_RUN_ID']}"
        )

    relative_pdf = pdf.relative_to(root).as_posix()
    relative_report = report_path.relative_to(root).as_posix()
    relative_lock = lock_path.relative_to(root).as_posix()
    lines = [
        "UTC HPC Guide PDF build traceability record",
        "distribution_status=review-only release candidate; not stable",
        "",
        "[run]",
        f"commit={commit}",
        f"repository={context['GITHUB_REPOSITORY']}",
        f"workflow={context['GITHUB_WORKFLOW']}",
        f"event={context['GITHUB_EVENT_NAME']}",
        f"ref={context['GITHUB_REF']}",
        f"run_id={context['GITHUB_RUN_ID']}",
        f"run_number={context['GITHUB_RUN_NUMBER']}",
        f"run_attempt={context['GITHUB_RUN_ATTEMPT']}",
        f"run_url={run_url}",
        f"runner_os={context['RUNNER_OS']}",
        f"runner_arch={context['RUNNER_ARCH']}",
        f"runner_image_os={context['ImageOS']}",
        f"runner_image_version={context['ImageVersion']}",
        "",
        "[lock]",
        f"path={relative_lock}",
        f"sha256={lock_digest}",
        f"schema_version={lock['schema_version']}",
        f"platform={lock['platform']}",
        f"host={host_lock['os_id']} {host_lock['version_id']}",
        "",
        "[toolchain]",
        "pandoc="
        + record_value(
            matching_line(
                pandoc_output,
                lock["pandoc"]["version_line"],
                "Pandoc",
            )
        ),
        "lualatex="
        + record_value(
            matching_line(
                lualatex_output,
                lock["texlive"]["lualatex_version_line"],
                "LuaLaTeX",
            )
        ),
        f"tex_live_release={lock['texlive']['release']}",
        "tex_live_repository_revision="
        f"{lock['texlive']['repository_revision']}",
        f"tlmgr={record_value(first_line(tlmgr_output, 'tlmgr'))}",
        f"latex_kernel={lock['texlive']['latex_kernel']}",
        f"java_distribution={lock['java']['distribution']}",
        "java="
        + record_value(
            matching_line(
                java_output,
                lock["java"]["version_line"],
                "Java",
            )
        ),
        "java_runtime="
        + record_value(
            matching_line(
                java_output,
                lock["java"]["runtime_line"],
                "Java runtime",
            )
        ),
        "verapdf="
        + record_value(
            matching_line(
                verapdf_output,
                lock["verapdf"]["version_line"],
                "veraPDF",
            )
        ),
        f"verapdf_profile={lock['verapdf']['profile']}",
        f"verapdf_report_profile={record_value(vera.profile)}",
        "",
        "[tex-live-packages]",
    ]
    lines.extend(
        (
            f"{package}={details['cat-version']} "
            f"revision={details['revision']}"
        )
        for package, details in sorted(texlive_packages.items())
    )
    lines.extend(
        (
            "",
            "[fonts]",
            f"tex_live_package=dejavu {font_package['cat-version']}",
            f"tex_live_package_revision={font_package['revision']}",
        )
    )
    lines.extend(
        f"{filename}.sha256={font_hashes[filename]}"
        for filename in FONT_FILES
    )
    lines.extend(("", "[host-qa-packages]"))
    lines.extend(
        f"{name}={host_packages[name]}"
        for name in sorted(host_packages)
    )
    lines.extend(("", "[qa-tools]"))
    lines.extend(
        f"{name}={record_value(qa_versions[name])}"
        for name in sorted(qa_versions)
    )
    lines.extend(
        (
            "",
            "[pdf]",
            f"path={relative_pdf}",
            f"sha256={pdf_digest}",
            f"pages={checks['pages']}",
            f"fonts={checks['fonts']}",
            f"pdf_version={info['PDF version']}",
            f"Tagged={info['Tagged']}",
            "StructTreeRoot=present",
            "MarkInfo.Marked=true",
            f"Lang={record_value(language)}",
            "structure_roles="
            + ",".join(
                f"{name}:{count}"
                for name, count in sorted(structure.tags.items())
            ),
            "",
            "[validation]",
            f"reproducibility={checks['reproducibility']}",
            f"structural={checks['structural']}",
            f"render={checks['render']}",
            f"ocr={checks['ocr']}",
            f"ocr_dpi={checks['ocr_dpi']}",
            f"accessibility={checks['accessibility']}",
            f"verapdf={checks['verapdf']}",
            f"verapdf_jobs={vera.total_jobs}",
            f"verapdf_compliant_jobs={vera.compliant_jobs}",
            f"verapdf_report={relative_report}",
            f"verapdf_report_sha256={sha256(report_path)}",
        )
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("pdf/guide_manifest.json"),
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("pdf/toolchain.lock.json"),
    )
    parser.add_argument(
        "--toolchain-root",
        type=Path,
        default=Path(".cache/pdf-toolchain"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("dist/verapdf-report.xml"),
    )
    parser.add_argument(
        "--check-log",
        type=Path,
        default=Path("dist/check-pdf.log"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/build-toolchain.txt"),
    )
    parser.add_argument("--require-github-context", action="store_true")
    return parser.parse_args()


def repository_root() -> Path:
    return Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )


def rooted(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def main() -> int:
    args = parse_args()
    try:
        root = repository_root()
        write_record(
            root=root,
            manifest_path=rooted(root, args.manifest),
            lock_path=rooted(root, args.lock),
            toolchain_root=rooted(root, args.toolchain_root),
            report_path=rooted(root, args.report),
            check_log_path=rooted(root, args.check_log),
            destination=rooted(root, args.output),
            require_github_context=args.require_github_context,
        )
        print(
            "pdf_toolchain_record_written "
            f"path={rooted(root, args.output)}"
        )
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"ERROR: PDF toolchain record failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
