# Printable PDF Guide

The printable guide is assembled from the tracked numbered chapters, site
appendix, and runnable Slurm templates. Those files remain the canonical
editable sources; the repository does not maintain a second hand-edited copy
of the same content.

The document contract is `pdf/guide_manifest.json`. The PDF toolchain contract
is `pdf/toolchain.lock.json`. Build and validation commands derive the output
path from the manifest rather than maintaining a second filename setting.

## Locked Toolchain

The current Ubuntu 24.04 x86_64 toolchain pins:

- [Pandoc 3.10.1](https://github.com/jgm/pandoc/releases/tag/3.10.1);
- a frozen TeX Live 2025 repository with LuaLaTeX and the recorded LaTeX
  kernel and package revisions;
- [Eclipse Temurin 21.0.11+10](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.11%2B10);
- [veraPDF 1.30.2](https://software.verapdf.org/rel/1.30/) with its built-in
  `ua2` profile; and
- exact expected versions of qpdf, Poppler, Tesseract English OCR, and
  Fontconfig, MuPDF, and fontTools, plus revision- and archive-digest-pinned
  Noto Sans for body and display text, DejaVu Sans Mono for compact inline
  code, and Fira Code for fenced terminal and script blocks.

The frozen TeX Live repository supplies the Noto archive at revision `77677`.
The lock records that it has no catalogue version and binds its container to
SHA-512
`2e94b1490e1682391f66fe03ca46a70d2fa697eb71ae02b6d675a7b71b42c94e449f846fe459f3fd873450b1de5fd022bde96d8a96bb82e14db545800ccee5a6`.
The bootstrap rejects a different revision, digest, or an unexpected catalogue
version. Font files must resolve from the locked TeX trees; unrecorded host
font substitution is not a release build.

Fenced code uses the official static Fira Code 6.2 Regular face at
`9.1/11.5 pt`. The toolchain lock retains the official release tag and commit,
archive URL, archive member names, byte sizes, SHA-256 values, PostScript
names, and exact OFL license bytes for both Regular and Bold. The complete
fontspec ligature denylist and its raw OpenType equivalents are mandatory,
including `ContextualOff` and `-calt`; a missing option fails before the PDF is
built. Bold is validated in a tagged, test-only semantic fixture and is not
forced into the guide when canonical content does not use it.

The bootstrap requires Ubuntu 24.04 x86_64, Python 3, GnuPG, Perl, network
access, and the exact host QA packages recorded in the lock. It downloads into
the ignored `.cache/pdf-toolchain/` directory, verifies declared checksums and
release signatures, binds the signed TeX Live checksum to the installer,
verifies signing-key fingerprints, verifies every explicitly installed TeX
package container against its locked SHA-512, and checks exact installed
versions:

```bash
make setup-pdf-tools
```

After a complete verification, the cache receives an attestation containing
the exact lock-file digest. A missing or different attestation fails closed;
move the old cache aside and bootstrap again rather than reusing it under a
changed lock.

Do not substitute Ubuntu's distribution Pandoc or TeX packages for release
validation. The lock file, bootstrap, local Make targets, and hosted workflow
define one release toolchain.

## Presentation and Tagging Contract

The polished presentation remains part of the source-generated tagged build,
not a second hand-maintained Markdown or TeX document. The PDF intentionally
uses Noto Sans for prose and headings, DejaVu Sans Mono for compact inline
code, and Fira Code for fenced code. This semantic distinction keeps short
identifiers visually integrated with prose while terminal and script blocks
retain the selected code face. The document uses this reviewed palette:

- navy `#112E51` for the cover and primary navigation text;
- ink `#172033` for body and code text on white;
- code rail `#335E8A` and link blue `#1D4ED8`; and
- gold `#FDB736` only for decorative rules and accents, never as text on
  white.

The build retains the tagging-aware standard Article title, section,
table-of-contents, list, table, figure, and link commands. Code remains in the
custom semantic `Code` structure. It deliberately avoids `titlesec`,
`tocloft`, `needspace`, `listings`, `multirow`, and other packages that are
incompatible with the locked LaTeX tagging path. Decorative cover elements,
running headers, footers, rules, and code rails are marked as layout artifacts
rather than placed in logical reading order.

Chapter and subsection numbers are derived during assembly from the ordered
manifest. Appendix A and the four Appendix B templates receive corresponding
lettered numbers. The PDF-only Lua filter applies the reviewed `84%`, `78%`,
and `52%` widths to the three screenshots. Their ordinary Markdown image
labels remain the canonical alternatives and must reach the three `Figure`
structures unchanged and in source order.

## Build and Automated Validation

Build the manifest-selected document:

```bash
make pdf
```

The review-only `v1.2.2-rc.1` manifest produces:

```text
dist/UTC_HPC_Guide_v1.2.2-rc.1.pdf
```

The published `v1.2.1` stable asset remains unchanged while this candidate is
under review.

Run the accessibility gate against an existing build:

```bash
make check-pdf-accessibility
```

Run the complete PDF gate:

```bash
make check-pdf
```

For release-affecting work, run the repository-wide gate:

```bash
npm ci
make setup-pdf-tools
make release-check
```

The PDF gate:

- builds twice with the manifest's fixed `SOURCE_DATE_EPOCH` and requires
  byte-identical PDFs;
- generates PDF 2.0 through Pandoc's supported LuaLaTeX
  `pdfstandard=ua-2` path;
- validates basic PDF structure with qpdf;
- checks US Letter page size, title, author, encryption state, the exact
  embedded Noto Sans and DejaVu Sans Mono family set, and Unicode mappings with
  Poppler;
- requires `Tagged: yes`, a structure tree, marked content, `en-US`, and the
  expected PDF/UA-2 identification;
- requires representative heading, list, table, table-header, table-cell,
  link, figure, and code structure;
- requires the manifest's exact semantic role counts for headings, lists,
  table components, links, figures, code, and contents references so an
  omitted, duplicated, or reclassified meaningful element fails closed;
- requires every page to use structure tab order `/Tabs /S`, requires unique
  contiguous `/StructParents` values, and requires the viewer preference to
  display the document title;
- requires one physical `Cover` label, lowercase Roman contents labels
  starting at `i`, and Arabic body labels restarting at `1`;
- renders screenshots as non-floating, source-position figures with nearby
  contextual labels, and rejects detached caption structures that could move
  ahead of their headings or figures in logical reading order;
- checks the expected meaningful alternative descriptions for all three Open
  OnDemand screenshots;
- rejects forms, JavaScript, attachments, embedded files, and other prohibited
  active content;
- runs the pinned veraPDF `ua2` profile and preserves the machine-readable
  result as `dist/verapdf-report.xml`;
- extracts text and checks required guide sections and examples;
- rasterizes every page and requires the complete document to render; and
- runs Tesseract against every rendered page, enforces the per-page text
  threshold, checks representative headings in the combined OCR output, and
  separately requires `Practical HPC Onboarding Guide` and
  `Release candidate for v1.2.2` to be legible on physical page 1.

The [Pandoc LaTeX variables](https://pandoc.org/demo/example33/19.1-latex.html)
enable the source-generated PDF-standard path. The
[LaTeX tagging project instructions](https://latex3.github.io/tagging-project/documentation/usage-instructions)
describe the underlying tagging support, and the
[veraPDF CLI documentation](https://docs.verapdf.org/cli/validation/) describes
the independent machine validator.

The OCR check is a legibility regression test, not proof of privacy,
redaction, or accessibility. Likewise, a tagged PDF and passing veraPDF report
cover machine-verifiable requirements only. They do not certify WCAG 2.1 AA,
prove usable reading order, or constitute UTC accessibility approval.

## Manual Accessibility Review

Complete this review only after source edits are finished, on the exact
document identified by filename and SHA-256. Any PDF-changing commit
invalidates earlier evidence.

W3C PDF3 lists either of these reading-order methods:

- read the document with a screen reader or read-aloud tool and listen for
  correct order; or
- inspect the order with a tool that exposes the document through an
  accessibility API.

This repository uses a stricter publication-evidence boundary: a completed
manual reading-order result requires a screen reader or accessibility-API
inspection. A read-aloud-only run is supplemental and must leave the full
manual reading-order result recorded as not tested.

It permits either keyboard traversal or a tool that exposes the page
tab-order setting for focus-order review. Choose and record the methods
actually used. Record the reviewer profile, date, exact tools and versions,
relevant settings, tasks, itemized results, defects, remediations, retest
results, PDF hash before and after review, and every untested limitation.
Do not infer a result for a tool or assistive-technology pairing that was not
run.

Current desktop Adobe Acrobat Reader plus current stable NVDA on Windows 11 is
the recommended reference environment because it exercises screen-reader
semantics and structural navigation in a common desktop pairing. It is not an
exclusive release requirement. When using it, open the local PDF in Reader
rather than a browser viewer, use the tagged document structure rather than a
reading-order override, record Reader and NVDA settings, and record the
reviewer's proficiency. Other screen-reader/viewer pairings or accessibility
API inspection tools are valid evidence when their exact environment and
limitations are disclosed.

Adobe explicitly states that
[Read Out Loud is not a screen reader](https://helpx.adobe.com/reader/desktop/accessibility-features.html#use-the-read-out-loud-text-to-speech-tool).
Although it is a read-aloud tool described by one W3C PDF3 test option, this
repository treats it only as supplemental evidence. It does not exercise
screen-reader navigation, establish screen-reader interoperability, or
complete this repository's manual reading-order review by itself.

Complete and record each applicable result as pass, fail, or not tested:

- Confirm the document title and heading hierarchy through structural
  navigation or accessibility-API inspection.
- Confirm list boundaries, counts, and nesting.
- Confirm every UTC partition-table cell retains the correct `Partition` or
  `Public UTC notes` column header and row/column relationship.
- Confirm all three Open OnDemand figures expose each useful alternative
  description once at the intended source position, without a filename,
  identifier, or detached caption.
- Confirm meaningful link purpose and logical focus order for representative
  contents and external links. Test activation without a mouse when keyboard
  traversal is the selected focus-order method.
- Complete an end-to-end reading-order pass from the title through Appendix B.
  Meaningful content must occur once in logical order; repeated running
  headers, page numbers, rules, and decorative elements must not interrupt it.
- Inspect representative narrative commands and the complete CPU and
  TensorFlow Appendix B templates line by line. Confirm quoting, variables,
  comments, indentation, wrapping, and page transitions remain
  understandable under the selected reading-order method.
- Inspect every page at 200% zoom and with a reflow-capable viewer. Optionally
  use a screen magnifier and record whether narrative content remains readable
  without clipping, overlap, or unnecessary two-dimensional scrolling. A
  table or indentation-dependent code may retain two-dimensional layout; no
  information may disappear.
- Confirm the separate visual review found no clipping, broken glyphs,
  unintended blanks, malformed code, table overflow, insufficient contrast,
  or exposed private information.

The [NVDA user guide](https://download.nvaccess.org/releases/stable/documentation/en/userGuide.html#BrowseMode)
documents Adobe Reader browse mode and structural navigation for headings,
lists, tables, links, and graphics. W3C's
[PDF reading- and tab-order test](https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF3)
permits the reading-order and focus-order methods listed above. Adobe documents
[tag-dependent reflow](https://helpx.adobe.com/uk/acrobat/using/reading-pdfs-reflow-accessibility-features.html#reflow-a-pdf),
and Section508.gov provides a
[manual PDF testing and remediation series](https://www.section508.gov/create/pdfs/).

JAWS with Acrobat, VoiceOver with a supported macOS viewer, or another pairing
can broaden confidence. A clean result demonstrates only the named
environment, reviewer profile, settings, and tasks; it does not establish
universal assistive-technology interoperability, WCAG or Section 508
certification, disability-user testing, or UTC accessibility approval.

Record the following evidence in a pull-request comment so recording the
review does not alter the PDF that was tested:

```text
Reviewer and tester profile:
Review date:
PDF filename:
SHA-256 before and after review:
Operating system:
Viewer, reading-order tool, and versions:
Relevant settings:
Reading-order method and result:
Focus-order method and result:
Heading/list/table/figure/link/code/end-to-end results:
Keyboard, magnification, and reflow results, as tested:
Defects, remediations, and retest result:
Untested tools and assistive-technology pairings:
Unresolved limitations:
```

Omitted, duplicated, materially reordered, mislabeled, or unusable meaningful
content found by a performed review is a release blocker even when veraPDF
passes. If machine validation, visual quality, reproducibility, OCR, or a
performed manual accessibility check conflicts, stop and remediate. Do not
weaken or allowlist a failed gate. An independent GitHub release must disclose
the exact evidence and untested limitations and must not imply institutional
endorsement. Institution-hosted or officially endorsed publication remains
subject to that institution's documented accessibility review and publishing
process.

## Reproducibility and Artifacts

The fixed build epoch follows Pandoc's
[reproducible-build guidance](https://pandoc.org/demo/example33/18-reproducible-builds.html).
The LuaLaTeX build uses Pandoc's supported deterministic trailer-identifier
path, fixed source ordering, and the locked toolchain. Reproducibility means
byte-identical output under that declared environment; it is not a claim of
signed or hermetic provenance.

After PDF QA passes, the hosted workflow uploads these files together:

- the manifest-selected PDF, currently
  `UTC_HPC_Guide_v1.2.2-rc.1.pdf`;
- `build-toolchain.txt`; and
- `verapdf-report.xml`.

The toolchain record captures the commit and workflow run, runner image,
toolchain-lock digest, observed tool versions, structural and accessibility
results, and PDF SHA-256. The lock declares the expected inputs; the run record
describes one observed build. The hosted Ubuntu runner image and transitive
system dependencies are not digest-pinned, so this remains a reference build
rather than hermetic or signed provenance. The workflow artifact has a short
retention period.

The existing `v1.2.1` GitHub release remains the stable publication. A
candidate artifact is review-only: complete the exact-hash automated, visual,
OCR, and manual review before changing the manifest to final. Only a reviewed
final build belongs on a matching GitHub release under the stable asset name
`UTC_HPC_Guide.pdf`; a candidate must not overwrite the existing release.
