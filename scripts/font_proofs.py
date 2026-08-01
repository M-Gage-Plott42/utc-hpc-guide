"""Strict loading and derivation for review-only PDF font proofs.

The font-proof configuration is additive: the release manifest remains the
source of truth, while this module verifies the proof-specific supplement,
source transformations, and vendored font lock before deriving an effective
manifest for one named profile.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from .pdf_manifest import load_manifest
except ImportError:
    from pdf_manifest import load_manifest


SCHEMA_VERSION = 1
TEXLIVE_DEJAVU = "texlive-dejavu"
SAFE_ID = re.compile(r"[a-z0-9](?:[a-z0-9.-]{0,126}[a-z0-9])?")
SAFE_PROFILE_ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?")
SAFE_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,190}\.pdf")
SAFE_FONT_TOKEN = re.compile(r"[A-Za-z0-9*][A-Za-z0-9*_.-]{0,126}")
SAFE_POSTSCRIPT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,126}")
HEX_40 = re.compile(r"[0-9a-f]{40}")
HEX_64 = re.compile(r"[0-9a-f]{64}")
REQUIRED_FONTSPEC_LIGATURES = frozenset(
    {
        "RequiredOff",
        "CommonOff",
        "ContextualOff",
        "DiscretionaryOff",
        "HistoricOff",
        "TeXOff",
    }
)
REQUIRED_RAW_FEATURES = frozenset(
    {"-calt", "-liga", "-clig", "-dlig", "-hlig", "-rlig", "-tlig"}
)
CONFIG_KEYS = frozenset(
    {
        "schema_version",
        "proof_set",
        "proof_identifier",
        "proof_label",
        "base_manifest",
        "base_manifest_sha256",
        "base_toolchain_lock",
        "base_toolchain_lock_sha256",
        "font_lock",
        "baseline",
        "supplement",
        "structure_count_deltas",
        "required_pdf_text",
        "required_ocr_text",
        "fontspec_ligatures",
        "raw_features",
        "source_transforms",
        "profiles",
    }
)
PROFILE_KEYS = frozenset(
    {
        "label",
        "font_source",
        "font_stem",
        "upright_pattern",
        "bold_pattern",
        "regular_postscript",
        "bold_postscript",
        "font_size",
        "leading",
        "extraction_pitch",
        "units_per_em",
        "x_height_units",
        "output_filename",
    }
)
LOCK_SOURCE_KEYS = frozenset(
    {
        "project",
        "project_url",
        "release",
        "release_tag",
        "release_commit",
        "release_url",
        "archive_url",
        "archive_size",
        "archive_sha256",
        "license_file",
        "regular",
        "bold",
    }
)


@dataclass(frozen=True)
class SourceTransform:
    """One exact, review-only source substitution."""

    path: str
    original: str
    replacement: str


@dataclass(frozen=True)
class ProofProfile:
    """Validated settings for one complete-guide typeface proof."""

    id: str
    label: str
    font_source: str
    font_size: float
    leading: float
    extraction_pitch: float
    units_per_em: int
    x_height_units: int
    output_filename: str
    regular_postscript: str
    bold_postscript: str
    font_stem: str
    upright_pattern: str
    bold_pattern: str

    @property
    def effective_x_height_pt(self) -> float:
        """Return the regular face's configured lowercase-x height in points."""
        return self.font_size * self.x_height_units / self.units_per_em


@dataclass(frozen=True)
class ProofContext:
    """Validated shared and profile-specific inputs for a proof build."""

    config_path: Path
    config_hash: str
    lock_hash: str
    proof_set: str
    proof_identifier: str
    proof_label: str
    base_manifest: dict[str, Any]
    base_manifest_hash: str
    base_toolchain_lock: Path
    base_toolchain_lock_hash: str
    baseline_commit: str
    baseline_document_version: str
    baseline_filename: str
    baseline_sha256: str
    supplement: Path
    structure_count_deltas: dict[str, int]
    required_pdf_text: tuple[str, ...]
    required_ocr_text: tuple[str, ...]
    fontspec_ligatures: tuple[str, ...]
    raw_features: tuple[str, ...]
    ligature_denylist: tuple[str, ...]
    source_transforms: tuple[SourceTransform, ...]
    profile: ProofProfile
    regular_font_path: Path | None
    bold_font_path: Path | None

    @property
    def regular_path(self) -> Path | None:
        """Alias used by font-variable construction."""
        return self.regular_font_path

    @property
    def bold_path(self) -> Path | None:
        """Alias used by font-variable construction."""
        return self.bold_font_path


