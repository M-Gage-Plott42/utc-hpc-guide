#!/usr/bin/env python3
"""Check machine-verifiable PDF accessibility and PDF/UA-2 invariants.

This checker is deliberately narrower than a human accessibility review. It
checks the PDF catalog and logical structure with qpdf, checks summary metadata
with pdfinfo, and requires one compliant veraPDF PDF/UA-2 validation job.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

try:
    from .pdf_manifest import load_manifest, output_path
except ImportError:
    from pdf_manifest import load_manifest, output_path


OBJECT_REFERENCE = re.compile(r"^(\d+)\s+(\d+)\s+R$")
PDFINFO_DESTINATION = re.compile(
    r'^\s*(?P<page>\d+)\s+\[[^\]]+\]\s+"(?P<name>[^"]+)"\s*$'
)
PDFUA_ID_NAMESPACE = "http://www.aiim.org/pdfua/ns/id/"
VERAPDF_PROFILE = "ua2"

REQUIRED_STRUCTURE_TAGS = {
    "L",
    "Table",
    "TH",
    "TD",
    "Link",
    "Figure",
    "Code",
}
HEADING_TAGS = {"H", "H1", "H2", "H3", "H4", "H5", "H6"}

DANGEROUS_DICTIONARY_KEYS = {
    "/AcroForm": "interactive form",
    "/AF": "associated-file attachment",
    "/EF": "embedded file",
    "/EmbeddedFiles": "embedded-files name tree",
    "/JavaScript": "JavaScript name tree",
    "/JS": "JavaScript action",
}
DANGEROUS_NAME_VALUES = {
    "/EmbeddedFile": "embedded file",
    "/FileAttachment": "file-attachment annotation",
    "/Filespec": "file specification",
    "/ImportData": "active ImportData action",
    "/JavaScript": "JavaScript action",
    "/Launch": "active Launch action",
    "/Movie": "active Movie action",
    "/Rendition": "active Rendition action",
    "/RichMedia": "active RichMedia content",
    "/Sound": "active Sound action",
    "/SubmitForm": "active SubmitForm action",
}


@dataclass(frozen=True)
class StructureSummary:
    tags: Counter[str]
    figure_alt_text: tuple[str, ...]


@dataclass(frozen=True)
class VeraPdfSummary:
    total_jobs: int
    compliant_jobs: int
    profile: str


def run_text(
    command: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        capture_output=True,
        text=True,
    )


def tool(name: str) -> str:
    result = shutil.which(name)
    if not result:
        raise RuntimeError(f"required PDF accessibility tool is unavailable: {name}")
    return result


def parse_info(text: str) -> dict[str, str]:
    info: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info


def validate_manifest(manifest: dict[str, Any]) -> tuple[str, ...]:
    if manifest.get("schema_version") != 2:
        raise ValueError("PDF manifest schema_version must be 2")
    for key in ("title", "author"):
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"PDF manifest {key} must be a nonempty string")
    if manifest.get("language") != "en-US":
        raise ValueError("PDF manifest language must be en-US")
    if manifest.get("pdf_standard") != "ua-2":
        raise ValueError("PDF manifest pdf_standard must be ua-2")

    alternatives = manifest.get("expected_figure_alt_text")
    if (
        not isinstance(alternatives, list)
        or len(alternatives) != 3
        or not all(isinstance(item, str) for item in alternatives)
    ):
        raise ValueError(
            "expected_figure_alt_text must contain exactly three strings"
        )

    normalized: list[str] = []
    for alternative in alternatives:
        text = alternative.strip()
        words = re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)
        if len(text) < 20 or len(words) < 3:
            raise ValueError(
                "each expected figure alternative must be a meaningful "
                "description of at least three words"
            )
        normalized.append(text)
    if len(set(normalized)) != 3:
        raise ValueError("expected figure alternatives must be distinct")
    return tuple(normalized)


def validate_pdfinfo(info: dict[str, str], manifest: dict[str, Any]) -> None:
    if info.get("Title") != manifest["title"]:
        raise RuntimeError(f"unexpected PDF title: {info.get('Title')}")
    if info.get("Author") != manifest["author"]:
        raise RuntimeError(f"unexpected PDF author: {info.get('Author')}")
    if info.get("Tagged", "").casefold() != "yes":
        raise RuntimeError("pdfinfo must report Tagged: yes")
    if info.get("PDF version") != "2.0":
        raise RuntimeError(
            f"PDF must use PDF 2.0; pdfinfo reported {info.get('PDF version')}"
        )
    if info.get("Encrypted", "").casefold() != "no":
        raise RuntimeError("PDF must not be encrypted")
    if info.get("Form", "").casefold() != "none":
        raise RuntimeError("PDF must not contain an interactive form")
    if info.get("JavaScript", "").casefold() != "no":
        raise RuntimeError("PDF must not contain JavaScript")
    if info.get("Metadata Stream", "").casefold() != "yes":
        raise RuntimeError("PDF must contain an XMP metadata stream")


def qpdf_objects(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    qpdf = document.get("qpdf")
    if not isinstance(qpdf, list) or len(qpdf) < 2:
        raise RuntimeError("qpdf JSON is missing its object map")
    objects: dict[str, dict[str, Any]] = {}
    for section in qpdf[1:]:
        if not isinstance(section, dict):
            raise RuntimeError("qpdf JSON contains a malformed object-map section")
        for key, payload in section.items():
            if key == "trailer":
                continue
            if not key.startswith("obj:") or not isinstance(payload, dict):
                raise RuntimeError(f"qpdf JSON contains a malformed object: {key}")
            objects[key.removeprefix("obj:")] = payload
    if not objects:
        raise RuntimeError("qpdf JSON contains no PDF objects")
    return objects


def qpdf_header(document: dict[str, Any]) -> dict[str, Any]:
    qpdf = document.get("qpdf")
    if (
        not isinstance(qpdf, list)
        or not qpdf
        or not isinstance(qpdf[0], dict)
    ):
        raise RuntimeError("qpdf JSON is missing its document header")
    return qpdf[0]


def object_value(payload: dict[str, Any]) -> Any:
    if "value" in payload:
        return payload["value"]
    stream = payload.get("stream")
    if isinstance(stream, dict):
        return stream.get("dict")
    return None


def resolve_reference(
    value: Any,
    objects: dict[str, dict[str, Any]],
    *,
    description: str,
) -> Any:
    if isinstance(value, str) and OBJECT_REFERENCE.fullmatch(value):
        payload = objects.get(value)
        if payload is None:
            raise RuntimeError(f"{description} references a missing object: {value}")
        return object_value(payload)
    return value


def qpdf_text(value: Any, *, description: str) -> str:
    if not isinstance(value, str):
        raise RuntimeError(f"{description} must be a PDF text string")
    if value.startswith("u:"):
        return value[2:]
    if value.startswith("b:"):
        try:
            return base64.b64decode(value[2:], validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise RuntimeError(f"{description} is not valid Unicode text") from exc
    return value


def find_catalog(objects: dict[str, dict[str, Any]]) -> dict[str, Any]:
    catalogs = []
    for payload in objects.values():
        value = object_value(payload)
        if isinstance(value, dict) and value.get("/Type") == "/Catalog":
            catalogs.append(value)
    if len(catalogs) != 1:
        raise RuntimeError(f"expected exactly one PDF catalog; found {len(catalogs)}")
    return catalogs[0]


def validate_page_contract(
    catalog: dict[str, Any],
    objects: dict[str, dict[str, Any]],
) -> tuple[int, int]:
    pages: list[dict[str, Any]] = []
    for payload in objects.values():
        value = object_value(payload)
        if isinstance(value, dict) and value.get("/Type") == "/Page":
            pages.append(value)
    if len(pages) < 3:
        raise RuntimeError("tagged guide must contain cover, contents, and body pages")

    structure_parents: list[int] = []
    for page in pages:
        if page.get("/Tabs") != "/S":
            raise RuntimeError("every PDF page must use structure tab order /Tabs /S")
        parent = page.get("/StructParents")
        if not isinstance(parent, int) or isinstance(parent, bool):
            raise RuntimeError("every PDF page must have an integer StructParents value")
        structure_parents.append(parent)
    if sorted(structure_parents) != list(range(len(pages))):
        raise RuntimeError(
            "PDF page StructParents values must be unique and contiguous from zero"
        )

    viewer_preferences = resolve_reference(
        catalog.get("/ViewerPreferences"),
        objects,
        description="catalog ViewerPreferences",
    )
    if (
        not isinstance(viewer_preferences, dict)
        or viewer_preferences.get("/DisplayDocTitle") is not True
    ):
        raise RuntimeError("catalog ViewerPreferences must enable DisplayDocTitle")

    page_labels = resolve_reference(
        catalog.get("/PageLabels"),
        objects,
        description="catalog PageLabels",
    )
    if not isinstance(page_labels, dict):
        raise RuntimeError("catalog must contain a PageLabels number tree")
    numbers = resolve_reference(
        page_labels.get("/Nums"),
        objects,
        description="PageLabels Nums",
    )
    if not isinstance(numbers, list) or len(numbers) != 6:
        raise RuntimeError(
            "PageLabels must define exactly Cover, Roman contents, and Arabic body"
        )
    indices = numbers[0::2]
    styles = numbers[1::2]
    if (
        any(not isinstance(index, int) for index in indices)
        or indices[0] != 0
        or indices[1] != 1
        or not 1 < indices[2] < len(pages)
        or indices != sorted(set(indices))
        or any(not isinstance(style, dict) for style in styles)
    ):
        raise RuntimeError(
            "PageLabels must progress from physical cover to contents to body"
        )
    cover = qpdf_text(styles[0].get("/P"), description="cover page label")
    if cover != "Cover" or set(styles[0]) != {"/P"}:
        raise RuntimeError("the first physical page must have the unique label Cover")
    if (
        set(styles[1]) not in ({"/S"}, {"/S", "/St"})
        or styles[1].get("/S") != "/r"
        or isinstance(styles[1].get("/St", 1), bool)
        or styles[1].get("/St", 1) != 1
    ):
        raise RuntimeError("contents pages must start with lowercase Roman label i")
    if (
        set(styles[2]) not in ({"/S"}, {"/S", "/St"})
        or styles[2].get("/S") != "/D"
        or isinstance(styles[2].get("/St", 1), bool)
        or styles[2].get("/St", 1) != 1
    ):
        raise RuntimeError("body pages must restart with Arabic label 1")
    return indices[1] + 1, indices[2] + 1


def validate_named_page_destinations(
    text: str,
    *,
    contents_page: int,
    body_page: int,
) -> None:
    destinations: dict[str, list[int]] = {}
    for line in text.splitlines():
        match = PDFINFO_DESTINATION.fullmatch(line)
        if match is None:
            continue
        destinations.setdefault(match.group("name"), []).append(
            int(match.group("page"))
        )

    for name, expected_page in (
        ("page.i", contents_page),
        ("page.1", body_page),
    ):
        pages = destinations.get(name, [])
        if pages != [expected_page]:
            raise RuntimeError(
                f'named destination "{name}" must resolve exactly once to '
                f"physical page {expected_page}; found {pages}"
            )


def iter_nodes(node: Any) -> Iterator[tuple[str | None, Any]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield key, value
            yield from iter_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield None, value
            yield from iter_nodes(value)


def reject_active_content(objects: dict[str, dict[str, Any]]) -> None:
    for object_reference, payload in objects.items():
        value = object_value(payload)
        for key, item in iter_nodes(value):
            if key in DANGEROUS_DICTIONARY_KEYS:
                raise RuntimeError(
                    f"PDF contains {DANGEROUS_DICTIONARY_KEYS[key]} "
                    f"in object {object_reference}"
                )
            if isinstance(item, str) and item in DANGEROUS_NAME_VALUES:
                raise RuntimeError(
                    f"PDF contains {DANGEROUS_NAME_VALUES[item]} "
                    f"in object {object_reference}"
                )


def role_map(
    structure_root: dict[str, Any],
    objects: dict[str, dict[str, Any]],
) -> dict[str, str]:
    raw = resolve_reference(
        structure_root.get("/RoleMap", {}),
        objects,
        description="StructTreeRoot RoleMap",
    )
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise RuntimeError("StructTreeRoot RoleMap must be a dictionary")
    result: dict[str, str] = {}
    for source, target in raw.items():
        if not (
            isinstance(source, str)
            and source.startswith("/")
            and isinstance(target, str)
            and target.startswith("/")
        ):
            raise RuntimeError("StructTreeRoot RoleMap contains an invalid mapping")
        result[source[1:]] = target[1:]
    return result


def mapped_role(role: str, mappings: dict[str, str]) -> str:
    seen: set[str] = set()
    while role in mappings:
        if role in seen:
            raise RuntimeError("StructTreeRoot RoleMap contains a cycle")
        seen.add(role)
        role = mappings[role]
    return role


def collect_structure(
    structure_root: dict[str, Any],
    objects: dict[str, dict[str, Any]],
) -> StructureSummary:
    mappings = role_map(structure_root, objects)
    tags: Counter[str] = Counter()
    alternatives: list[str] = []
    visited_references: set[str] = set()

    def visit(kid: Any) -> None:
        if kid is None:
            return
        if isinstance(kid, list):
            for entry in kid:
                visit(entry)
            return
        if isinstance(kid, int):
            return
        if isinstance(kid, str) and OBJECT_REFERENCE.fullmatch(kid):
            if kid in visited_references:
                return
            visited_references.add(kid)
            payload = objects.get(kid)
            if payload is None:
                raise RuntimeError(
                    f"logical structure references a missing object: {kid}"
                )
            kid = object_value(payload)
        if not isinstance(kid, dict):
            raise RuntimeError("logical structure contains an unsupported kid")

        raw_role = kid.get("/S")
        if raw_role is not None:
            if not isinstance(raw_role, str) or not raw_role.startswith("/"):
                raise RuntimeError("logical structure contains an invalid role")
            role = mapped_role(raw_role[1:], mappings)
            tags[role] += 1
            if role == "Figure":
                if "/Alt" not in kid:
                    raise RuntimeError("Figure structure element is missing Alt text")
                alternative = qpdf_text(
                    kid["/Alt"],
                    description="Figure Alt text",
                ).strip()
                if not alternative:
                    raise RuntimeError("Figure structure element has empty Alt text")
                alternatives.append(alternative)

        if "/K" in kid:
            visit(kid["/K"])

    if "/K" not in structure_root:
        raise RuntimeError("StructTreeRoot is missing its K entry")
    visit(structure_root["/K"])
    return StructureSummary(tags=tags, figure_alt_text=tuple(alternatives))


def validate_pdfua_xmp(xmp: bytes) -> None:
    try:
        root = ET.fromstring(xmp)
    except ET.ParseError as exc:
        raise RuntimeError(f"PDF XMP metadata is malformed: {exc}") from exc

    for element in root.iter():
        if (
            element.tag == f"{{{PDFUA_ID_NAMESPACE}}}part"
            and (element.text or "").strip() == "2"
        ):
            return
        if element.attrib.get(f"{{{PDFUA_ID_NAMESPACE}}}part", "").strip() == "2":
            return
    raise RuntimeError("XMP metadata is missing the PDF/UA-2 part identifier")


def validate_qpdf_document(
    document: dict[str, Any],
    manifest: dict[str, Any],
    xmp: bytes,
) -> StructureSummary:
    alternatives = validate_manifest(manifest)
    if document.get("version") != 2:
        raise RuntimeError("qpdf JSON version must be 2")
    header = qpdf_header(document)
    if header.get("jsonversion") != 2:
        raise RuntimeError("qpdf document JSON version must be 2")
    if header.get("pdfversion") != "2.0":
        raise RuntimeError(
            f"qpdf must report PDF 2.0; found {header.get('pdfversion')}"
        )

    encryption = document.get("encrypt")
    if not isinstance(encryption, dict) or encryption.get("encrypted") is not False:
        raise RuntimeError("qpdf must report that the PDF is not encrypted")
    acroform = document.get("acroform")
    if (
        not isinstance(acroform, dict)
        or acroform.get("hasacroform") is not False
        or acroform.get("fields") != []
    ):
        raise RuntimeError("qpdf must report no AcroForm and no form fields")
    attachments = document.get("attachments")
    if not isinstance(attachments, dict) or attachments:
        raise RuntimeError("qpdf must report no attachments")

    objects = qpdf_objects(document)
    catalog = find_catalog(objects)
    validate_page_contract(catalog, objects)
    language = qpdf_text(
        catalog.get("/Lang"),
        description="catalog Lang",
    )
    if language != manifest["language"]:
        raise RuntimeError(f"catalog Lang must be en-US; found {language}")

    mark_info = resolve_reference(
        catalog.get("/MarkInfo"),
        objects,
        description="catalog MarkInfo",
    )
    if not isinstance(mark_info, dict) or mark_info.get("/Marked") is not True:
        raise RuntimeError("catalog MarkInfo must have Marked true")

    structure_root = resolve_reference(
        catalog.get("/StructTreeRoot"),
        objects,
        description="catalog StructTreeRoot",
    )
    if (
        not isinstance(structure_root, dict)
        or structure_root.get("/Type") != "/StructTreeRoot"
    ):
        raise RuntimeError("catalog must reference a StructTreeRoot dictionary")
    metadata = catalog.get("/Metadata")
    if not isinstance(metadata, str) or not OBJECT_REFERENCE.fullmatch(metadata):
        raise RuntimeError("catalog must reference an XMP Metadata stream")

    reject_active_content(objects)
    summary = collect_structure(structure_root, objects)

    missing = sorted(REQUIRED_STRUCTURE_TAGS - set(summary.tags))
    has_heading = bool(set(summary.tags) & HEADING_TAGS)
    if missing or not has_heading:
        requirements = missing
        if not has_heading:
            requirements.append("heading (H/H1/H2)")
        raise RuntimeError(
            "logical structure is missing required roles: "
            + ", ".join(requirements)
        )
    if not (
        summary.tags.get("H", 0)
        or (summary.tags.get("H1", 0) and summary.tags.get("H2", 0))
    ):
        raise RuntimeError(
            "logical structure must contain H1 and H2 roles or a generic H role"
        )
    if summary.tags.get("Caption", 0):
        raise RuntimeError(
            "logical structure must not contain detached Caption roles; "
            "screenshots use source-position figures with contextual labels"
        )
    if summary.figure_alt_text != alternatives:
        raise RuntimeError(
            "Figure Alt text must exactly match the three manifest alternatives "
            "in source order"
        )

    expected_counts = manifest.get("expected_structure_counts")
    if expected_counts is not None:
        if not isinstance(expected_counts, dict):
            raise ValueError("expected_structure_counts must be an object")
        mismatches = {
            role: (summary.tags.get(role, 0), expected)
            for role, expected in expected_counts.items()
            if summary.tags.get(role, 0) != expected
        }
        if mismatches:
            details = ", ".join(
                f"{role}={actual} (expected {expected})"
                for role, (actual, expected) in sorted(mismatches.items())
            )
            raise RuntimeError(f"logical structure role counts changed: {details}")
    if summary.tags.get("Artifact", 0):
        raise RuntimeError(
            "decorative content must use marked-content artifacts, not Artifact roles"
        )

    validate_pdfua_xmp(xmp)
    return summary


def metadata_reference(document: dict[str, Any]) -> str:
    catalog = find_catalog(qpdf_objects(document))
    reference = catalog.get("/Metadata")
    if not isinstance(reference, str) or not OBJECT_REFERENCE.fullmatch(reference):
        raise RuntimeError("catalog must reference an XMP Metadata stream")
    return reference


def extract_metadata_stream(qpdf: str, pdf: Path, reference: str) -> bytes:
    match = OBJECT_REFERENCE.fullmatch(reference)
    if not match:
        raise RuntimeError(f"invalid Metadata object reference: {reference}")
    result = run_text(
        [
            qpdf,
            "--json=2",
            "--json-key=qpdf",
            "--json-stream-data=inline",
            "--decode-level=all",
            f"--json-object={match.group(1)},{match.group(2)}",
            str(pdf),
        ]
    )
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"qpdf returned malformed Metadata JSON: {exc}") from exc
    objects = qpdf_objects(document)
    payload = objects.get(reference)
    stream = payload.get("stream") if isinstance(payload, dict) else None
    encoded = stream.get("data") if isinstance(stream, dict) else None
    if not isinstance(encoded, str):
        raise RuntimeError("qpdf did not return the XMP Metadata stream data")
    try:
        return base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise RuntimeError("qpdf returned invalid base64 Metadata stream data") from exc


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_elements(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(parent) if local_name(child.tag) == name]


def integer_attribute(element: ET.Element, name: str) -> int:
    value = element.get(name)
    if value is None:
        raise RuntimeError(
            f"veraPDF report element {local_name(element.tag)} "
            f"is missing {name}"
        )
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"veraPDF report attribute {name} is not an integer: {value}"
        ) from exc


def parse_verapdf_report(report: str | bytes) -> VeraPdfSummary:
    try:
        root = ET.fromstring(report)
    except ET.ParseError as exc:
        raise RuntimeError(f"veraPDF report is malformed: {exc}") from exc
    if local_name(root.tag) != "report":
        raise RuntimeError("veraPDF output root must be report")

    jobs_containers = child_elements(root, "jobs")
    if len(jobs_containers) != 1:
        raise RuntimeError("veraPDF report must contain exactly one jobs element")
    jobs = child_elements(jobs_containers[0], "job")
    if len(jobs) != 1:
        raise RuntimeError(
            f"veraPDF report must contain exactly one job; found {len(jobs)}"
        )
    validations = child_elements(jobs[0], "validationReport")
    if len(validations) != 1:
        raise RuntimeError(
            "veraPDF job must contain exactly one validationReport"
        )
    validation = validations[0]
    if validation.get("jobEndStatus") != "normal":
        raise RuntimeError(
            "veraPDF validation job did not end with normal status"
        )
    if validation.get("isCompliant") != "true":
        raise RuntimeError("veraPDF PDF/UA-2 validation is noncompliant")
    profile = validation.get("profileName", "")
    if "PDF/UA-2" not in profile:
        raise RuntimeError(
            f"veraPDF validation report used an unexpected profile: {profile}"
        )
    details = child_elements(validation, "details")
    if len(details) != 1:
        raise RuntimeError(
            "veraPDF validationReport must contain exactly one details element"
        )
    for attribute in ("failedRules", "failedChecks"):
        if integer_attribute(details[0], attribute) != 0:
            raise RuntimeError(
                f"veraPDF validationReport contains failures: {attribute}"
            )

    summaries = child_elements(root, "batchSummary")
    if len(summaries) != 1:
        raise RuntimeError(
            "veraPDF report must contain exactly one batchSummary element"
        )
    summary = summaries[0]
    total_jobs = integer_attribute(summary, "totalJobs")
    if total_jobs != 1:
        raise RuntimeError(
            f"veraPDF batchSummary totalJobs must be 1; found {total_jobs}"
        )
    for attribute in (
        "failedToParse",
        "encrypted",
        "outOfMemory",
        "veraExceptions",
    ):
        if integer_attribute(summary, attribute) != 0:
            raise RuntimeError(
                f"veraPDF batchSummary reports an exceptional job: {attribute}"
            )

    report_summaries = child_elements(summary, "validationReports")
    if len(report_summaries) != 1:
        raise RuntimeError(
            "veraPDF batchSummary must contain one validationReports element"
        )
    reports = report_summaries[0]
    compliant = integer_attribute(reports, "compliant")
    if compliant != 1:
        raise RuntimeError(
            f"veraPDF compliant validation count must be 1; found {compliant}"
        )
    for attribute in ("nonCompliant", "failedJobs"):
        if integer_attribute(reports, attribute) != 0:
            raise RuntimeError(
                f"veraPDF validationReports contains failures: {attribute}"
            )
    if (reports.text or "").strip() != "1":
        raise RuntimeError("veraPDF validationReports total must be 1")

    for report_type in ("featureReports", "repairReports"):
        elements = child_elements(summary, report_type)
        if len(elements) != 1:
            raise RuntimeError(
                f"veraPDF batchSummary must contain one {report_type} element"
            )
        if integer_attribute(elements[0], "failedJobs") != 0:
            raise RuntimeError(f"veraPDF {report_type} contains a failed job")

    return VeraPdfSummary(
        total_jobs=total_jobs,
        compliant_jobs=compliant,
        profile=profile,
    )


def run_verapdf(
    command: str,
    pdf: Path,
    report_path: Path,
    *,
    profile: str = VERAPDF_PROFILE,
) -> VeraPdfSummary:
    if profile != VERAPDF_PROFILE:
        raise ValueError(f"veraPDF profile must be {VERAPDF_PROFILE}")
    command_path = Path(command)
    command_words = [command] if command_path.is_file() else shlex.split(command)
    if not command_words:
        raise ValueError("veraPDF command must not be empty")
    result = run_text(
        [
            *command_words,
            "--format",
            "xml",
            "--flavour",
            profile,
            "--loglevel",
            "0",
            "--maxfailures",
            "-1",
            "--maxfailuresdisplayed",
            "-1",
            str(pdf),
        ],
        check=False,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(result.stdout, encoding="utf-8")
    summary = parse_verapdf_report(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(
            f"veraPDF exited with status {result.returncode} "
            "despite producing a report"
        )
    return summary


def load_qpdf_document(qpdf: str, pdf: Path) -> dict[str, Any]:
    result = run_text(
        [
            qpdf,
            "--json=2",
            "--json-key=qpdf",
            "--json-key=acroform",
            "--json-key=attachments",
            "--json-key=encrypt",
            str(pdf),
        ]
    )
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"qpdf returned malformed JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise RuntimeError("qpdf JSON root must be an object")
    return document


def validate_pdf_accessibility(
    pdf: Path,
    manifest: dict[str, Any],
    verapdf: str,
    report: Path,
) -> None:
    validate_manifest(manifest)
    qpdf = tool("qpdf")
    pdfinfo = tool("pdfinfo")
    info = parse_info(run_text([pdfinfo, str(pdf)]).stdout)
    validate_pdfinfo(info, manifest)
    document = load_qpdf_document(qpdf, pdf)
    objects = qpdf_objects(document)
    contents_page, body_page = validate_page_contract(
        find_catalog(objects),
        objects,
    )
    validate_named_page_destinations(
        run_text([pdfinfo, "-dests", str(pdf)]).stdout,
        contents_page=contents_page,
        body_page=body_page,
    )
    reference = metadata_reference(document)
    xmp = extract_metadata_stream(qpdf, pdf, reference)
    structure = validate_qpdf_document(document, manifest, xmp)
    validation = run_verapdf(verapdf, pdf, report)
    print(
        "pdf_accessibility_qa_passed "
        f"structure_roles={sum(structure.tags.values())} "
        f"figures={len(structure.figure_alt_text)} "
        f"verapdf_profile={VERAPDF_PROFILE} "
        f"verapdf_jobs={validation.total_jobs}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("pdf/guide_manifest.json"),
    )
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--verapdf", default="verapdf")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("dist/verapdf-report.xml"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
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
        manifest = load_manifest(manifest_path)
        pdf = args.pdf or output_path(root, manifest)
        if not pdf.is_absolute():
            pdf = root / pdf
        report = args.report
        if not report.is_absolute():
            report = root / report
        validate_pdf_accessibility(
            pdf,
            manifest,
            args.verapdf,
            report,
        )
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"ERROR: PDF accessibility QA failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
