# Printable PDF Guide

The printable guide is assembled from the tracked numbered chapters,
site appendix, and runnable Slurm templates. Those files remain the canonical
editable sources; the repository does not maintain a second hand-edited copy
of the same content.

The ordered source manifest is `pdf/guide_manifest.json`. Build the current
release candidate with:

```bash
make pdf
```

Run the full PDF gate with:

```bash
make check-pdf
```

For release-affecting work, use the repository-wide gate instead:

```bash
npm ci
make release-check
```

That target includes the routine content checks, Bash syntax and ShellCheck
validation, the full PDF gate, and `git diff --check`.

The full gate:

- builds twice with the manifest's fixed `SOURCE_DATE_EPOCH` and requires
  byte-identical PDFs;
- validates the PDF structure with `qpdf`;
- checks letter page size, metadata, encryption state, embedded fonts, and
  Unicode mappings with Poppler;
- extracts text and checks required guide sections and examples; and
- rasterizes every page to ensure the complete document renders;
- runs Tesseract against every rendered page and requires a minimum amount of
  visible OCR text on each one; and
- checks representative guide and appendix headings in the combined OCR
  output.

The OCR check is a legibility regression test, not a claim that OCR can prove
privacy or redaction quality. Human review of every page and source image
remains mandatory. The local PDF toolchain therefore also requires the
`tesseract` command with English language data.

The fixed build epoch follows Pandoc's
[reproducible-build guidance](https://pandoc.org/demo/example33/18-reproducible-builds.html).
The tracked XeLaTeX header also supplies a stable PDF trailer identifier so the
repository's supported Pandoc 3.1 toolchain produces identical bytes.

The generated release candidate is
`dist/UTC_HPC_Guide_v1.2.1-rc.1.pdf`. The `dist/` directory is intentionally
ignored: reviewed final release binaries belong on the corresponding GitHub
release, while the tracked Markdown, manifest, and build scripts remain
authoritative.

Reproducibility here means byte-identical output from the same source and
declared toolchain. A different Pandoc, XeLaTeX, or font package version can
produce different typesetting even when the guide content is unchanged.

The PDF workflow runs on `ubuntu-24.04`. After PDF QA passes, it uploads the
PDF and `build-toolchain.txt` together as one review artifact. The record
captures the commit and workflow run, runner image, operating system, command
and package versions, resolved DejaVu fonts, and PDF SHA-256 observed during
that run.

This is traceability, not a complete toolchain lock or signed build
provenance. The fixed runner label does not freeze future runner-image or apt
package updates, and the workflow artifact has a short retention period.
Publish a separately reviewed PDF on the matching GitHub release for durable
distribution.