def _duplicate_rejecting_object(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key is not allowed: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _parse_json(raw: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def _require_exact_keys(
    value: dict[str, Any],
    expected: frozenset[str],
    *,
    label: str,
) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"{label} keys do not match the schema "
            f"(missing={missing}, extra={extra})"
        )


def _require_string(
    value: dict[str, Any],
    key: str,
    *,
    label: str,
) -> str:
    result = value.get(key)
    if (
        not isinstance(result, str)
        or not result.strip()
        or "\x00" in result
        or "\r" in result
    ):
        raise ValueError(f"{label} {key} must be a nonempty string")
    return result


def _require_positive_integer(
    value: dict[str, Any],
    key: str,
    *,
    label: str,
) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 1:
        raise ValueError(f"{label} {key} must be a positive integer")
    return result


def _require_number(
    value: dict[str, Any],
    key: str,
    *,
    minimum: float,
    maximum: float,
    label: str,
) -> float:
    result = value.get(key)
    if (
        not isinstance(result, (int, float))
        or isinstance(result, bool)
        or not math.isfinite(float(result))
        or not minimum <= float(result) <= maximum
    ):
        raise ValueError(
            f"{label} {key} must be a finite number from {minimum:g} "
            f"through {maximum:g}"
        )
    return float(result)


def _require_sha256(value: str, *, label: str) -> str:
    if HEX_64.fullmatch(value) is None:
        raise ValueError(f"{label} must be exactly 64 lowercase hex characters")
    return value


def _safe_relative_path(raw_path: str, *, label: str) -> PurePosixPath:
    if (
        not isinstance(raw_path, str)
        or not raw_path
        or raw_path != raw_path.strip()
        or "\\" in raw_path
        or "\x00" in raw_path
    ):
        raise ValueError(f"{label} must be a normalized repository-relative path")
    path = PurePosixPath(raw_path)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != raw_path
    ):
        raise ValueError(f"{label} must stay inside the repository: {raw_path}")
    return path


def _path_argument_relative(
    root: Path,
    path: Path,
    *,
    label: str,
) -> PurePosixPath:
    candidate = path if path.is_absolute() else root / path
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the repository") from exc
    return _safe_relative_path(relative.as_posix(), label=label)


def _read_repository_file(
    root: Path,
    relative: PurePosixPath,
    *,
    label: str,
) -> bytes:
    """Read a regular repository file through a retained no-follow chain."""
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    descriptors: list[int] = []
    final_descriptor: int | None = None
    try:
        root_descriptor = os.open(root, directory_flags)
        descriptors.append(root_descriptor)
        current = root_descriptor
        for component in relative.parts[:-1]:
            current = os.open(
                component,
                directory_flags | no_follow,
                dir_fd=current,
            )
            descriptors.append(current)
        final_descriptor = os.open(
            relative.parts[-1],
            os.O_RDONLY | os.O_CLOEXEC | no_follow,
            dir_fd=current,
        )
        metadata = os.fstat(final_descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"{label} must be a regular file")
        with os.fdopen(final_descriptor, "rb", closefd=True) as handle:
            final_descriptor = None
            return handle.read()
    except OSError as exc:
        raise ValueError(
            f"{label} must exist as a regular file without symbolic links: "
            f"{relative}"
        ) from exc
    finally:
        if final_descriptor is not None:
            os.close(final_descriptor)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_string_list(
    value: Any,
    *,
    label: str,
) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(
            not isinstance(item, str)
            or not item.strip()
            or "\x00" in item
            or "\r" in item
            for item in value
        )
    ):
        raise ValueError(f"{label} must be a nonempty list of nonempty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{label} must not contain duplicates")
    return tuple(value)


def _validate_url(raw: str, *, label: str) -> str:
    if (
        not raw.startswith("https://")
        or any(character.isspace() for character in raw)
        or "\x00" in raw
    ):
        raise ValueError(f"{label} must be a whitespace-free HTTPS URL")
    return raw


