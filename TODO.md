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

- [ ] Validate raw repository-relative paths without resolving symlinks.
- [ ] Traverse every parent component from an open repository-root descriptor
  using directory-relative, no-follow opens.
- [ ] Require regular final files and retain identity/race checks.
- [ ] Apply the same boundary to ordinary worktree files, the scrub policy,
  site-exception targets, preflight inspection, and the final exception count.
- [ ] Preserve index scanning, staged/worktree coverage, executable files,
  tab-bearing names, and deleted-worktree handling.
- [ ] Add parent-link, broken-link, non-directory, race, external-read, policy,
  exception-target, and normal nested-file regression tests.
- [ ] Align `AGENTS.md`, `SECURITY.md`, `CONTRIBUTING.md`, and the release
  checklist with the every-component boundary.

## Phase 2: Manifest-Derived Artifact Provenance

- [ ] Derive the PDF path, document version, release status, safe artifact
  label, and distribution-status text from the validated manifest.
- [ ] Reject unsafe workflow-output tokens.
- [ ] Remove RC.2 hard-coding from the PDF workflow and toolchain record.
- [ ] Give candidate and final manifest tests explicit fixtures.
- [ ] Test candidate/final artifact labels, record wording, and unsafe values.

## Phase 3: Product-Neutral Accessibility Policy

- [ ] Define reading-order and focus-order review by function rather than by
  one commercial product pairing.
- [ ] Retain current NVDA plus desktop Acrobat Reader as a recommended
  reference environment, not an exclusive requirement.
- [ ] Keep Read Out Loud classified as supplemental, not screen-reader
  evidence.
- [ ] Require exact tools, versions, settings, artifact hash, tasks, results,
  reviewer profile, and untested limitations.
- [ ] Distinguish an independent GitHub release from UTC-hosted or officially
  endorsed publication.
- [ ] Preserve all no-certification and no-UTC-approval claim boundaries.

## Phase 4: Final v1.2.1 Metadata and Documentation

- [ ] Select the actual publication date and matching deterministic build
  epoch.
- [ ] Promote the manifest to final `1.2.1` and `UTC_HPC_Guide.pdf`.
- [ ] Generate a new deterministic, engine-compatible trailer identifier.
- [ ] Replace candidate PDF/OCR text with final-version text.
- [ ] Move the completed changelog material into the dated `1.2.1` section.
- [ ] Replace stale RC.2 wording in release-facing documentation and Make help.
- [ ] Preserve the guide body, screenshots, July 30 field notes, and disclosed
  120/128 discrepancy.

## Phase 5: Final Artifact Validation

- [ ] Run locked Node, scrub, asset, link, placeholder, shell, whitespace, and
  complete unit-test gates.
- [ ] Run the separate external-link monitor.
- [ ] Bootstrap and verify the locked PDF toolchain.
- [ ] Require byte-identical repeated PDF builds.
- [ ] Require structural, font, text, active-content, every-page render, OCR,
  and PDF/UA-2 veraPDF success.
- [ ] Compare every final page at 200 DPI with the hash-verified RC.2 reference.
- [ ] Record the exact manual accessibility/interoperability evidence completed
  and disclose untested pairings without inventing results.
- [ ] Verify final PDF, toolchain record, and veraPDF report hashes and state.

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
