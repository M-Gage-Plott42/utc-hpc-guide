from __future__ import annotations

import copy
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_pdf_accessibility import (
    parse_info,
    parse_verapdf_report,
    run_verapdf,
    validate_manifest,
    validate_named_page_destinations,
    validate_pdfinfo,
    validate_qpdf_document,
)


ALTERNATIVES = [
    "Open OnDemand desktop request form with sanitized resource fields.",
    "Open OnDemand session card showing a sanitized running desktop.",
    "Open OnDemand Files menu showing sanitized home and project shortcuts.",
]

MANIFEST = {
    "schema_version": 2,
    "title": "Practical HPC Onboarding Guide",
    "author": "Gage Plott",
    "language": "en-US",
    "pdf_standard": "ua-2",
    "expected_figure_alt_text": ALTERNATIVES,
    "expected_structure_counts": {
        "H1": 1,
        "H2": 1,
        "L": 1,
        "Table": 1,
        "TH": 1,
        "TD": 1,
        "Link": 1,
        "Code": 1,
        "Figure": 3,
    },
}

PDFINFO = """\
Title:           Practical HPC Onboarding Guide
Author:          Gage Plott
Metadata Stream: yes
Tagged:          yes
Form:            none
JavaScript:      no
Encrypted:       no
PDF version:     2.0
"""

DESTINATIONS = """\
Page  Destination                 Name
   1 [ XYZ   52  740 null      ] "Doc-Start"
   2 [ XYZ   51  775 null      ] "page.i"
   3 [ XYZ   69  705 null      ] "page.1"
"""

XMP = b"""\
<?xpacket begin="\xef\xbb\xbf"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description xmlns:pdfuaid="http://www.aiim.org/pdfua/ns/id/">
      <pdfuaid:part>2</pdfuaid:part>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>
"""

PASS_REPORT = """\
<?xml version="1.0" encoding="utf-8"?>
<report>
  <jobs>
    <job>
      <item size="123"><name>guide.pdf</name></item>
      <validationReport
        profileName="PDF/UA-2 validation profile"
        jobEndStatus="normal"
        isCompliant="true">
        <details passedRules="10" failedRules="0"
          passedChecks="20" failedChecks="0" />
      </validationReport>
    </job>
  </jobs>
  <batchSummary totalJobs="1" failedToParse="0" encrypted="0"
    outOfMemory="0" veraExceptions="0">
    <validationReports compliant="1" nonCompliant="0"
      failedJobs="0">1</validationReports>
    <featureReports failedJobs="0">0</featureReports>
    <repairReports failedJobs="0">0</repairReports>
  </batchSummary>
</report>
"""


def structure_element(role: str, *, alt: str | None = None) -> dict[str, object]:
    value: dict[str, object] = {
        "/Type": "/StructElem",
        "/S": f"/{role}",
        "/K": 0,
    }
    if alt is not None:
        value["/Alt"] = f"u:{alt}"
    return {"value": value}


