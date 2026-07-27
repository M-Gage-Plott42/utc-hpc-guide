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

The full gate:

- builds twice with the manifest's fixed `SOURCE_DATE_EPOCH` and requires
  byte-identical PDFs;
- validates the PDF structure with `qpdf`;
- checks letter page size, metadata, encryption state, embedded fonts, and
  Unicode mappings with Poppler;
- extracts text and checks required guide sections and examples; and
- rasterizes every page to ensure the complete document renders.

The fixed build epoch follows Pandoc's
[reproducible-build guidance](https://pandoc.org/demo/example33/18-reproducible-builds.html).
The tracked XeLaTeX header also supplies a stable PDF trailer identifier so the
repository's supported Pandoc 3.1 toolchain produces identical bytes.

The generated release candidate is
`dist/UTC_HPC_Guide_v1.2.0-rc.1.pdf`. The `dist/` directory is intentionally
ignored: reviewed release binaries belong on the corresponding GitHub release,
while the tracked Markdown, manifest, and build scripts remain authoritative.

Reproducibility here means byte-identical output from the same source and
declared toolchain. A different Pandoc, XeLaTeX, or font package version can
produce different typesetting even when the guide content is unchanged.
