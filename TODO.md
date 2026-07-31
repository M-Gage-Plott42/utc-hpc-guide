# v1.2.1 Final Promotion To-Do

Status: complete — published as `v1.2.1`
Audited baseline: `0e000262a19ffaa4e9110427a3403f9464941ef7`

This checklist records the focused final-promotion work following the RC.2
audit. It deliberately excludes new cluster functionality, another PDF
toolchain redesign, and new live-site checks.

## Phase 0: Guard and Plan

- [x] Confirm a clean worktree at the audited baseline.
- [x] Confirm the fetched `origin/main` matches the audited baseline.
- [x] Create the focused `agent/publish-v1.2.1-final` topic branch.
- [x] Record this implementation plan before changing implementation files.
- [x] Leave the existing live-site evidence unchanged because no new
  administrative clarification will be provided.

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
- [x] Preserve the guide body, screenshots, and isolated site-note content and
  evidence boundaries without duplicating site facts outside `docs/sites/`.

## Phase 5: Final Artifact Validation

- [x] Run locked Node, scrub, asset, link, placeholder, shell, whitespace, and
  complete unit-test gates.
- [x] Run the separate external-link monitor and keep restricted-site results
  in site-note or pull-request evidence rather than this generic checklist.
- [x] Bootstrap and verify the locked PDF toolchain.
- [x] Require byte-identical repeated PDF builds.
- [x] Require structural, font, text, active-content, every-page render, OCR,
  and PDF/UA-2 veraPDF success.
- [x] Compare every final page at 200 DPI with the hash-verified RC.2 reference.
- [x] Record the exact manual accessibility/interoperability evidence completed
  and disclose untested pairings without inventing results.
- [x] Verify final PDF, toolchain record, and veraPDF report hashes and state.

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

- [x] Commit and push the complete implementation.
- [x] Open a focused draft pull request against `main`.
- [x] Report hashes, tests, PDF properties, veraPDF counts, visual review,
  manual evidence, limitations, and the absence of new live-site activity.
- [x] Request review and resolve every actionable finding with revalidation.
- [x] Require all hosted checks to pass on the final PR head.

## Phase 7: Publication

- [x] Merge the approved pull request.
- [x] Require all push-to-main checks to pass on the exact merge commit.
- [x] Download and verify the exact main-push PDF, toolchain record, and
  veraPDF report.
- [x] Confirm the main-push PDF is byte-identical to the reviewed final PDF.
- [x] Tag the exact main commit as `v1.2.1`.
- [x] Publish a non-prerelease GitHub release with the three verified assets.
- [x] Verify the stable latest-download URL and published SHA-256.
- [x] Confirm `main` and the local worktree are clean and synchronized.

## Publication Record

- Pull request
  [`#27`](https://github.com/M-Gage-Plott42/utc-hpc-guide/pull/27)
  merged as `3a937926455d0d17011df9dce0280843e1de4e78`.
- Tag `v1.2.1` points to that exact reviewed and validated merge commit.
- Main PDF workflow
  [`30599818138`](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/runs/30599818138)
  passed for the merge commit and produced artifact
  `utc-hpc-guide-v1.2.1-final-3a937926455d0d17011df9dce0280843e1de4e78`.
- Verified publication hashes:
  - `UTC_HPC_Guide.pdf`:
    `41f20791a9577fa263ea5a6444bc25264b27c582bd033237542e41c68f904643`
  - `build-toolchain.txt`:
    `0ec21cf4c6e34f22ae3fae3b9aff430c251fb8021e114487fe98214b9147d030`
  - `verapdf-report.xml`:
    `2129764669f72f42c046965ba2f163a6556040bda21e49f047928189b68733e1`
- The final veraPDF report records one compliant job, 1,727 passed rules,
  210,849 passed checks, no failed rules or checks, and no veraPDF
  exceptions.
- The final, non-prerelease
  [`v1.2.1` release](https://github.com/M-Gage-Plott42/utc-hpc-guide/releases/tag/v1.2.1)
  contains those three verified assets. The
  [stable PDF download](https://github.com/M-Gage-Plott42/utc-hpc-guide/releases/latest/download/UTC_HPC_Guide.pdf)
  was downloaded independently and matched the published PDF hash.
- This post-publication checklist closure intentionally advances `main`
  beyond the immutable `v1.2.1` tag; it does not alter the tagged source or
  published assets.

## Live-Site Rule

No phase requires new live-site access. Reopen live validation only if an
authoritative change makes the isolated site guidance ambiguous. No new
administrative clarification will be provided for this release.

## Parked Follow-Up: Polished PDF Redesign

Status: parked for the next work session

Audit date: July 31, 2026

Reviewed prototype PDF SHA-256:
`29ca3b095aade4bb267a781348154265b3b5c377f77aacd8b7a7e910ce5d3d2e`

Accept the prototype's visual design direction, but do not replace the
published PDF with that exact file. The 27-page LuaLaTeX prototype is visually
complete, has embedded Unicode fonts, includes every expected section,
screenshot, and template, and preserves the visible canonical content. It is
not a release artifact because it is an untagged PDF 1.7 build outside the
locked reproducible pipeline.

When work resumes:

- Port the design into the existing manifest-driven Pandoc/LuaLaTeX pipeline;
  retain the numbered chapters, `docs/sites/` page, examples, and manifest as
  the only canonical editable sources. Do not commit the aggregate root
  Markdown or TeX as a second hand-maintained copy.
- Preserve standard image alternatives through the tagged-PDF path. The
  prototype's empty Markdown image labels plus custom `fig-alt` attributes do
  not survive its direct TeX build, and the resulting figures have no
  PDF-level alternatives.
- Change the 12-point gold-on-white `Version 1.2.1` text. Its approximately
  1.75:1 contrast is insufficient, and the locked OCR gate misses that required
  phrase even though every page otherwise satisfies the OCR density threshold.
  Prefer navy text while keeping gold as a decorative accent.
- Restore the manifest-required `Appendix A:` and `Appendix B:` punctuation.
- Remove the duplicate logical page label `1` for the cover and first body
  page, and resolve the nonfatal `tocloft` redefinition warning.
- Produce the redesign only through the locked PDF 2.0/PDF/UA-2 toolchain,
  then run reproducibility, structure, veraPDF, every-page render, OCR, visual,
  and manual accessibility reviews on the exact final hash.

No VPN or new live-cluster validation is needed for this design migration.
Reopen live validation only under the existing live-site rule above.
