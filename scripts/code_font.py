"""Load and verify the one canonical fenced-code font contract."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


SOURCE_ID = "fira-code-6.2"
LOCK_PATH = PurePosixPath("pdf/toolchain.lock.json")
REQUIRED_LIGATURES = (
    "RequiredOff",
    "CommonOff",
    "ContextualOff",
    "DiscretionaryOff",
    "HistoricOff",
    "TeXOff",
)
REQUIRED_RAW_FEATURES = (
    "-calt",
    "-liga",
    "-clig",
    "-dlig",
    "-hlig",
    "-rlig",
    "-tlig",
)
HEX_40 = re.compile(r"[0-9a-f]{40}")
HEX_64 = re.compile(r"[0-9a-f]{64}")
SAFE_FONT_TOKEN = re.compile(r"[A-Za-z0-9*][A-Za-z0-9*_.-]{0,126}")
SAFE_POSTSCRIPT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,126}")


@dataclass(frozen=True)
class LockedFace:
    """One hash- and name-verified static font face."""

    path: Path
    relative_path: str
    archive_member: str
    size: int
    sha256: str
    postscript_name: str


@dataclass(frozen=True)
class LockedCodeFont:
    """The selected canonical font, its layout, and upstream provenance."""

    source_id: str
    font_stem: str
    upright_pattern: str
    bold_pattern: str
    font_size_pt: float
    leading_pt: float
    extraction_pitch: float
    prose_family: str
    inline_code_family: str
    ligatures: tuple[str, ...]
    raw_features: tuple[str, ...]
    regular: LockedFace
    bold: LockedFace
    source: dict[str, Any]


def _duplicate_rejecting_object(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key is not allowed: {key}")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _safe_relative_path(raw: str, *, label: str) -> PurePosixPath:
    if (
        not isinstance(raw, str)
        or not raw
        or raw != raw.strip()
        or "\\" in raw
        or "\x00" in raw
    ):
        raise ValueError(f"{label} must be a normalized repository-relative path")
    path = PurePosixPath(raw)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != raw
    ):
        raise ValueError(f"{label} must stay inside the repository: {raw}")
    return path


def _read_repository_file(
    root: Path,
    relative: PurePosixPath,
    *,
    label: str,
) -> bytes:
    """Read one regular file through a retained no-follow descriptor chain."""
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
            f"{label} must be a regular file without symbolic links: {relative}"
        ) from exc
    finally:
        if final_descriptor is not None:
            os.close(final_descriptor)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _exact_keys(
    value: dict[str, Any],
    expected: set[str],
    *,
    label: str,
) -> None:
    actual = set(value)
    if actual != expected:
        raise ValueError(
            f"{label} keys do not match the contract "
            f"(missing={sorted(expected - actual)}, extra={sorted(actual - expected)})"
        )


def _string(value: dict[str, Any], key: str, *, label: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip() or "\x00" in result:
        raise ValueError(f"{label} {key} must be a nonempty string")
    return result


def _positive_integer(value: dict[str, Any], key: str, *, label: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 1:
        raise ValueError(f"{label} {key} must be a positive integer")
    return result


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _https(value: str, *, label: str) -> str:
    if not value.startswith("https://") or any(char.isspace() for char in value):
        raise ValueError(f"{label} must be a whitespace-free HTTPS URL")
    return value


def _postscript_names(raw: bytes, *, label: str) -> set[str]:
    """Read name ID 6 through the bounded OpenType `name` table."""
    try:
        if len(raw) < 12:
            raise ValueError
        table_count = struct.unpack_from(">H", raw, 4)[0]
        directory_end = 12 + table_count * 16
        if table_count < 1 or directory_end > len(raw):
            raise ValueError
        name_entries: list[tuple[int, int]] = []
        for index in range(table_count):
            record_offset = 12 + index * 16
            tag, _checksum, offset, length = struct.unpack_from(
                ">4sIII", raw, record_offset
            )
            if offset > len(raw) or length > len(raw) - offset:
                raise ValueError
            if tag == b"name":
                name_entries.append((offset, length))
        if len(name_entries) != 1:
            raise ValueError
        table_offset, table_length = name_entries[0]
        if table_length < 6:
            raise ValueError
        version, name_count, storage_offset = struct.unpack_from(
            ">HHH", raw, table_offset
        )
        records_end = 6 + name_count * 12
        if version not in {0, 1} or records_end > table_length:
            raise ValueError
        if storage_offset < records_end or storage_offset > table_length:
            raise ValueError

        names: set[str] = set()
        for index in range(name_count):
            record_offset = table_offset + 6 + index * 12
            platform, _encoding, _language, name_id, length, offset = (
                struct.unpack_from(">HHHHHH", raw, record_offset)
            )
            if name_id != 6 or platform not in {0, 1, 3}:
                continue
            relative_start = storage_offset + offset
            if relative_start > table_length or length > table_length - relative_start:
                raise ValueError
            start = table_offset + relative_start
            encoded = raw[start : start + length]
            codec = "mac_roman" if platform == 1 else "utf-16-be"
            value = encoded.decode(codec)
            if not value or "\x00" in value:
                raise ValueError
            names.add(value)
    except (struct.error, UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"{label} is not a readable OpenType font") from exc
    if not names:
        raise ValueError(f"{label} has no PostScript name")
    return names


def _load_face(
    root: Path,
    entry: Any,
    *,
    label: str,
    expected_path: str,
    expected_member: str,
) -> LockedFace:
    if not isinstance(entry, dict):
        raise ValueError(f"{label} must be an object")
    _exact_keys(
        entry,
        {"path", "archive_member", "size", "sha256", "postscript_name"},
        label=label,
    )
    relative = _safe_relative_path(_string(entry, "path", label=label), label=label)
    if relative.as_posix() != expected_path:
        raise ValueError(f"{label} path must be {expected_path}")
    member = _string(entry, "archive_member", label=label)
    if member != expected_member:
        raise ValueError(f"{label} archive member must be {expected_member}")
    size = _positive_integer(entry, "size", label=label)
    digest = _string(entry, "sha256", label=label)
    if HEX_64.fullmatch(digest) is None:
        raise ValueError(f"{label} sha256 must be 64 lowercase hex characters")
    postscript = _string(entry, "postscript_name", label=label)
    if SAFE_POSTSCRIPT.fullmatch(postscript) is None:
        raise ValueError(f"{label} postscript_name is unsafe")
    raw = _read_repository_file(root, relative, label=label)
    if len(raw) != size:
        raise ValueError(f"{label} size mismatch: expected {size}, got {len(raw)}")
    if _sha256(raw) != digest:
        raise ValueError(f"{label} SHA-256 mismatch")
    names = _postscript_names(raw, label=label)
    if names != {postscript}:
        raise ValueError(
            f"{label} PostScript name mismatch: {sorted(names)} != {postscript!r}"
        )
    return LockedFace(
        path=root / relative,
        relative_path=relative.as_posix(),
        archive_member=member,
        size=size,
        sha256=digest,
        postscript_name=postscript,
    )


def load_code_font(
    root: Path,
    lock_path: PurePosixPath = LOCK_PATH,
) -> LockedCodeFont:
    """Load the selected Fira configuration and verify every local byte."""
    root = root.resolve()
    lock_raw = _read_repository_file(root, lock_path, label="PDF toolchain lock")
    try:
        lock = json.loads(
            lock_raw.decode("utf-8"),
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"PDF toolchain lock is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(lock, dict):
        raise ValueError("PDF toolchain lock must be an object")

    config = lock.get("code_font")
    if not isinstance(config, dict):
        raise ValueError("PDF toolchain lock code_font must be an object")
    _exact_keys(
        config,
        {
            "source",
            "font_stem",
            "upright_pattern",
            "bold_pattern",
            "font_size_pt",
            "leading_pt",
            "extraction_pitch",
            "prose_family",
            "inline_code_family",
            "fontspec_ligatures",
            "raw_features",
        },
        label="code_font",
    )
    source_id = _string(config, "source", label="code_font")
    if source_id != SOURCE_ID:
        raise ValueError(f"canonical code font source must be {SOURCE_ID}")
    for key in ("font_stem", "upright_pattern", "bold_pattern"):
        if SAFE_FONT_TOKEN.fullmatch(_string(config, key, label="code_font")) is None:
            raise ValueError(f"code_font {key} is unsafe")
    for key, expected in (
        ("font_size_pt", 9.1),
        ("leading_pt", 11.5),
        ("extraction_pitch", 5.5),
    ):
        observed = config.get(key)
        if (
            not isinstance(observed, (int, float))
            or isinstance(observed, bool)
            or not math.isfinite(float(observed))
            or float(observed) != expected
        ):
            raise ValueError(f"code_font {key} must be exactly {expected:g}")
    if _string(config, "prose_family", label="code_font") != "NotoSans":
        raise ValueError("canonical prose family must remain NotoSans")
    if (
        _string(config, "inline_code_family", label="code_font")
        != "DejaVuSansMono"
    ):
        raise ValueError("canonical inline-code family must remain DejaVuSansMono")
    ligatures = config.get("fontspec_ligatures")
    raw_features = config.get("raw_features")
    if (
        tuple(ligatures) if isinstance(ligatures, list) else ()
    ) != REQUIRED_LIGATURES:
        raise ValueError("code_font fontspec_ligatures must match the full denylist")
    if (
        tuple(raw_features) if isinstance(raw_features, list) else ()
    ) != REQUIRED_RAW_FEATURES:
        raise ValueError("code_font raw_features must match the full denylist")

    sources = lock.get("font_sources")
    if not isinstance(sources, dict) or set(sources) != {SOURCE_ID}:
        raise ValueError("font_sources must contain only the selected Fira source")
    source = sources[SOURCE_ID]
    if not isinstance(source, dict):
        raise ValueError(f"font source {SOURCE_ID} must be an object")
    _exact_keys(
        source,
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
        },
        label=f"font source {SOURCE_ID}",
    )
    for key in ("project", "release", "release_tag"):
        _string(source, key, label=SOURCE_ID)
    for key in ("project_url", "release_url", "archive_url"):
        _https(_string(source, key, label=SOURCE_ID), label=f"{SOURCE_ID} {key}")
    if HEX_40.fullmatch(_string(source, "release_commit", label=SOURCE_ID)) is None:
        raise ValueError(f"{SOURCE_ID} release_commit must be 40 lowercase hex characters")
    _positive_integer(source, "archive_size", label=SOURCE_ID)
    if HEX_64.fullmatch(_string(source, "archive_sha256", label=SOURCE_ID)) is None:
        raise ValueError(f"{SOURCE_ID} archive_sha256 must be 64 lowercase hex characters")

    license_entry = source.get("license_file")
    if not isinstance(license_entry, dict):
        raise ValueError(f"{SOURCE_ID} license_file must be an object")
    _exact_keys(
        license_entry,
        {
            "path",
            "upstream_url",
            "upstream_size",
            "upstream_sha256",
            "normalization",
            "stripped_trailing_spaces",
            "size",
            "sha256",
        },
        label=f"{SOURCE_ID} license_file",
    )
    license_path = _safe_relative_path(
        _string(license_entry, "path", label=SOURCE_ID),
        label=f"{SOURCE_ID} license_file",
    )
    if license_path.as_posix() != f"pdf/fonts/{SOURCE_ID}/LICENSE.txt":
        raise ValueError(f"{SOURCE_ID} license path is not canonical")
    _https(
        _string(license_entry, "upstream_url", label=SOURCE_ID),
        label=f"{SOURCE_ID} license upstream_url",
    )
    license_raw = _read_repository_file(root, license_path, label="Fira Code license")
    license_size = _positive_integer(license_entry, "size", label=SOURCE_ID)
    license_hash = _string(license_entry, "sha256", label=SOURCE_ID)
    if len(license_raw) != license_size or _sha256(license_raw) != license_hash:
        raise ValueError("Fira Code license size or SHA-256 mismatch")
    if (
        license_entry.get("normalization") != "none"
        or license_entry.get("stripped_trailing_spaces") != {}
        or license_entry.get("upstream_size") != license_size
        or license_entry.get("upstream_sha256") != license_hash
    ):
        raise ValueError("Fira Code license must preserve the exact upstream bytes")

    regular = _load_face(
        root,
        source.get("regular"),
        label="Fira Code Regular",
        expected_path=f"pdf/fonts/{SOURCE_ID}/FiraCode-Regular.ttf",
        expected_member="ttf/FiraCode-Regular.ttf",
    )
    bold = _load_face(
        root,
        source.get("bold"),
        label="Fira Code Bold",
        expected_path=f"pdf/fonts/{SOURCE_ID}/FiraCode-Bold.ttf",
        expected_member="ttf/FiraCode-Bold.ttf",
    )
    return LockedCodeFont(
        source_id=source_id,
        font_stem=_string(config, "font_stem", label="code_font"),
        upright_pattern=_string(config, "upright_pattern", label="code_font"),
        bold_pattern=_string(config, "bold_pattern", label="code_font"),
        font_size_pt=float(config["font_size_pt"]),
        leading_pt=float(config["leading_pt"]),
        extraction_pitch=float(config["extraction_pitch"]),
        prose_family="NotoSans",
        inline_code_family="DejaVuSansMono",
        ligatures=REQUIRED_LIGATURES,
        raw_features=REQUIRED_RAW_FEATURES,
        regular=regular,
        bold=bold,
        source=source,
    )


def fontspec_definition(font: LockedCodeFont, *, command: str = "GuideCodeFont") -> str:
    """Return a fail-closed fontspec family using only the vendored static faces."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", command):
        raise ValueError("fontspec command name is unsafe")
    if font.regular.path.parent != font.bold.path.parent:
        raise ValueError("canonical Fira faces must share one directory")
    directory = font.regular.path.parent.as_posix() + "/"
    if any(character in directory for character in "{},\n\r"):
        raise ValueError("canonical Fira path contains a TeX-unsafe character")
    options = [
        f"Path={directory}",
        "Extension=.ttf",
        f"UprightFont={font.upright_pattern}",
        f"BoldFont={font.bold_pattern}",
        *(f"Ligatures={feature}" for feature in font.ligatures),
        *(f"RawFeature={feature}" for feature in font.raw_features),
    ]
    return (
        f"\\newfontfamily\\{command}[\n  "
        + ",\n  ".join(options)
        + f"\n]{{{font.font_stem}}}"
    )
