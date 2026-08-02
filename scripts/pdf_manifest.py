"""Shared validation for the printable-guide manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 2
PDF_STANDARD = "ua-2"
DOCUMENT_LANGUAGE = "en-US"
FIGURE_COUNT = 3
RELEASE_TARGET = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
)
ARTIFACT_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9.-]{0,126}[a-z0-9])?")


def _require_string(manifest: dict[str, Any], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"PDF manifest {key} must be a nonempty string")
    return value


def _require_string_list(manifest: dict[str, Any], key: str) -> list[str]:
    value = manifest.get(key)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ValueError(f"PDF manifest {key} must be a nonempty list of strings")
    return value


def _validate_relative_path(raw_path: str, *, label: str) -> PurePosixPath:
    normalized = PurePosixPath(raw_path)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError(f"{label} must stay inside the repository: {raw_path}")
    return normalized


def derive_pdf_trailer_id(document_version: str, source_date_epoch: int) -> str:
    """Derive the stable 128-bit PDF trailer identifier from release metadata."""
    seed = f"utc-hpc-guide:v{document_version}:{source_date_epoch}".encode("ascii")
    return hashlib.sha256(seed).hexdigest()[:32]


def _validate_release_state(manifest: dict[str, Any]) -> None:
    status = _require_string(manifest, "release_status")
    target = _require_string(manifest, "release_target")
    version = _require_string(manifest, "document_version")
    filename = _require_string(manifest, "output_filename")
    if RELEASE_TARGET.fullmatch(target) is None:
        raise ValueError(
            "release_target must be a safe numeric major.minor.patch version"
        )
    if status == "candidate":
        if not re.fullmatch(re.escape(target) + r"-rc\.[1-9][0-9]*", version):
            raise ValueError(
                "candidate document_version must match release_target-rc.N"
            )
        expected_filename = f"UTC_HPC_Guide_v{version}.pdf"
    elif status == "final":
        if version != target:
            raise ValueError("final document_version must equal release_target")
        expected_filename = "UTC_HPC_Guide.pdf"
    else:
        raise ValueError("release_status must be candidate or final")
    if filename != expected_filename:
        raise ValueError(
            "output_filename does not match release state: "
            f"expected {expected_filename}"
        )


def load_manifest(
    path: Path,
    *,
    root: Path | None = None,
    validate_sources: bool = False,
) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"PDF manifest schema_version must be {SCHEMA_VERSION}"
        )

    for key in (
        "title",
        "subtitle",
        "author",
        "date",
        "release_status",
        "release_target",
        "document_version",
        "pdf_trailer_id",
        "output_filename",
        "pdf_standard",
        "language",
        "header_source",
        "template_source",
        "code_filter_source",
    ):
        _require_string(manifest, key)
    for key in (
        "core_sources",
        "examples",
        "required_pdf_text",
        "required_ocr_text",
        "expected_figure_alt_text",
    ):
        _require_string_list(manifest, key)

    page_ocr = manifest.get("required_page_ocr_text")
    if not isinstance(page_ocr, dict) or not page_ocr:
        raise ValueError(
            "PDF manifest required_page_ocr_text must be a nonempty object"
        )
    for page, phrases in page_ocr.items():
        if not isinstance(page, str) or re.fullmatch(r"[1-9][0-9]*", page) is None:
            raise ValueError(
                "PDF manifest required_page_ocr_text keys must be positive page numbers"
            )
        if (
            not isinstance(phrases, list)
            or not phrases
            or any(not isinstance(phrase, str) or not phrase.strip() for phrase in phrases)
        ):
            raise ValueError(
                "PDF manifest required_page_ocr_text values must be "
                "nonempty lists of strings"
            )

    if not isinstance(manifest.get("source_date_epoch"), int):
        raise ValueError("PDF manifest source_date_epoch must be an integer")
    if manifest["source_date_epoch"] < 1:
        raise ValueError("PDF manifest source_date_epoch must be positive")
    if not re.fullmatch(r"[0-9a-f]{32}", manifest["pdf_trailer_id"]):
        raise ValueError(
            "PDF manifest pdf_trailer_id must be exactly 32 lowercase hex characters"
        )
    if manifest["pdf_standard"] != PDF_STANDARD:
        raise ValueError(f"PDF manifest pdf_standard must be {PDF_STANDARD}")
    if manifest["language"] != DOCUMENT_LANGUAGE:
        raise ValueError(f"PDF manifest language must be {DOCUMENT_LANGUAGE}")
    if len(manifest["expected_figure_alt_text"]) != FIGURE_COUNT:
        raise ValueError(
            f"PDF manifest expected_figure_alt_text must contain {FIGURE_COUNT} items"
        )
    if len(set(manifest["expected_figure_alt_text"])) != FIGURE_COUNT:
        raise ValueError("PDF figure alternative text entries must be unique")
    if any(len(item.split()) < 5 for item in manifest["expected_figure_alt_text"]):
        raise ValueError("PDF figure alternative text must be context-meaningful")

    structure_counts = manifest.get("expected_structure_counts")
    if not isinstance(structure_counts, dict) or not structure_counts:
        raise ValueError(
            "PDF manifest expected_structure_counts must be a nonempty object"
        )
    for role, count in structure_counts.items():
        if (
            not isinstance(role, str)
            or re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", role) is None
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count < 1
        ):
            raise ValueError(
                "PDF manifest expected_structure_counts must map safe role "
                "names to positive integers"
            )

    appendices = manifest.get("site_appendices")
    if not isinstance(appendices, list) or not appendices:
        raise ValueError("PDF manifest site_appendices must be a nonempty list")
    for index, appendix in enumerate(appendices):
        if not isinstance(appendix, dict):
            raise ValueError(f"PDF manifest site_appendices[{index}] must be an object")
        _require_string(appendix, "path")
        _require_string(appendix, "title")

    _validate_release_state(manifest)
    expected_trailer_id = derive_pdf_trailer_id(
        manifest["document_version"],
        manifest["source_date_epoch"],
    )
    if manifest["pdf_trailer_id"] != expected_trailer_id:
        raise ValueError(
            "PDF manifest pdf_trailer_id must match the deterministic "
            "document_version/source_date_epoch derivation"
        )

    if validate_sources:
        if root is None:
            raise ValueError("root is required when validating PDF sources")
        source_paths = [
            manifest["header_source"],
            manifest["template_source"],
            manifest["code_filter_source"],
            *manifest["core_sources"],
        ]
        source_paths.extend(item["path"] for item in appendices)
        source_paths.extend(manifest["examples"])
        for raw_path in source_paths:
            normalized = _validate_relative_path(
                raw_path,
                label="PDF source",
            )
            if not (root / normalized).is_file():
                raise ValueError(f"PDF source does not exist: {raw_path}")
    return manifest


def output_path(root: Path, manifest: dict[str, Any]) -> Path:
    filename = _validate_relative_path(
        manifest["output_filename"],
        label="PDF output filename",
    )
    if len(filename.parts) != 1:
        raise ValueError("PDF output_filename must not contain directories")
    return root / "dist" / filename


def distribution_status(manifest: dict[str, Any]) -> str:
    """Describe document state without claiming that an artifact is published."""
    _validate_release_state(manifest)
    if manifest["release_status"] == "candidate":
        return (
            f"review-only release candidate for v{manifest['release_target']}; "
            "not stable"
        )
    return (
        f"final document build for v{manifest['document_version']}; "
        "publication is separate"
    )


def workflow_metadata(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    """Return newline-safe GitHub Actions outputs derived from the manifest."""
    _validate_release_state(manifest)
    version = manifest["document_version"]
    status = manifest["release_status"]
    artifact_label = f"utc-hpc-guide-v{version}-{status}"
    if ARTIFACT_LABEL.fullmatch(artifact_label) is None:
        raise ValueError("manifest-derived artifact label is not workflow-safe")
    relative_output = output_path(root, manifest).relative_to(root).as_posix()
    if re.fullmatch(r"dist/[A-Za-z0-9][A-Za-z0-9._-]*\.pdf", relative_output) is None:
        raise ValueError("manifest-derived PDF path is not workflow-safe")
    return {
        "path": relative_output,
        "document_version": version,
        "release_status": status,
        "artifact_label": artifact_label,
    }