def passing_qpdf_document() -> dict[str, object]:
    role_objects = {
        "3 0 R": structure_element("H1"),
        "4 0 R": structure_element("H2"),
        "5 0 R": structure_element("L"),
        "6 0 R": structure_element("Table"),
        "7 0 R": structure_element("TH"),
        "8 0 R": structure_element("TD"),
        "9 0 R": structure_element("Link"),
        "10 0 R": structure_element("Code"),
        "11 0 R": structure_element("Figure", alt=ALTERNATIVES[0]),
        "12 0 R": structure_element("Figure", alt=ALTERNATIVES[1]),
        "13 0 R": structure_element("Figure", alt=ALTERNATIVES[2]),
    }
    objects: dict[str, object] = {
        "obj:1 0 R": {
            "value": {
                "/Type": "/Catalog",
                "/Lang": "u:en-US",
                "/MarkInfo": {"/Marked": True},
                "/StructTreeRoot": "2 0 R",
                "/Metadata": "14 0 R",
                "/ViewerPreferences": {"/DisplayDocTitle": True},
                "/PageLabels": {
                    "/Nums": [
                        0,
                        {"/P": "u:Cover"},
                        1,
                        {"/S": "/r"},
                        2,
                        {"/S": "/D"},
                    ]
                },
            }
        },
        "obj:2 0 R": {
            "value": {
                "/Type": "/StructTreeRoot",
                "/K": list(role_objects),
            }
        },
        "obj:14 0 R": {
            "stream": {
                "dict": {
                    "/Type": "/Metadata",
                    "/Subtype": "/XML",
                }
            }
        },
        "obj:15 0 R": {
            "value": {
                "/Type": "/Page",
                "/Tabs": "/S",
                "/StructParents": 0,
            }
        },
        "obj:16 0 R": {
            "value": {
                "/Type": "/Page",
                "/Tabs": "/S",
                "/StructParents": 1,
            }
        },
        "obj:17 0 R": {
            "value": {
                "/Type": "/Page",
                "/Tabs": "/S",
                "/StructParents": 2,
            }
        },
    }
    objects.update({f"obj:{key}": value for key, value in role_objects.items()})
    return {
        "version": 2,
        "acroform": {
            "fields": [],
            "hasacroform": False,
            "needappearances": False,
        },
        "attachments": {},
        "encrypt": {"encrypted": False},
        "qpdf": [
            {
                "jsonversion": 2,
                "pdfversion": "2.0",
                "calledgetallpages": True,
                "maxobjectid": 17,
            },
            objects,
        ],
    }