def _validate_locked_file(
    root: Path,
    entry: dict[str, Any],
    *,
    label: str,
    expected_suffix: str,
) -> tuple[Path, str]:
    if not isinstance(entry, dict):
        raise ValueError(f"{label} must be an object")
    is_license = label.endswith("license_file")
    expected_keys = (
        frozenset(
            {
                "path",
                "upstream_url",
                "upstream_size",
                "upstream_sha256",
                "normalization",
                "stripped_trailing_spaces",
                "size",
                "sha256",
            }
        )
        if is_license
        else frozenset(
            {"path", "archive_member", "size", "sha256", "postscript_name"}
        )
    )
    _require_exact_keys(entry, expected_keys, label=label)
    raw_path = _require_string(entry, "path", label=label)
    relative = _safe_relative_path(raw_path, label=f"{label} path")
    if relative.suffix.casefold() != expected_suffix:
        raise ValueError(f"{label} path must end in {expected_suffix}")
    raw = _read_repository_file(root, relative, label=label)
    expected_size = _require_positive_integer(entry, "size", label=label)
    if len(raw) != expected_size:
        raise ValueError(
            f"{label} size mismatch: expected {expected_size}, got {len(raw)}"
        )
    expected_hash = _require_sha256(
        _require_string(entry, "sha256", label=label),
        label=f"{label} sha256",
    )
    actual_hash = _sha256(raw)
    if actual_hash != expected_hash:
        raise ValueError(
            f"{label} SHA-256 mismatch: expected {expected_hash}, "
            f"got {actual_hash}"
        )
    if is_license:
        if any(
            line.rstrip(b"\r\n").endswith((b" ", b"\t"))
            for line in raw.splitlines(keepends=True)
        ):
            raise ValueError(f"{label} local copy contains trailing whitespace")
        stripped_spaces = entry.get("stripped_trailing_spaces")
        if not isinstance(stripped_spaces, dict):
            raise ValueError(
                f"{label} stripped_trailing_spaces must be an object"
            )
        reconstructed_lines = raw.splitlines(keepends=True)
        for line_key, count in stripped_spaces.items():
            if (
                not isinstance(line_key, str)
                or re.fullmatch(r"[1-9][0-9]*", line_key) is None
                or not isinstance(count, int)
                or isinstance(count, bool)
                or not 1 <= count <= 32
            ):
                raise ValueError(
                    f"{label} stripped trailing-space entries must map "
                    "canonical line numbers to counts from 1 through 32"
                )
            line_index = int(line_key) - 1
            if line_index >= len(reconstructed_lines):
                raise ValueError(
                    f"{label} stripped trailing-space line is out of range: "
                    f"{line_key}"
                )
            line = reconstructed_lines[line_index]
            if line.endswith(b"\n"):
                reconstructed_lines[line_index] = (
                    line[:-1] + b" " * count + b"\n"
                )
            else:
                reconstructed_lines[line_index] = line + b" " * count
        normalized_upstream = b"".join(reconstructed_lines)
        normalization = _require_string(entry, "normalization", label=label)
        if normalization == "none":
            upstream_raw = normalized_upstream
        elif normalization == "crlf-to-lf":
            if b"\r" in raw:
                raise ValueError(
                    f"{label} crlf-to-lf copy must contain only LF newlines"
                )
            upstream_raw = normalized_upstream.replace(b"\n", b"\r\n")
        else:
            raise ValueError(
                f"{label} normalization must be none or crlf-to-lf"
            )
        upstream_size = _require_positive_integer(
            entry,
            "upstream_size",
            label=label,
        )
        if len(upstream_raw) != upstream_size:
            raise ValueError(
                f"{label} reconstructed upstream size mismatch: "
                f"expected {upstream_size}, got {len(upstream_raw)}"
            )
        upstream_hash = _require_sha256(
            _require_string(entry, "upstream_sha256", label=label),
            label=f"{label} upstream_sha256",
        )
        actual_upstream_hash = _sha256(upstream_raw)
        if actual_upstream_hash != upstream_hash:
            raise ValueError(
                f"{label} reconstructed upstream SHA-256 mismatch: "
                f"expected {upstream_hash}, got {actual_upstream_hash}"
            )
    return root / Path(relative), raw_path


