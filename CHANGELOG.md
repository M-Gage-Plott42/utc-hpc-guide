# Changelog

All notable changes to this repository are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Locked the exact TeX Live 2025 Noto archive by repository revision and
  SHA-512, including explicit validation that the archive has no catalogue
  version, and paired Noto Sans body text with the existing locked DejaVu Sans
  Mono code font.
- Added cover-specific OCR requirements, exact logical-structure role counts,
  the exact embedded font-family set, and page contracts for document-title
  display, structure tab order, contiguous structure-parent identifiers, and
  distinct cover, contents, and body page labels.
- Selected official static Fira Code 6.2 for canonical fenced code, with exact
  Regular/Bold font and license provenance, a complete ligature/contextual
  denylist, and an isolated tagged semantic fixture that validates default
  glyphs and meaningful source spacing without entering release artifacts.
- Added fail-closed chapter-opener, Appendix-template, heading-font, code-rail,
  and canonical 80-character source-width contracts.

### Changed

- Redesigned the `v1.2.2-rc.2` printable candidate through the locked,
  reproducible Pandoc/LuaLaTeX PDF/UA-2 path while retaining tagging-aware
  standard title, section, contents, list, table, figure, link, and code
  structures.
- Added a high-contrast navy cover, accessible text colors, restrained gold
  decoration, two-column contents, stronger heading hierarchy, running
  navigation, and styled semantic code rails without introducing the
  tagging-incompatible and only partially compatible packages used by the
  visual prototype.
- Derived chapter, subsection, and appendix-template numbering during PDF
  assembly and applied reviewed screenshot sizes in the PDF Lua filter while
  preserving the normal Markdown image alternatives as canonical content.
- Assigned the physical cover the unique `Cover` label, used lowercase Roman
  labels for contents and Arabic labels for the body, and kept cover, header,
  footer, rule, and code-rail decoration out of logical reading order.
- Corrected generated Appendix B source boundaries, kept chapter and template
  headings with their opening content, normalized PDF-only heading typography,
  wrapped long canonical commands, added concise terminology and placeholder
  guidance, and added one-file `scp` examples ahead of incremental `rsync`.
- Reduced the permanent pipeline to the canonical RC.2 and temporary selected-
  Fira fixture. The completed three-font comparison remains historical
  review-only evidence on draft PR #28 and is not a release artifact.

## [1.2.1] - 2026-07-30

### Added

- Added a checksum- and signature-verifying PDF toolchain bootstrap locked to
  Pandoc 3.10.1, frozen TeX Live 2025 with LuaLaTeX, Eclipse Temurin
  21.0.11+10, and veraPDF 1.30.2 with the `ua2` profile.
- Added source-generated PDF/UA-2 structure checks, a preserved
  machine-readable veraPDF report, and a manual accessibility review checklist
  for the final `v1.2.1` document.

### Changed

- Migrated the printable-guide build contract from the distribution
  Pandoc/XeLaTeX path to manifest-derived output paths and the locked LuaLaTeX
  tagged-PDF path while retaining byte-identical rebuild, structural, render,
  text-extraction, font, and every-page OCR gates.
- Made the public-content scrub fail closed on tracked symbolic links,
  gitlinks, unmerged or unsupported index entries, and worktree replacement
  links while scanning both indexed and differing worktree content through a
  repository-rooted boundary that opens every path component without following
  symbolic links.
- Rechecked the selected UTC partition facts against current public
  documentation and a July 30 read-only live session; recorded the confirmed
  4 GiB scheduler default and authenticated Open OnDemand route. The
  authenticated desktop form independently corroborates the conservative
  public CPU request ceiling; the higher raw Slurm value remains a disclosed,
  nonblocking administrative discrepancy rather than permission to request
  more.
- Defined product-neutral manual accessibility evidence for reading order,
  focus order, structure, keyboard use, magnification, and reflow, bound to the
  exact PDF hash with tested-tool and untested-limitation disclosures. Desktop
  Acrobat Reader plus NVDA remains a recommended reference pairing.
- Corrected Open OnDemand guidance to describe `srun --jobid` as a new,
  resource-sharing job step rather than an attachment to an existing app.
- Qualified CPU-count diagnostics and added comparisons with Slurm allocation
  variables and `scontrol show job`.
- Made Python environment placement site-dependent, with persistent
  project/software storage preferred when environments must survive and
  durable reconstruction metadata required when scratch may be purged.
- Scoped the UTC partition table to a selected onboarding subset and labeled
  the 64 GB examples as field-note diagnostic starting points, not minima.