class PdfAccessibilityStructureTests(unittest.TestCase):
    def test_accepts_complete_machine_verifiable_structure(self) -> None:
        validate_pdfinfo(parse_info(PDFINFO), MANIFEST)
        summary = validate_qpdf_document(
            passing_qpdf_document(),
            MANIFEST,
            XMP,
        )
        self.assertEqual(summary.tags["Figure"], 3)
        self.assertEqual(summary.tags["TH"], 1)
        self.assertEqual(summary.figure_alt_text, tuple(ALTERNATIVES))

    def test_rejects_pdfinfo_missing_tagging(self) -> None:
        info = parse_info(
            PDFINFO.replace("Tagged:          yes", "Tagged:          no")
        )
        with self.assertRaisesRegex(RuntimeError, "Tagged: yes"):
            validate_pdfinfo(info, MANIFEST)

    def test_rejects_missing_structure_tree(self) -> None:
        document = passing_qpdf_document()
        del document["qpdf"][1]["obj:1 0 R"]["value"]["/StructTreeRoot"]
        with self.assertRaisesRegex(RuntimeError, "StructTreeRoot"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_wrong_catalog_language(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:1 0 R"]["value"]["/Lang"] = "u:en"
        with self.assertRaisesRegex(RuntimeError, "catalog Lang"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_page_without_structure_tab_order(self) -> None:
        document = passing_qpdf_document()
        del document["qpdf"][1]["obj:16 0 R"]["value"]["/Tabs"]
        with self.assertRaisesRegex(RuntimeError, r"Tabs /S"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_duplicate_page_structure_parent(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:16 0 R"]["value"]["/StructParents"] = 0
        with self.assertRaisesRegex(RuntimeError, "unique and contiguous"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_missing_display_document_title_preference(self) -> None:
        document = passing_qpdf_document()
        del document["qpdf"][1]["obj:1 0 R"]["value"][
            "/ViewerPreferences"
        ]
        with self.assertRaisesRegex(RuntimeError, "DisplayDocTitle"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_duplicate_cover_and_body_page_style(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:1 0 R"]["value"]["/PageLabels"][
            "/Nums"
        ] = [0, {"/S": "/D"}]
        with self.assertRaisesRegex(RuntimeError, "Cover, Roman contents"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_contents_page_label_prefix(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:1 0 R"]["value"]["/PageLabels"][
            "/Nums"
        ][3]["/P"] = "u:x"
        with self.assertRaisesRegex(RuntimeError, "lowercase Roman label i"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_body_page_label_prefix(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:1 0 R"]["value"]["/PageLabels"][
            "/Nums"
        ][5]["/P"] = "u:x"
        with self.assertRaisesRegex(RuntimeError, "Arabic label 1"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_accepts_distinct_contents_and_body_destinations(self) -> None:
        validate_named_page_destinations(
            DESTINATIONS,
            contents_page=2,
            body_page=3,
        )

    def test_rejects_body_destination_on_cover(self) -> None:
        destinations = DESTINATIONS.replace(
            '   3 [ XYZ   69  705 null      ] "page.1"',
            '   1 [ XYZ   69  705 null      ] "page.1"',
        )
        with self.assertRaisesRegex(RuntimeError, '"page.1".*page 3'):
            validate_named_page_destinations(
                destinations,
                contents_page=2,
                body_page=3,
            )

    def test_rejects_duplicate_contents_destination(self) -> None:
        destinations = DESTINATIONS + (
            '   2 [ XYZ   52  600 null      ] "page.i"\n'
        )
        with self.assertRaisesRegex(RuntimeError, '"page.i".*exactly once'):
            validate_named_page_destinations(
                destinations,
                contents_page=2,
                body_page=3,
            )

    def test_rejects_expected_structure_count_drift(self) -> None:
        manifest = copy.deepcopy(MANIFEST)
        manifest["expected_structure_counts"]["H1"] = 2
        with self.assertRaisesRegex(RuntimeError, r"H1=1 \(expected 2\)"):
            validate_qpdf_document(
                passing_qpdf_document(),
                manifest,
                XMP,
            )

    def test_rejects_artifact_structure_role(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:18 0 R"] = structure_element("Artifact")
        document["qpdf"][1]["obj:2 0 R"]["value"]["/K"].append("18 0 R")
        with self.assertRaisesRegex(RuntimeError, "marked-content artifacts"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_missing_figure_alt_text(self) -> None:
        document = passing_qpdf_document()
        del document["qpdf"][1]["obj:11 0 R"]["value"]["/Alt"]
        with self.assertRaisesRegex(RuntimeError, "missing Alt"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_alt_text_not_listed_in_manifest(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:11 0 R"]["value"]["/Alt"] = (
            "u:A different but otherwise descriptive alternative for this image."
        )
        with self.assertRaisesRegex(RuntimeError, "exactly match"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_figure_alternatives_out_of_source_order(self) -> None:
        document = passing_qpdf_document()
        root_kids = document["qpdf"][1]["obj:2 0 R"]["value"]["/K"]
        root_kids[-3], root_kids[-2] = root_kids[-2], root_kids[-3]
        with self.assertRaisesRegex(RuntimeError, "source order"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_detached_caption_structure(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:18 0 R"] = structure_element("Caption")
        document["qpdf"][1]["obj:2 0 R"]["value"]["/K"].insert(0, "18 0 R")
        with self.assertRaisesRegex(RuntimeError, "detached Caption"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_missing_table_header_role(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:7 0 R"]["value"]["/S"] = "/TD"
        with self.assertRaisesRegex(RuntimeError, r"TH"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_javascript_active_content(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:18 0 R"] = {
            "value": {"/S": "/JavaScript", "/JS": "u:app.alert('no')"}
        }
        with self.assertRaisesRegex(RuntimeError, "JavaScript"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_associated_file_attachment(self) -> None:
        document = passing_qpdf_document()
        document["qpdf"][1]["obj:18 0 R"] = {
            "value": {"/Type": "/Filespec", "/AF": ["19 0 R"]}
        }
        with self.assertRaisesRegex(RuntimeError, "file"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_acroform_summary(self) -> None:
        document = passing_qpdf_document()
        document["acroform"]["hasacroform"] = True
        with self.assertRaisesRegex(RuntimeError, "AcroForm"):
            validate_qpdf_document(document, MANIFEST, XMP)

    def test_rejects_missing_pdfua_identifier(self) -> None:
        xmp = XMP.replace(b"<pdfuaid:part>2</pdfuaid:part>", b"")
        with self.assertRaisesRegex(RuntimeError, "PDF/UA-2"):
            validate_qpdf_document(passing_qpdf_document(), MANIFEST, xmp)

    def test_rejects_malformed_xmp(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "XMP metadata is malformed"):
            validate_qpdf_document(
                passing_qpdf_document(),
                MANIFEST,
                b"<x:xmpmeta>",
            )

    def test_requires_three_meaningful_manifest_alternatives(self) -> None:
        manifest = copy.deepcopy(MANIFEST)
        manifest["expected_figure_alt_text"] = ["short", *ALTERNATIVES[1:]]
        with self.assertRaisesRegex(ValueError, "meaningful"):
            validate_manifest(manifest)


class VeraPdfReportTests(unittest.TestCase):
    def test_accepts_one_compliant_pdfua2_job(self) -> None:
        summary = parse_verapdf_report(PASS_REPORT)
        self.assertEqual(summary.total_jobs, 1)
        self.assertEqual(summary.compliant_jobs, 1)
        self.assertIn("PDF/UA-2", summary.profile)

    def test_rejects_malformed_report(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "malformed"):
            parse_verapdf_report("<report>")

    def test_rejects_noncompliant_report(self) -> None:
        report = PASS_REPORT.replace('isCompliant="true"', 'isCompliant="false"')
        report = report.replace('compliant="1"', 'compliant="0"')
        report = report.replace('nonCompliant="0"', 'nonCompliant="1"')
        with self.assertRaisesRegex(RuntimeError, "noncompliant"):
            parse_verapdf_report(report)

    def test_rejects_exceptional_report(self) -> None:
        report = PASS_REPORT.replace('veraExceptions="0"', 'veraExceptions="1"')
        with self.assertRaisesRegex(RuntimeError, "exceptional"):
            parse_verapdf_report(report)

    def test_rejects_multiple_jobs(self) -> None:
        report = PASS_REPORT.replace(
            "</jobs>",
            "<job><validationReport "
            'profileName="PDF/UA-2 validation profile" '
            'jobEndStatus="normal" isCompliant="true">'
            '<details failedRules="0" failedChecks="0"/>'
            "</validationReport></job></jobs>",
        )
        with self.assertRaisesRegex(RuntimeError, "exactly one job"):
            parse_verapdf_report(report)

    @patch("scripts.check_pdf_accessibility.subprocess.run")
    def test_invokes_locked_flavour_and_writes_report(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=PASS_REPORT,
            stderr="",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = Path(temporary_directory) / "verapdf-report.xml"
            summary = run_verapdf(
                "/opt/verapdf/verapdf",
                Path("guide.pdf"),
                report,
            )
            self.assertEqual(report.read_text(encoding="utf-8"), PASS_REPORT)
            self.assertEqual(summary.compliant_jobs, 1)

        command = run_mock.call_args.args[0]
        self.assertEqual(command[0], "/opt/verapdf/verapdf")
        self.assertIn("--flavour", command)
        self.assertEqual(command[command.index("--flavour") + 1], "ua2")
        self.assertEqual(command[command.index("--format") + 1], "xml")

    @patch("scripts.check_pdf_accessibility.subprocess.run")
    def test_rejects_nonzero_exit_even_with_compliant_report(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout=PASS_REPORT,
            stderr="unexpected failure",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = Path(temporary_directory) / "verapdf-report.xml"
            with self.assertRaisesRegex(RuntimeError, "status 2"):
                run_verapdf("verapdf", Path("guide.pdf"), report)
            self.assertEqual(report.read_text(encoding="utf-8"), PASS_REPORT)


if __name__ == "__main__":
    unittest.main()