def _load_lock(
    root: Path,
    lock_relative: PurePosixPath,
    profiles: dict[str, ProofProfile],
) -> tuple[str, dict[str, tuple[Path, Path]]]:
    raw = _read_repository_file(root, lock_relative, label="font proof lock")
    lock = _parse_json(raw, label="font proof lock")
    _require_exact_keys(
        lock,
        frozenset(
            {
                "schema_version",
                "license",
                "ubuntu_24_04_qa_packages",
                "sources",
            }
        ),
        label="font proof lock",
    )
    if lock.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"font proof lock schema_version must be {SCHEMA_VERSION}"
        )
    _require_string(lock, "license", label="font proof lock")
    qa_packages = lock.get("ubuntu_24_04_qa_packages")
    if qa_packages != {
        "mupdf-tools": "1.23.10+ds1-1build3",
        "python3-fonttools": "4.46.0-1build2",
    }:
        raise ValueError(
            "font proof lock must pin the Ubuntu 24.04 MuPDF and FontTools "
            "packages"
        )
    sources = lock.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("font proof lock sources must be an object")

    required_sources = {
        profile.font_source
        for profile in profiles.values()
        if profile.font_source != TEXLIVE_DEJAVU
    }
    if set(sources) != required_sources:
        raise ValueError(
            "font proof lock sources must exactly match vendored profile "
            f"sources: expected {sorted(required_sources)}, got {sorted(sources)}"
        )

    used_paths: set[str] = set()
    resolved: dict[str, tuple[Path, Path]] = {}
    for source_id, source in sources.items():
        if SAFE_ID.fullmatch(source_id) is None:
            raise ValueError(f"font proof lock source ID is unsafe: {source_id}")
        if not isinstance(source, dict):
            raise ValueError(f"font proof lock source {source_id} must be an object")
        source_label = f"font proof lock source {source_id}"
        _require_exact_keys(source, LOCK_SOURCE_KEYS, label=source_label)
        for key in ("project", "release", "release_tag"):
            _require_string(source, key, label=source_label)
        for key in ("project_url", "release_url", "archive_url"):
            _validate_url(
                _require_string(source, key, label=source_label),
                label=f"{source_label} {key}",
            )
        release_commit = _require_string(
            source,
            "release_commit",
            label=source_label,
        )
        if HEX_40.fullmatch(release_commit) is None:
            raise ValueError(
                f"{source_label} release_commit must be 40 lowercase hex characters"
            )
        _require_positive_integer(source, "archive_size", label=source_label)
        _require_sha256(
            _require_string(source, "archive_sha256", label=source_label),
            label=f"{source_label} archive_sha256",
        )

        license_entry = source.get("license_file")
        license_path, license_raw_path = _validate_locked_file(
            root,
            license_entry,
            label=f"{source_label} license_file",
            expected_suffix=".txt",
        )
        if not isinstance(license_entry, dict):
            raise AssertionError("validated license entry must be an object")
        _validate_url(
            _require_string(
                license_entry,
                "upstream_url",
                label=f"{source_label} license_file",
            ),
            label=f"{source_label} license_file upstream_url",
        )

        matching_profiles = [
            profile
            for profile in profiles.values()
            if profile.font_source == source_id
        ]
        regular_names = {
            profile.regular_postscript for profile in matching_profiles
        }
        bold_names = {profile.bold_postscript for profile in matching_profiles}
        if len(regular_names) != 1 or len(bold_names) != 1:
            raise ValueError(
                f"profiles sharing {source_id} must use the same PostScript names"
            )
        expected_names = {
            "regular": regular_names.pop(),
            "bold": bold_names.pop(),
        }
        face_paths: dict[str, Path] = {}
        for weight in ("regular", "bold"):
            face_label = f"{source_label} {weight}"
            face = source.get(weight)
            face_path, face_raw_path = _validate_locked_file(
                root,
                face,
                label=face_label,
                expected_suffix=".ttf",
            )
            if not isinstance(face, dict):
                raise AssertionError("validated font face entry must be an object")
            archive_member = _require_string(
                face,
                "archive_member",
                label=face_label,
            )
            _safe_relative_path(
                archive_member,
                label=f"{face_label} archive_member",
            )
            postscript_name = _require_string(
                face,
                "postscript_name",
                label=face_label,
            )
            if SAFE_POSTSCRIPT.fullmatch(postscript_name) is None:
                raise ValueError(f"{face_label} postscript_name is unsafe")
            expected_postscript = expected_names[weight]
            if postscript_name != expected_postscript:
                raise ValueError(
                    f"{face_label} postscript_name does not match its profile"
                )
            face_paths[weight] = face_path
            if face_raw_path in used_paths:
                raise ValueError(
                    f"font proof lock reuses a vendored path: {face_raw_path}"
                )
            used_paths.add(face_raw_path)
        if license_raw_path in used_paths:
            raise ValueError(
                f"font proof lock reuses a vendored path: {license_raw_path}"
            )
        used_paths.add(license_raw_path)
        if license_path in face_paths.values():
            raise ValueError(f"{source_label} license and font paths must differ")
        resolved[source_id] = (face_paths["regular"], face_paths["bold"])
    return _sha256(raw), resolved


