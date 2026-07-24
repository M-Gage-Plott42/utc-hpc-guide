# Changelog

All notable changes to this repository are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