- Unified the local release gate, added PDF build traceability, and added
  every-page OCR legibility checks for the final v1.2.1 document.
- Hardened asset-path, shell-fence, and public-content policy boundaries; added
  scheduled external-link monitoring; and consolidated Markdown lint under the
  locked Quality Gate.
- Derived workflow artifact identity and build distribution status from the
  validated candidate-or-final manifest instead of RC-specific workflow text.

## [1.2.0] - 2026-07-27

### Added

- Locked local Markdown tooling through checked `package.json` and
  `package-lock.json` files.
- GitHub dependency review for pull requests and merge-queue checks via
  `.github/workflows/dependency-review.yml` and
  `.github/dependency-review-config.yml`.
- UTC MocsHPC site notes covering the March 2026 refresh, explicit memory
  requests, GPU partition selection, CUDA module checks, and Jobstats usage.
- TensorFlow GPU probe example for diagnosing Slurm allocation, framework GPU
  visibility, and memory-related kills.
- Deterministic printable-guide assembly, byte-for-byte reproducibility checks,
  PDF structure/font/text/render QA, and a dedicated hosted PDF workflow.
- Shell-placeholder validation and focused failure-path tests.

### Changed

- The quality workflow now uses `npm ci` and the repository-local
  `markdownlint` binary instead of installing an unpinned global CLI.
- Dependency-review action pins now carry exact, provenance-verified release
  comments.
- Existing required workflows now use workflow-level concurrency and
  `merge_group` triggers so repository checks stay stable in merge queues.
- Markdown lint config now allows repeated changelog subsection headings under
  different release versions so `make check` matches the repository's own
  changelog format.
- Strengthened Slurm and GPU documentation to emphasize explicit `--mem`
  requests and post-run memory inspection.
- Expanded troubleshooting for plain `Killed` failures in Python and ML
  workloads.
- Clarified that Python environment rebuilds should follow allocation and
  memory checks, not precede them.
- Replaced assumed `/scratch/$USER` and `/home/<username>` paths with quoted,
  site-configurable storage placeholders.
- Pinned the Miniconda Linux x86-64 installer example to an exact release and
  source-verified SHA-256 digest.
- Replaced fixed-path scrub commands with a fail-closed scan of every tracked
  text file and explicit, path-bound exceptions for official public site facts.
- Added scrub-policy tests for expanded path coverage, exact site exceptions,
  and stale exceptions.
- Replaced the regular-expression-only local link scan with a parser-based
  validator for Markdown, reference-style, and raw HTML links.
- Added local heading-anchor validation, including duplicate GitHub-style
  heading suffixes, plus link-parser failure-path tests.
- Expanded PNG checks from signature and metadata inspection to CRC, chunk
  order and uniqueness, terminal IEND, bounded decompression, scanline/filter,
  color/palette, and explicit ancillary-chunk policy validation.
- Added corrupt, malformed, metadata-bearing, and decode failure-path tests for
  public PNG assets.
- Replaced the remaining assumed scratch paths in runnable CPU/GPU examples
  with fail-closed, site-configurable environment paths.
- Clarified whole-job versus job-step interpretation of Slurm `ReqMem` and
  `MaxRSS`.
- Updated generic TensorFlow GPU installation guidance while keeping
  site-module compatibility decisions explicit.

## [1.1.0] - 2026-02-17

### Added

- CI quality gate workflow (`.github/workflows/quality.yml`) that runs `make check`.
- Shell lint workflow for sbatch templates (`.github/workflows/shell-lint.yml`).
- Asset hygiene checker script (`scripts/check_assets.py`) and `make check-assets` target.
- Repository governance files:
  - `.github/CODEOWNERS`
  - `.github/ISSUE_TEMPLATE/bug_report.yml`
  - `.github/ISSUE_TEMPLATE/feature_request.yml`
  - `.github/ISSUE_TEMPLATE/config.yml`

### Changed

- `Makefile` scrub checks now include strict-fail patterns and manual-review patterns.
- `make check` now enforces markdown linting, scrub checks, asset checks, and Markdown link checks.
- `markdown-lint` workflow now uses full-SHA pinned actions.
- sbatch templates updated to satisfy `shellcheck` (`SC1091`/`SC2086`) in CI.
- Guidance docs updated for:
  - SLURM `#SBATCH` directive parsing behavior,
  - scheduler polling etiquette,
  - stronger scratch-vs-home placement and resource-sizing language.

## [1.0.0] - 2026-02-16

### Initial Release

- Initial public release of the UTC HPC onboarding guide with docs, sbatch templates, and release hygiene checklist.
