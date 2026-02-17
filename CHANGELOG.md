# Changelog

All notable changes to this repository are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Guidance docs updated for:
  - SLURM `#SBATCH` directive parsing behavior,
  - scheduler polling etiquette,
  - stronger scratch-vs-home placement and resource-sizing language.

## [1.0.0] - 2026-02-16

### Initial Release

- Initial public release of the UTC HPC onboarding guide with docs, sbatch templates, and release hygiene checklist.