def _parse_profiles(value: Any) -> dict[str, ProofProfile]:
    if not isinstance(value, dict) or not value:
        raise ValueError("font proof profiles must be a nonempty object")
    profiles: dict[str, ProofProfile] = {}
    output_filenames: set[str] = set()
    labels: set[str] = set()
    for profile_id, raw_profile in value.items():
        if SAFE_PROFILE_ID.fullmatch(profile_id) is None:
            raise ValueError(f"font proof profile ID is unsafe: {profile_id}")
        if not isinstance(raw_profile, dict):
            raise ValueError(f"font proof profile {profile_id} must be an object")
        profile_label = f"font proof profile {profile_id}"
        _require_exact_keys(raw_profile, PROFILE_KEYS, label=profile_label)
        label = _require_string(raw_profile, "label", label=profile_label)
        if "\n" in label:
            raise ValueError(f"{profile_label} label must be one line")
        font_source = _require_string(
            raw_profile,
            "font_source",
            label=profile_label,
        )
        if (
            font_source != TEXLIVE_DEJAVU
            and SAFE_ID.fullmatch(font_source) is None
        ):
            raise ValueError(f"{profile_label} font_source is unsafe")
        font_size = _require_number(
            raw_profile,
            "font_size",
            minimum=7,
            maximum=14,
            label=profile_label,
        )
        leading = _require_number(
            raw_profile,
            "leading",
            minimum=7,
            maximum=20,
            label=profile_label,
        )
        if leading <= font_size:
            raise ValueError(f"{profile_label} leading must be greater than font_size")
        extraction_pitch = _require_number(
            raw_profile,
            "extraction_pitch",
            minimum=3,
            maximum=10,
            label=profile_label,
        )
        units_per_em = _require_positive_integer(
            raw_profile,
            "units_per_em",
            label=profile_label,
        )
        if not 500 <= units_per_em <= 4096:
            raise ValueError(
                f"{profile_label} units_per_em must be from 500 through 4096"
            )
        x_height_units = _require_positive_integer(
            raw_profile,
            "x_height_units",
            label=profile_label,
        )
        if x_height_units >= units_per_em:
            raise ValueError(
                f"{profile_label} x_height_units must be less than units_per_em"
            )
        output_filename = _require_string(
            raw_profile,
            "output_filename",
            label=profile_label,
        )
        if SAFE_FILENAME.fullmatch(output_filename) is None:
            raise ValueError(
                f"{profile_label} output_filename must be one safe PDF filename"
            )
        regular_postscript = _require_string(
            raw_profile,
            "regular_postscript",
            label=profile_label,
        )
        bold_postscript = _require_string(
            raw_profile,
            "bold_postscript",
            label=profile_label,
        )
        for key, token in (
            (
                "font_stem",
                _require_string(raw_profile, "font_stem", label=profile_label),
            ),
            (
                "upright_pattern",
                _require_string(raw_profile, "upright_pattern", label=profile_label),
            ),
            (
                "bold_pattern",
                _require_string(raw_profile, "bold_pattern", label=profile_label),
            ),
        ):
            if SAFE_FONT_TOKEN.fullmatch(token) is None:
                raise ValueError(f"{profile_label} {key} is unsafe")
        if SAFE_POSTSCRIPT.fullmatch(regular_postscript) is None:
            raise ValueError(f"{profile_label} regular_postscript is unsafe")
        if SAFE_POSTSCRIPT.fullmatch(bold_postscript) is None:
            raise ValueError(f"{profile_label} bold_postscript is unsafe")
        if regular_postscript == bold_postscript:
            raise ValueError(
                f"{profile_label} regular and bold PostScript names must differ"
            )
        if output_filename in output_filenames:
            raise ValueError(
                f"font proof profile output_filename is duplicated: {output_filename}"
            )
        if label in labels:
            raise ValueError(f"font proof profile label is duplicated: {label}")
        output_filenames.add(output_filename)
        labels.add(label)
        profiles[profile_id] = ProofProfile(
            id=profile_id,
            label=label,
            font_source=font_source,
            font_size=font_size,
            leading=leading,
            extraction_pitch=extraction_pitch,
            units_per_em=units_per_em,
            x_height_units=x_height_units,
            output_filename=output_filename,
            regular_postscript=regular_postscript,
            bold_postscript=bold_postscript,
            font_stem=raw_profile["font_stem"],
            upright_pattern=raw_profile["upright_pattern"],
            bold_pattern=raw_profile["bold_pattern"],
        )
    effective_heights = [
        profile.effective_x_height_pt for profile in profiles.values()
    ]
    if max(effective_heights) - min(effective_heights) > 0.02:
        raise ValueError(
            "font proof effective x-heights must stay within 0.02 pt; "
            f"observed {min(effective_heights):.4f} through "
            f"{max(effective_heights):.4f} pt"
        )
    return profiles


