# v1.2.1 Final Promotion To-Do

Status: in progress
Audited baseline: `0e000262a19ffaa4e9110427a3403f9464941ef7`

This checklist records the focused final-promotion work following the RC.2
audit. It deliberately excludes new cluster functionality, another PDF
toolchain redesign, and new live UTC checks.

## Phase 0: Guard and Plan

- [x] Confirm a clean worktree at the audited baseline.
- [x] Confirm the fetched `origin/main` matches the audited baseline.
- [x] Create the focused `agent/publish-v1.2.1-final` topic branch.
- [x] Record this implementation plan before changing implementation files.
- [x] Skip VPN and live-cluster checks because no administrative clarification
  will be provided and the July 30 validation remains current.

## Phase 1: Repository-Rooted Scrub Reads

- [x] Validate raw repository-relative paths without resolving symlinks.
- [x] Traverse every parent component from an open repository-root descriptor
  using directory-relative, no-follow opens.
- [x] Require regular final files and retain identity/race checks.
- [x] Apply the same boundary to ordinary worktree files, the scrub policy,
  site-exception targets, preflight inspection, and the final exception count.
- [x] Preserve index scanning, staged/worktree coverage, executable files,
  tab-bearing names, and deleted-worktree handling.
- [x] Add parent-link, broken-link, non-directory, race, external-read, policy,
  exception-target, and normal nested-file regression tests.
- [x] Align `AGENTS.md`, `SECURITY.md`, `CONTRIBUTING.md`, and the release
  checklist with the every-component boundary.

## Phase 2: Manifest-Derived Artifact Provenance

- [x] Derive the PDF path, document version, release status, safe artifact
  label, and distribution-status text from the validated manifest.
- [x] Reject unsafe workflow-output tokens.
- [x] Remove RC.2 hard-coding from the PDF workflow and toolchain record.
- [x] Give candidate and final manifest tests explicit fixtures.
- [x] Test candidate/final artifact labels, record wording, and unsafe values.

## Phase 3: Product-Neutral Accessibility Policy

- [x] Define reading-order and focus-order review by function rather than by
  one commercial product pairing.
- [x] Retain current NVDA plus desktop Acrobat Reader as a recommended
  reference environment, not an exclusive requirement.
- [x] Keep Read Out Loud classified as supplemental, not screen-reader
  evidence.
- [x] Require exact tools, versions, settings, artifact hash, tasks, results,
  reviewer profile, and untested limitations.
- [x] Distinguish an independent GitHub release from UTC-hosted or officially
  endorsed publication.
- [x] Preserve all no-certification and no-UTC-approval claim boundaries.

## Phase 4: Final v1.2.1 Metadata and Documentation

- [x] Select the actual publication date and matching deterministic build
  epoch.
- [x] Promote the manifest to final `1.2.1` and `UTC_HPC_Guide.pdf`.
- [x] Generate a new deterministic, engine-compatible trailer identifier.
- [x] Replace candidate PDF/OCR text with final-version text.
- [x] Move the completed changelog material into the dated `1.2.1` section.
- [x] Replace stale RC.2 wording in release-facing documentation and Make help.
- [x] Preserve the guide body, screenshots, July 30 field notes, and disclosed
  120/128 discrepancy.

## Phase 5: Final Artifact Validation

- [x] Run locked Node, scrub, asset, link, placeholder, shell, whitespace, and
  complete unit-test gates.
- [x] Run the separate external-link monitor. Its VPN-only Open OnDemand target
  remained DNS-inaccessible without VPN; all other monitored links passed.
- [x] Bootstrap and verify the locked PDF toolchain.
- [x] Require byte-identical repeated PDF builds.
- [x] Require structural, font, text, active-content, every-page render, OCR,
  and PDF/UA-2 veraPDF success.
- [x] Compare every final page at 200 DPI with the hash-verified RC.2 reference.
- [x] Record the exact manual accessibility/interoperability evidence completed
  and disclose untested pairings without inventing results.
- [ ] Verify final PDF, toolchain record, and veraPDF report hashes and state.

Validation evidence recorded before the publication workflow:

- Final PDF SHA-256:
  `41f20791a9577fa263ea5a6444bc25264b27c582bd033237542e41c68f904643`.
  The locked release gate passed reproducibility, structural/font/text and
  active-content checks, every-page rendering, OCR at 150 DPI, and veraPDF
  1.30.2 PDF/UA-2 validation for all 26 pages.
- The hash-verified RC.2 reference was
  `cb00a014d42a611d27ee4b71a72d199d8f05d13b9fabef0fffd32cf4dacb1ec5`.
  Independent 200-DPI rerenders matched the reviewed render sets. Page 1 was
  pixel-identical; page 2 differed only in final-version metadata; pages 3–26
  differed only in the repeated final-version header.
- Static structure inspection found `/Tabs /S` on all 26 pages, contiguous
  page structure parents, structured link annotations, the expected three
  figure alternatives, and no normalized structure-tree change from RC.2.
  Contact-sheet and representative original-resolution inspection found no
  reflow, clipping, overlap, misplaced figures, malformed code, or broken
  glyphs.
- No interactive keyboard traversal, reflow-mode review, screen-reader/viewer
  pairing, or other real assistive-technology interoperability test was
  performed. These untested pairings remain disclosed and no WCAG, universal
  assistive-technology, or UTC approval claim is made.

## Phase 6: Focused Pull Request

- [ ] Commit and push the complete implementation.
- [ ] Open a focused draft pull request against `main`.
- [ ] Report hashes, tests, PDF properties, veraPDF counts, visual review,
  manual evidence, limitations, and the absence of new VPN/HPC activity.
- [ ] Request review and resolve every actionable finding with revalidation.
- [ ] Require all hosted checks to pass on the final PR head.

## Phase 7: Publication

- [ ] Merge the approved pull request.
- [ ] Require all push-to-main checks to pass on the exact merge commit.
- [ ] Download and verify the exact main-push PDF, toolchain record, and
  veraPDF report.
- [ ] Confirm the main-push PDF is byte-identical to the reviewed final PDF.
- [ ] Tag the exact main commit as `v1.2.1`.
- [ ] Publish a non-prerelease GitHub release with the three verified assets.
- [ ] Verify the stable latest-download URL and published SHA-256.
- [ ] Confirm `main` and the local worktree are clean and synchronized.

## VPN Rule

No phase requires VPN. A new VPN/live-cluster check would only be reopened if
an authoritative UTC change made the published site guidance ambiguous. The
maintainer has confirmed that no such administrative clarification will be
provided for this release.
