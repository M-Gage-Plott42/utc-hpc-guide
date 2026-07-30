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
- exact expected versions of qpdf, Poppler, Tesseract English OCR, Fontconfig,
  and the DejaVu fonts used by the build.

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

## Build and Automated Validation

Build the current review candidate:

```bash
make pdf
```

The manifest currently produces:

```text
dist/UTC_HPC_Guide_v1.2.1-rc.2.pdf
```

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
- checks US Letter page size, title, author, encryption state, embedded fonts,
  and Unicode mappings with Poppler;
- requires `Tagged: yes`, a structure tree, marked content, `en-US`, and the
  expected PDF/UA-2 identification;
- requires representative heading, list, table, table-header, table-cell,
  link, figure, and code structure;
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
  threshold, and checks representative headings in the combined OCR output.

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

Complete this review on the exact candidate identified by filename and
SHA-256. Record the reviewer, review date, operating system, assistive
technology or PDF viewer and version, findings, remediations, and unresolved
limitations.

- Navigate by headings and confirm a logical hierarchy.
- Navigate each list and confirm item boundaries and nesting.
- Read the document in logical order, including transitions around images,
  tables, page breaks, and Appendix B.
- Inspect the UTC partition table and confirm column headers are associated
  with each data cell.
- Review every link in context and confirm its purpose is understandable from
  the linked text and surrounding sentence.
- Inspect all three Open OnDemand figures and confirm their alternative text
  communicates the useful visual information without relying on the word
  "image" or exposing identifiers.
- Confirm repeated running headers, page numbers, rules, and purely decorative
  elements do not interrupt assistive-technology reading order.
- Read representative narrative and Appendix B code blocks with assistive
  technology; confirm punctuation, selection order, indentation, and line
  wrapping remain understandable.
- Check text, links, code styling, table rules, and meaningful graphics for
  sufficient contrast.
- Inspect every page at 200% zoom and test reflow mode where the review tool
  supports it; record any tool or format limitation rather than claiming a
  capability that was not tested.
- Complete an end-to-end screen-reader reading-order pass with the named tool
  and record defects or skipped content.
- Confirm the visual page review found no clipping, broken glyphs, unintended
  blanks, malformed code, table overflow, or exposed private information.

A reviewer may use the following evidence fields in the pull request:

```text
Reviewer:
Review date:
PDF filename and SHA-256:
Operating system:
PDF viewer and version:
Assistive technology and version:
Findings and remediations:
Unresolved limitations:
```

If machine validation, visual quality, reproducibility, OCR, or manual
accessibility review conflicts, stop with a release-candidate report. Do not
weaken or allowlist the failed gate and do not promote an unreviewed PDF.

## Reproducibility and Artifacts

The fixed build epoch follows Pandoc's
[reproducible-build guidance](https://pandoc.org/demo/example33/18-reproducible-builds.html).
The LuaLaTeX build uses Pandoc's supported deterministic trailer-identifier
path, fixed source ordering, and the locked toolchain. Reproducibility means
byte-identical output under that declared environment; it is not a claim of
signed or hermetic provenance.

After PDF QA passes, the hosted workflow uploads these files together:

- `UTC_HPC_Guide_v1.2.1-rc.2.pdf`;
- `build-toolchain.txt`; and
- `verapdf-report.xml`.

The toolchain record captures the commit and workflow run, runner image,
toolchain-lock digest, observed tool versions, structural and accessibility
results, and PDF SHA-256. The lock declares the expected inputs; the run record
describes one observed build. The hosted Ubuntu runner image and transitive
system dependencies are not digest-pinned, so this remains a reference build
rather than hermetic or signed provenance. The workflow artifact has a short
retention period.

The stable latest-release URL continues to serve `v1.2.0`.
`v1.2.1-rc.2` artifacts are review-only and are not for redistribution.
Reviewed final binaries belong on the matching GitHub release under the stable
asset name `UTC_HPC_Guide.pdf`.