def load_proof_context(
    root: Path,
    config_path: Path,
    profile_id: str,
    manifest_path: Path,
) -> ProofContext:
    """Load one proof profile and verify every local input it names."""
    root = root.resolve(strict=True)
    config_relative = _path_argument_relative(
        root,
        config_path,
        label="font proof config path",
    )
    config_raw = _read_repository_file(
        root,
        config_relative,
        label="font proof config",
    )
    config = _parse_json(config_raw, label="font proof config")
    _require_exact_keys(config, CONFIG_KEYS, label="font proof config")
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"font proof config schema_version must be {SCHEMA_VERSION}"
        )

    proof_set = _require_string(config, "proof_set", label="font proof config")
    if SAFE_ID.fullmatch(proof_set) is None:
        raise ValueError("font proof config proof_set is unsafe")
    proof_identifier = _require_string(
        config,
        "proof_identifier",
        label="font proof config",
    )
    if SAFE_ID.fullmatch(proof_identifier) is None:
        raise ValueError("font proof config proof_identifier is unsafe")
    proof_label = _require_string(
        config,
        "proof_label",
        label="font proof config",
    )
    if "\n" in proof_label:
        raise ValueError("font proof config proof_label must be one line")

    configured_manifest = _safe_relative_path(
        _require_string(config, "base_manifest", label="font proof config"),
        label="font proof config base_manifest",
    )
    requested_manifest = _path_argument_relative(
        root,
        manifest_path,
        label="font proof manifest path",
    )
    if requested_manifest != configured_manifest:
        raise ValueError(
            "font proof manifest path must exactly match config base_manifest"
        )
    manifest_raw = _read_repository_file(
        root,
        requested_manifest,
        label="font proof base manifest",
    )
    configured_manifest_hash = _require_sha256(
        _require_string(
            config,
            "base_manifest_sha256",
            label="font proof config",
        ),
        label="font proof config base_manifest_sha256",
    )
    actual_manifest_hash = _sha256(manifest_raw)
    if actual_manifest_hash != configured_manifest_hash:
        raise ValueError(
            "font proof base manifest SHA-256 mismatch: "
            f"expected {configured_manifest_hash}, got {actual_manifest_hash}"
        )
    base_manifest = load_manifest(
        root / Path(requested_manifest),
        root=root,
        validate_sources=True,
    )

    toolchain_relative = _safe_relative_path(
        _require_string(
            config,
            "base_toolchain_lock",
            label="font proof config",
        ),
        label="font proof config base_toolchain_lock",
    )
    toolchain_raw = _read_repository_file(
        root,
        toolchain_relative,
        label="font proof base toolchain lock",
    )
    configured_toolchain_hash = _require_sha256(
        _require_string(
            config,
            "base_toolchain_lock_sha256",
            label="font proof config",
        ),
        label="font proof config base_toolchain_lock_sha256",
    )
    actual_toolchain_hash = _sha256(toolchain_raw)
    if actual_toolchain_hash != configured_toolchain_hash:
        raise ValueError(
            "font proof base toolchain lock SHA-256 mismatch: "
            f"expected {configured_toolchain_hash}, got {actual_toolchain_hash}"
        )

    baseline = config.get("baseline")
    if not isinstance(baseline, dict):
        raise ValueError("font proof config baseline must be an object")
    _require_exact_keys(
        baseline,
        frozenset({"commit", "document_version", "filename", "sha256"}),
        label="font proof config baseline",
    )
    baseline_commit = _require_string(
        baseline,
        "commit",
        label="font proof config baseline",
    )
    if HEX_40.fullmatch(baseline_commit) is None:
        raise ValueError(
            "font proof baseline commit must be 40 lowercase hex characters"
        )
    baseline_document_version = _require_string(
        baseline,
        "document_version",
        label="font proof config baseline",
    )
    baseline_filename = _require_string(
        baseline,
        "filename",
        label="font proof config baseline",
    )
    if SAFE_FILENAME.fullmatch(baseline_filename) is None:
        raise ValueError("font proof baseline filename must be one safe PDF filename")
    baseline_sha256 = _require_sha256(
        _require_string(baseline, "sha256", label="font proof config baseline"),
        label="font proof baseline sha256",
    )
    if baseline_document_version != base_manifest["document_version"]:
        raise ValueError(
            "font proof baseline document_version must match the base manifest"
        )
    if baseline_filename != base_manifest["output_filename"]:
        raise ValueError("font proof baseline filename must match the base manifest")

    supplement_relative = _safe_relative_path(
        _require_string(config, "supplement", label="font proof config"),
        label="font proof supplement",
    )
    if supplement_relative.suffix.casefold() != ".md":
        raise ValueError("font proof supplement must be a Markdown file")
    supplement_raw = _read_repository_file(
        root,
        supplement_relative,
        label="font proof supplement",
    )
    try:
        supplement_text = supplement_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("font proof supplement must be UTF-8") from exc

    deltas = config.get("structure_count_deltas")
    if deltas != {"H1": 1, "Code": 2}:
        raise ValueError(
            "font proof structure_count_deltas must be exactly H1 +1 and Code +2"
        )
    required_pdf_text = _require_string_list(
        config.get("required_pdf_text"),
        label="font proof required_pdf_text",
    )
    required_ocr_text = _require_string_list(
        config.get("required_ocr_text"),
        label="font proof required_ocr_text",
    )
    for phrase in required_pdf_text:
        if phrase not in supplement_text:
            raise ValueError(
                f"font proof supplement is missing required proof text: {phrase}"
            )
    for phrase in required_ocr_text:
        if phrase.casefold() not in supplement_text.casefold():
            raise ValueError(
                f"font proof supplement is missing required OCR text: {phrase}"
            )

    fontspec_ligatures = _require_string_list(
        config.get("fontspec_ligatures"),
        label="font proof fontspec_ligatures",
    )
    if frozenset(fontspec_ligatures) != REQUIRED_FONTSPEC_LIGATURES:
        raise ValueError(
            "font proof fontspec_ligatures must disable required, common, "
            "contextual, discretionary, historic, and TeX ligatures"
        )
    raw_features = _require_string_list(
        config.get("raw_features"),
        label="font proof raw_features",
    )
    if frozenset(raw_features) != REQUIRED_RAW_FEATURES:
        raise ValueError(
            "font proof raw_features must explicitly disable the locked "
            "ligature and contextual feature denylist"
        )

    transforms = config.get("source_transforms")
    if not isinstance(transforms, list) or not transforms:
        raise ValueError("font proof source_transforms must be a nonempty list")
    parsed_transforms: list[SourceTransform] = []
    transform_keys: set[tuple[str, str, str]] = set()
    source_cache: dict[str, str] = {}
    for index, transform in enumerate(transforms):
        label = f"font proof source_transforms[{index}]"
        if not isinstance(transform, dict):
            raise ValueError(f"{label} must be an object")
        _require_exact_keys(
            transform,
            frozenset({"path", "original", "replacement"}),
            label=label,
        )
        raw_path = _require_string(transform, "path", label=label)
        relative = _safe_relative_path(raw_path, label=f"{label} path")
        original = _require_string(transform, "original", label=label)
        replacement = _require_string(transform, "replacement", label=label)
        if original == replacement:
            raise ValueError(f"{label} original and replacement must differ")
        transform_key = (raw_path, original, replacement)
        if transform_key in transform_keys:
            raise ValueError(f"{label} duplicates another source transform")
        transform_keys.add(transform_key)
        if raw_path not in source_cache:
            raw_source = _read_repository_file(root, relative, label=label)
            try:
                source_cache[raw_path] = raw_source.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(f"{label} source must be UTF-8") from exc
        occurrence_count = source_cache[raw_path].count(original)
        if occurrence_count != 1:
            raise ValueError(
                f"{label} original must occur exactly once in its source; "
                f"found {occurrence_count}"
            )
        parsed_transforms.append(
            SourceTransform(raw_path, original, replacement)
        )

    profiles = _parse_profiles(config.get("profiles"))
    if profile_id not in profiles:
        raise ValueError(f"unknown font proof profile: {profile_id}")

    lock_relative = _safe_relative_path(
        _require_string(config, "font_lock", label="font proof config"),
        label="font proof font_lock",
    )
    lock_hash, resolved_fonts = _load_lock(root, lock_relative, profiles)
    profile = profiles[profile_id]
    if profile.font_source == TEXLIVE_DEJAVU:
        regular_font_path = None
        bold_font_path = None
    else:
        regular_font_path, bold_font_path = resolved_fonts[profile.font_source]

    return ProofContext(
        config_path=root / Path(config_relative),
        config_hash=_sha256(config_raw),
        lock_hash=lock_hash,
        proof_set=proof_set,
        proof_identifier=proof_identifier,
        proof_label=proof_label,
        base_manifest=base_manifest,
        base_manifest_hash=actual_manifest_hash,
        base_toolchain_lock=root / Path(toolchain_relative),
        base_toolchain_lock_hash=actual_toolchain_hash,
        baseline_commit=baseline_commit,
        baseline_document_version=baseline_document_version,
        baseline_filename=baseline_filename,
        baseline_sha256=baseline_sha256,
        supplement=root / Path(supplement_relative),
        structure_count_deltas=dict(deltas),
        required_pdf_text=required_pdf_text,
        required_ocr_text=required_ocr_text,
        fontspec_ligatures=fontspec_ligatures,
        raw_features=raw_features,
        ligature_denylist=(*fontspec_ligatures, *raw_features),
        source_transforms=tuple(parsed_transforms),
        profile=profile,
        regular_font_path=regular_font_path,
        bold_font_path=bold_font_path,
    )


