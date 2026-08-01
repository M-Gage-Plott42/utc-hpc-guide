#!/usr/bin/env python3
"""Build, validate, and record every review-only code-typeface proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    from .build_pdf import locked_tex_font_paths
    from .check_pdf import parse_info
    from .check_pdf_accessibility import parse_verapdf_report
    from .font_proofs import load_proof_context, proof_output_path
    from .write_pdf_toolchain_record import parse_check_log
except ImportError:
    from build_pdf import locked_tex_font_paths
    from check_pdf import parse_info
    from check_pdf_accessibility import parse_verapdf_report
    from font_proofs import load_proof_context, proof_output_path
    from write_pdf_toolchain_record import parse_check_log


EXPECTED_QA_PACKAGES = {
    "mupdf-tools": "1.23.10+ds1-1build3",
    "python3-fonttools": "4.46.0-1build2",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_bundle_sums(root: Path, artifacts: list[Path]) -> Path:
    """Write hashes relative to GitHub's uploaded ``dist`` artifact root."""
    dist = (root / "dist").resolve()
    entries: list[tuple[str, Path]] = []
    for path in artifacts:
        resolved = path.resolve(strict=True)
        if not resolved.is_file() or resolved.is_symlink():
            raise RuntimeError(f"proof artifact is not a regular file: {path}")
        if not resolved.is_relative_to(dist):
            raise RuntimeError(f"proof artifact escaped the dist directory: {path}")
        entries.append((resolved.relative_to(dist).as_posix(), resolved))
    sums = dist / "font-proofs/SHA256SUMS"
    sums.parent.mkdir(parents=True, exist_ok=True)
    sums.write_text(
        "".join(
            f"{sha256(path)}  {relative}\n"
            for relative, path in sorted(entries)
        ),
        encoding="utf-8",
    )
    return sums


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


def run_logged(
    command: list[str],
    *,
    root: Path,
    log: list[str],
) -> None:
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    while True:
        try:
            stdout, stderr = process.communicate(timeout=20)
            break
        except subprocess.TimeoutExpired:
            print(
                "font_proof_command_running "
                f"elapsed_seconds={int(time.monotonic() - started)} "
                f"command={Path(command[1]).name if len(command) > 1 else command[0]}",
                flush=True,
            )
    output = stdout + stderr
    sys.stdout.write(output)
    sys.stdout.flush()
    log.append(output)
    if process.returncode != 0:
        raise RuntimeError(
            f"font proof command failed with status {process.returncode}: "
            + " ".join(command)
        )


