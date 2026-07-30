# Audit Maintenance Implementation Ledger

This ledger records the reconciled implementation plan for the independent
v1.2.0 audit. Reload this file and `AGENTS.md` before resuming work after any
context reset.

Baseline:

- Audit commit: `da32b64000ffa9cb87e497fbc28cfcc342731577`
- Working branch: `audit-maintenance-v1.2.1`
- Scope: public, cluster-agnostic documentation plus isolated UTC public notes
- Prohibited: private identifiers, live-cluster mutations, release publication,
  or unrelated repository cleanup

## Phase 0: Baseline and Durable Plan

- [x] Reload `AGENTS.md`.
- [x] Confirm a clean worktree and refresh `origin/main`.
- [x] Confirm local and remote `main` match the audited commit.
- [x] Create the topic branch.
- [x] Save this durable implementation ledger.
- [x] Record the maintenance work under `CHANGELOG.md` → `Unreleased`.

## Phase 1: Technical Documentation Corrections

### 1.1 Open OnDemand diagnostic shell

- [x] Rename the inaccurate OOD “attach” section.
- [x] Explain that `srun --jobid` starts a new job step.
- [x] Explain `--overlap` resource sharing and diagnostic-only use.
- [x] Keep `sattach` out of the user workflow.

### 1.2 CPU sanity checks

- [x] Qualify `nproc` in both Slurm and troubleshooting chapters.
- [x] Compare it with Slurm environment variables and `scontrol show job`.
- [x] Avoid treating any single value as universal allocation proof.

### 1.3 Environment storage policy

- [x] Make environment placement site-dependent.
- [x] Prefer site-approved persistent software/project storage when needed.
- [x] Allow scratch only when site retention and filesystem policy support it.
- [x] Keep reconstruction metadata in version-controlled or durable storage.
- [x] Apply the policy consistently to Conda, Miniconda, and venv examples.
- [x] Preserve the pinned Miniconda filename and SHA-256.

### 1.4 UTC scope

- [x] Label the partition table as a selected onboarding subset.
- [x] Label 64 GB as a field-note diagnostic starting value, not a minimum.
- [x] Keep current public partition facts and Jobstats guidance intact.

## Phase 2: Unified Release Contract

### 2.1 Local Make targets

- [x] Add `check-shell-syntax`.
- [x] Add `check-shell-lint` with an actionable missing-tool failure.
- [x] Add `check-whitespace`.
- [x] Add `release-check` while keeping `make check` fast.
- [x] Keep network-dependent dependency checks separate.

### 2.2 CI and contributor documentation

- [x] Make shell CI call the Makefile shell targets.
- [x] Distinguish routine `make check` from `make release-check`.
- [x] Align README, contributing guide, release checklist, PDF guide,
  best-practices chapter, PR template, and `AGENTS.md`.

## Phase 3: PDF Traceability

- [x] Pin the PDF workflow to `ubuntu-24.04`.
- [x] Generate `dist/build-toolchain.txt` after successful PDF QA.
- [x] Record OS, runner image, commit, tool/package versions, and PDF SHA-256.
- [x] Upload the PDF and toolchain record as one workflow artifact.
- [x] Pin the current official upload action by full commit SHA.
- [x] Describe the record as traceability, not signed provenance or permanent
  archival.

## Phase 4: Validation and PDF Review

- [x] Run the fast repository gate.
- [x] Run individual shell syntax and lint targets.
- [x] Run all Python unit-test modules directly.
- [x] Run the complete release gate.
- [x] Rebuild and validate the PDF twice for byte identity.
- [x] Run structural, font, text-extraction, rendering, and OCR checks.
- [x] Inspect every PDF page for layout defects.
- [ ] Confirm the toolchain-record hash matches the final PDF.
- [x] Review all scrub hits and public assets.

## Phase 5: Deferred Audit Hardening

### 5.1 Asset scope

- [x] Describe automation as PNG structure/metadata hygiene.
- [x] Enforce an explicit asset extension/path allowlist.
- [x] Cover uppercase and unexpected extensions with tests.
- [x] Retain mandatory human visual review and avoid OCR as a redaction claim.

### 5.2 External links

- [x] Add scheduled and manually dispatchable external-link monitoring.
- [x] Use retries, timeouts, and an explicit allowlist.
- [x] Keep the monitor separate from ordinary PR validation.

### 5.3 Placeholder and scrub scope

- [x] Add tests for `shell-session` and attribute-style shell fences.
- [x] Decide and document handling for indented code blocks.
- [x] Narrow scanner claims to repository policy coverage.
- [x] Evaluate a standard secret scanner without building a custom token catalog.

### 5.4 Markdown lint authority

- [x] Inspect current required-check/ruleset configuration.
- [x] Consolidate duplicate Markdown lint authority if safe.
- [x] Update workflow badges and documentation if consolidation occurs.

## Phase 6: Handoff

- [x] Confirm the final worktree contains only intended files.
- [ ] Commit the completed maintenance work.
- [ ] Push the topic branch.
- [ ] Copy the verified newest PDF to the Windows desktop.
- [ ] Report hashes, validation output, PDF page count, and remaining limits.