def derive_proof_trailer_id(
    base_manifest: dict[str, Any],
    proof_set: str,
    profile_id: str,
) -> str:
    """Derive a stable 128-bit trailer identifier for one review proof."""
    base_id = base_manifest.get("pdf_trailer_id")
    if not isinstance(base_id, str) or re.fullmatch(r"[0-9a-f]{32}", base_id) is None:
        raise ValueError("base manifest pdf_trailer_id is invalid")
    if SAFE_ID.fullmatch(proof_set) is None:
        raise ValueError("font proof proof_set is unsafe")
    if SAFE_PROFILE_ID.fullmatch(profile_id) is None:
        raise ValueError("font proof profile ID is unsafe")
    seed = (
        f"utc-hpc-guide:font-proof:{base_id}:{proof_set}:{profile_id}"
    ).encode("ascii")
    return hashlib.sha256(seed).hexdigest()[:32]


def _replace_exact_phrase(
    phrases: list[str],
    old: str,
    new: str,
    *,
    label: str,
) -> list[str]:
    if phrases.count(old) != 1:
        raise ValueError(f"{label} must contain the base cover phrase exactly once")
    return [new if phrase == old else phrase for phrase in phrases]


def _append_unique(target: list[str], additions: tuple[str, ...]) -> None:
    for phrase in additions:
        if phrase not in target:
            target.append(phrase)