def command_output(command: list[str], *, root: Path) -> str:
    result = subprocess.run(
        command,
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return (result.stdout + result.stderr).strip()


def first_nonempty_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def proof_profile_ids(config_path: Path) -> tuple[str, ...]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("font proof config profiles must be a nonempty object")
    return tuple(profiles)


def verify_qa_packages(root: Path, config_path: Path) -> tuple[str, str]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    lock_path = root / config["font_lock"]
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    packages = lock.get("ubuntu_24_04_qa_packages")
    if packages != EXPECTED_QA_PACKAGES:
        raise ValueError("font proof lock does not contain the exact QA package pins")
    for package, expected in sorted(EXPECTED_QA_PACKAGES.items()):
        observed = command_output(
            ["dpkg-query", "-W", "-f=${Version}", package],
            root=root,
        )
        if observed != expected:
            raise RuntimeError(
                f"{package} package mismatch: {observed!r} != {expected!r}"
            )
    return lock_path.relative_to(root).as_posix(), sha256(lock_path)


def ttf_x_height_metrics(path: Path) -> tuple[int, int]:
    """Read units-per-em and regular lowercase-x height from a pinned TTF."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError(
            "python3-fonttools is required for font-metric validation"
        ) from exc
    try:
        with TTFont(path, lazy=True) as font:
            units_per_em = int(font["head"].unitsPerEm)
            os2_x_height = int(getattr(font["OS/2"], "sxHeight", 0))
            if os2_x_height > 0:
                return units_per_em, os2_x_height
            cmap = font.getBestCmap()
            if cmap is None or ord("x") not in cmap:
                raise RuntimeError(f"font lacks a lowercase-x cmap entry: {path}")
            glyph = font["glyf"][cmap[ord("x")]]
            if glyph.yMin != 0 or glyph.yMax <= 0:
                raise RuntimeError(
                    f"font lowercase-x bounds do not start at the baseline: {path}"
                )
            return units_per_em, int(glyph.yMax)
    except (OSError, KeyError) as exc:
        raise RuntimeError(f"could not read pinned font metrics: {path}") from exc


def verify_profile_x_heights(root: Path, contexts) -> tuple[float, ...]:
    """Bind configured size matching to the actual regular face metrics."""
    effective: list[float] = []
    for context in contexts:
        regular, _bold = proof_font_paths(root, context)
        observed = ttf_x_height_metrics(regular)
        expected = (
            context.profile.units_per_em,
            context.profile.x_height_units,
        )
        if observed != expected:
            raise RuntimeError(
                f"{context.profile.id} x-height metric mismatch: "
                f"{observed} != {expected}"
            )
        effective.append(context.profile.effective_x_height_pt)
    if max(effective) - min(effective) > 0.02:
        raise RuntimeError("font proof effective x-height tolerance was exceeded")
    print(
        "font_proof_x_heights_verified "
        f"profiles={len(effective)} min_pt={min(effective):.4f} "
        f"max_pt={max(effective):.4f}"
    )
    return tuple(effective)


def ensure_baseline(
    root: Path,
    manifest_path: Path,
    config_path: Path,
    profile_id: str,
) -> tuple[Path, str]:
    context = load_proof_context(
        root,
        config_path,
        profile_id,
        manifest_path,
    )
    baseline = root / "dist" / context.baseline_filename
    run_logged(
        [
            sys.executable,
            "scripts/build_pdf.py",
            "--manifest",
            manifest_path.relative_to(root).as_posix(),
            "--verify-reproducible",
        ],
        root=root,
        log=[],
    )
    observed = sha256(baseline)
    if observed != context.baseline_sha256:
        raise RuntimeError(
            "immutable RC.1 baseline hash mismatch: "
            f"{observed} != {context.baseline_sha256}"
        )
    print(f"font_proof_baseline_verified sha256={observed}")
    return baseline, observed


def proof_font_paths(root: Path, context) -> tuple[Path, Path]:
    if context.regular_font_path is not None and context.bold_font_path is not None:
        return context.regular_font_path, context.bold_font_path
    regular, bold = locked_tex_font_paths(
        root,
        ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf"),
    )
    return regular, bold


def write_proof_record(
    *,
    root: Path,
    context,
    pdf: Path,
    report: Path,
    check_log: Path,
    baseline_sha256: str,
    font_lock_path: str,
    font_lock_hash: str,
) -> Path:
    pdf_hash = sha256(pdf)
    checks = parse_check_log(
        check_log.read_text(encoding="utf-8"),
        pdf=pdf,
        pdf_sha256=pdf_hash,
    )
    vera = parse_verapdf_report(report.read_bytes())
    if vera.total_jobs != 1 or vera.compliant_jobs != 1:
        raise RuntimeError("proof veraPDF report is not one compliant job")
    info = parse_info(command_output(["pdfinfo", str(pdf)], root=root))
    regular, bold = proof_font_paths(root, context)
    commit = command_output(["git", "rev-parse", "HEAD"], root=root)
    source_hashes = {
        transform.path: sha256(root / transform.path)
        for transform in context.source_transforms
    }
    versions = {
        "pandoc": first_nonempty_line(command_output(["pandoc", "--version"], root=root)),
        "lualatex": first_nonempty_line(command_output(["lualatex", "--version"], root=root)),
        "verapdf": first_nonempty_line(command_output(["verapdf", "--version"], root=root)),
        "qpdf": first_nonempty_line(command_output(["qpdf", "--version"], root=root)),
        "pdftotext": first_nonempty_line(command_output(["pdftotext", "-v"], root=root)),
        "tesseract": first_nonempty_line(command_output(["tesseract", "--version"], root=root)),
        "mutool": first_nonempty_line(command_output(["mutool", "-v"], root=root)),
    }
    lines = [
        "UTC HPC Guide review-only typeface proof record",
        f"status={context.proof_label}",
        "",
        "[run]",
        f"commit={commit}",
        f"github_run_id={os.environ.get('GITHUB_RUN_ID', 'local')}",
        f"github_sha={os.environ.get('GITHUB_SHA', commit)}",
        "",
        "[identity]",
        f"proof_set={context.proof_set}",
        f"proof_identifier={context.proof_identifier}",
        f"profile_id={context.profile.id}",
        f"profile_label={context.profile.label}",
        f"baseline_commit={context.baseline_commit}",
        f"baseline_pdf_sha256={baseline_sha256}",
        "",
        "[inputs]",
        f"base_manifest_sha256={context.base_manifest_hash}",
        f"base_toolchain_lock_sha256={context.base_toolchain_lock_hash}",
        f"proof_config_sha256={context.config_hash}",
        f"proof_font_lock_path={font_lock_path}",
        f"proof_font_lock_sha256={font_lock_hash}",
        f"supplement_sha256={sha256(context.supplement)}",
    ]
    lines.extend(
        f"source.{path}.sha256={digest}"
        for path, digest in sorted(source_hashes.items())
    )
    lines.extend(
        [
            "",
            "[font]",
            f"source={context.profile.font_source}",
            f"size_pt={context.profile.font_size:g}",
            f"leading_pt={context.profile.leading:g}",
            f"fixed_extraction_pitch={context.profile.extraction_pitch:.2f}",
            f"units_per_em={context.profile.units_per_em}",
            f"x_height_units={context.profile.x_height_units}",
            f"effective_x_height_pt={context.profile.effective_x_height_pt:.4f}",
            "fontspec_ligatures=" + ",".join(context.fontspec_ligatures),
            "raw_features=" + ",".join(context.raw_features),
            f"regular_postscript={context.profile.regular_postscript}",
            f"regular_sha256={sha256(regular)}",
            f"bold_postscript={context.profile.bold_postscript}",
            f"bold_sha256={sha256(bold)}",
            "",
            "[toolchain]",
        ]
    )
    lines.extend(f"{name}={value}" for name, value in versions.items())
    lines.extend(
        [
            "mupdf_tools_package=1.23.10+ds1-1build3",
            "python3_fonttools_package=4.46.0-1build2",
            "",
            "[pdf]",
            f"path={pdf.relative_to(root).as_posix()}",
            f"sha256={pdf_hash}",
            f"pages={checks['pages']}",
            f"fonts={checks['fonts']}",
            f"pdf_version={info.get('PDF version')}",
            f"tagged={info.get('Tagged')}",
            "",
            "[validation]",
            "reproducibility=passed",
            "structural_render=passed",
            "fixed_pitch_extraction=passed",
            "one_glyph_per_character=passed",
            "default_cmap_glyph_ids=passed",
            "ocr=passed",
            "pdfua2=passed",
            f"verapdf_report_sha256={sha256(report)}",
            "viewer_clipboard_interoperability=not established by Poppler extraction",
            "real_assistive_technology_review=not tested",
        ]
    )
    destination = check_log.parent / "build-toolchain.txt"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def validate_profile(
    *,
    root: Path,
    manifest_path: Path,
    config_path: Path,
    profile_id: str,
    baseline_sha256: str,
    font_lock_path: str,
    font_lock_hash: str,
) -> tuple[Path, ...]:
    context = load_proof_context(
        root,
        config_path,
        profile_id,
        manifest_path,
    )
    evidence = root / "dist" / "font-proofs" / profile_id
    evidence.mkdir(parents=True, exist_ok=True)
    report = evidence / "verapdf-report.xml"
    check_log = evidence / "check-pdf.log"
    log: list[str] = []
    common = [
        "--manifest",
        manifest_path.relative_to(root).as_posix(),
        "--proof-config",
        config_path.relative_to(root).as_posix(),
        "--proof-profile",
        profile_id,
    ]
    run_logged(
        [sys.executable, "scripts/build_pdf.py", *common, "--verify-reproducible"],
        root=root,
        log=log,
    )
    run_logged(
        [sys.executable, "scripts/check_pdf.py", *common],
        root=root,
        log=log,
    )
    run_logged(
        [sys.executable, "scripts/check_pdf_ocr.py", *common],
        root=root,
        log=log,
    )
    run_logged(
        [
            sys.executable,
            "scripts/check_pdf_accessibility.py",
            *common,
            "--verapdf",
            str(root / ".cache/pdf-toolchain/bin/verapdf"),
            "--report",
            report.relative_to(root).as_posix(),
        ],
        root=root,
        log=log,
    )
    check_log.write_text("".join(log), encoding="utf-8")
    pdf = proof_output_path(root, context)
    record = write_proof_record(
        root=root,
        context=context,
        pdf=pdf,
        report=report,
        check_log=check_log,
        baseline_sha256=baseline_sha256,
        font_lock_path=font_lock_path,
        font_lock_hash=font_lock_hash,
    )
    print(
        "font_proof_profile_passed "
        f"profile={profile_id} sha256={sha256(pdf)}"
    )
    return pdf, check_log, report, record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("pdf/guide_manifest.json"),
    )
    parser.add_argument(
        "--proof-config",
        type=Path,
        default=Path("pdf/font_proofs.json"),
    )
    parser.add_argument("--verify-inputs-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = repository_root()
        manifest_path = rooted(root, args.manifest)
        config_path = rooted(root, args.proof_config)
        profile_ids = proof_profile_ids(config_path)
        contexts = [
            load_proof_context(
                root,
                config_path,
                profile_id,
                manifest_path,
            )
            for profile_id in profile_ids
        ]
        if len(contexts) != 3:
            raise ValueError("font proof matrix must contain exactly three profiles")
        font_lock_path, font_lock_hash = verify_qa_packages(root, config_path)
        verify_profile_x_heights(root, contexts)
        if args.verify_inputs_only:
            print(
                "font_proof_inputs_verified "
                f"profiles={len(contexts)} lock_sha256={font_lock_hash}"
            )
            return 0
        _baseline, baseline_hash = ensure_baseline(
            root,
            manifest_path,
            config_path,
            profile_ids[0],
        )
        artifacts: list[Path] = []
        for profile_id in profile_ids:
            artifacts.extend(
                validate_profile(
                    root=root,
                    manifest_path=manifest_path,
                    config_path=config_path,
                    profile_id=profile_id,
                    baseline_sha256=baseline_hash,
                    font_lock_path=font_lock_path,
                    font_lock_hash=font_lock_hash,
                )
            )
        write_bundle_sums(root, artifacts)
        print(
            "font_proof_bundle_passed "
            f"profiles={len(profile_ids)} baseline_sha256={baseline_hash}"
        )
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: font proof validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