def effective_manifest(
    base: dict[str, Any],
    context: ProofContext,
) -> dict[str, Any]:
    """Return the proof-specific manifest without mutating the release base."""
    if base != context.base_manifest:
        raise ValueError("effective manifest base must match the proof context")
    manifest = copy.deepcopy(base)
    if manifest.get("release_status") != "candidate":
        raise ValueError("font proofs require a candidate base manifest")
    cover_phrase = f"Release candidate for v{manifest['release_target']}"

    manifest["required_pdf_text"] = _replace_exact_phrase(
        list(manifest["required_pdf_text"]),
        cover_phrase,
        context.proof_label,
        label="base required_pdf_text",
    )
    manifest["required_ocr_text"] = _replace_exact_phrase(
        list(manifest["required_ocr_text"]),
        cover_phrase,
        context.proof_label,
        label="base required_ocr_text",
    )
    page_one = list(manifest["required_page_ocr_text"]["1"])
    manifest["required_page_ocr_text"]["1"] = _replace_exact_phrase(
        page_one,
        cover_phrase,
        context.proof_label,
        label="base required_page_ocr_text page 1",
    )

    shared_identity = (context.proof_identifier, context.profile.label)
    _append_unique(
        manifest["required_pdf_text"],
        (*shared_identity, *context.required_pdf_text),
    )
    _append_unique(
        manifest["required_ocr_text"],
        (*shared_identity, *context.required_ocr_text),
    )
    _append_unique(
        manifest["required_page_ocr_text"]["1"],
        shared_identity,
    )

    for role, delta in context.structure_count_deltas.items():
        if role not in manifest["expected_structure_counts"]:
            raise ValueError(f"base manifest is missing structure role {role}")
        manifest["expected_structure_counts"][role] += delta

    manifest["output_filename"] = context.profile.output_filename
    manifest["pdf_trailer_id"] = derive_proof_trailer_id(
        base,
        context.proof_set,
        context.profile.id,
    )
    manifest["font_proof"] = {
        "proof_set": context.proof_set,
        "proof_identifier": context.proof_identifier,
        "proof_label": context.proof_label,
        "profile_id": context.profile.id,
        "profile_label": context.profile.label,
    }
    return manifest


def proof_output_path(root: Path, context: ProofContext) -> Path:
    """Return the repository-local output path for a validated profile."""
    filename = context.profile.output_filename
    if SAFE_FILENAME.fullmatch(filename) is None:
        raise ValueError("font proof output filename is unsafe")
    return root / "dist" / filename
