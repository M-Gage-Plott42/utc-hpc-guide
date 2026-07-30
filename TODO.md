# v1.2.1 Final-Readiness Implementation Plan

This is the temporary durable work ledger for the independent audit of
`v1.2.1-rc.1`. Reload this file and `AGENTS.md` before resuming after a context
reset.

## Baseline, Scope, and Hold Points

- Audited and required baseline:
  `0558c3028fb246df252a0b79e4019cca930abd02`
- Working branch: `release/v1.2.1-final-readiness`
- Current stable release: `v1.2.0`
- Current source candidate: `v1.2.1-rc.1`
- Planned implementation candidate: `v1.2.1-rc.2`
- Scope: the public scrub defect, verified public UTC facts, a source-generated
  tagged PDF pipeline, accessibility validation, release documentation, and
  candidate review.
- This branch must not be pushed directly to `main`, merged, tagged, published
  as a release, or used to replace the stable release asset without a later,
  explicit user decision.
- Do not access UTC live systems until the user explicitly confirms the VPN is
  connected. Never submit a job or workload for this documentation check.
- Do not claim WCAG, PDF/UA, or UTC approval from automation alone.

The audit's statement that the inspected binary came only from a synthetic pull
request ref is now historical: the same `rc.1` source was also built
successfully by the post-merge `main` workflow at the audited commit. That
transient artifact still does not constitute a tagged or final release.

## Reconciled Research Decisions

- Pandoc `3.10.1` is the current immutable upstream release. Begin the
  implementation proof with that exact version and a verified upstream asset
  checksum.
- Pandoc's supported PDF-standard path is LuaLaTeX plus
  `pdfstandard=ua-2`; it requires TeX Live 2025 and a LaTeX kernel dated
  2025-06-01 or newer.
- Use a current, immutable TeX Live/LaTeX environment rather than the
  Ubuntu 24.04 Pandoc and TeX packages. Resolve and record an exact container
  digest or equivalently immutable official toolchain snapshot during the
  proof phase.
- The current `listings` package is marked incompatible with LaTeX tagging.
  Treat replacement of `--listings` as required unless a minimal proof
  establishes an upstream-supported, validator-clean configuration.
- Pandoc now supports reproducible LaTeX builds through `pdf-trailer-id`, or
  can derive that identifier from `SOURCE_DATE_EPOCH` and document content;
  the XeLaTeX-specific trailer special is no longer needed.
- Use the current stable veraPDF `1.30.2` release and its built-in `ua2`
  profile. Verify the official signature and record an exact checksum before
  pinning the installer.
- Automated structure checks and veraPDF cover machine-verifiable properties;
  reading order, alternative-text quality, table semantics, contrast, zoom,
  and assistive-technology behavior still require human review.
- The official UTC partition page confirms the audit's two missing
  restrictions. It also shows that the selected CPU-only EPYC row is missing
  its five-day maximum runtime; add that same-page fact for a complete row.
- The scrub defect is real but latent: the audited commit contains no tracked
  symbolic links or gitlinks and there is no evidence of a current leak.

Primary implementation references:

- <https://github.com/jgm/pandoc/releases/tag/3.10.1>
- <https://pandoc.org/demo/example33/19.1-latex.html>
- <https://latex3.github.io/tagging-project/documentation/usage-instructions>
- <https://latex3.github.io/tagging-project/tagging-status/>
- <https://docs.verapdf.org/cli/validation/>
- <https://software.verapdf.org/rel/1.30/>
- <https://utc.teamdynamix.com/TDClient/2717/Portal/KB/Article/163830/HPC-Cluster-Slurm-Partitions>

## Phase 0: Planning-Only Checkpoint

### 0.1 Baseline and research

- [x] Reload `AGENTS.md` and the full attached audit.
- [x] Confirm a clean worktree at the required baseline.
- [x] Fetch and confirm `origin/main` still matches the required baseline.
- [x] Confirm there is no open current pull request and no `v1.2.1` release.
- [x] Reproduce the untagged `rc.1` status and inspect the current build path.
- [x] Verify the audit's core claims against current upstream and UTC sources.

### 0.2 Durable handoff

- [x] Create the dedicated final-readiness branch.
- [x] Replace the obsolete completed ledger with this reconciled plan.
- [x] Limit this checkpoint's repository diff to `TODO.md`.
- [x] Commit and push the plan before beginning implementation.
- [x] Stop and return the plan to the user.

## Phase 1: Fail-Closed Tracked-Entry Scrub

### 1.1 Index-aware entry discovery

- [ ] Parse `git ls-files -s -z` records without losing NUL-safe paths, index
  modes, object IDs, or stages.
- [ ] Accept ordinary stage-zero regular and executable files.
- [ ] Reject mode `120000` with `tracked_symlink_not_allowed`.
- [ ] Reject mode `160000`, unknown modes, and unmerged stages with explicit
  unsupported-entry diagnostics.
- [ ] Preflight all index entries before loading the scrub policy or reading
  any tracked content.

### 1.2 No-follow worktree reads

- [ ] Distinguish a genuinely deleted regular file from a valid, broken,
  absolute, or relative symbolic link.
- [ ] Reject a worktree symbolic link that replaces an index regular file.
- [ ] Use `lstat` plus a no-follow open and regular-file `fstat` check so a
  final-component link cannot be followed between inspection and read.
- [ ] Apply the same safe read boundary to the policy file and site-exception
  stale checks.
- [ ] Avoid resolving, reading, or printing a rejected link target.
- [ ] Preserve scanning of unstaged edits to ordinary tracked files.
- [ ] Add a focused staged-versus-worktree divergence test and close any case
  where content present in the index could escape the release scrub.

### 1.3 Regression coverage and policy wording

- [ ] Retain the genuine-deletion behavior.
- [ ] Test valid, broken, absolute, and relative index symlinks.
- [ ] Test a materialized link blob, a worktree link replacing a regular file,
  a gitlink, an executable file, a tab-bearing path, and a nonzero index stage.
- [ ] Prove with an open/read spy that an external link target is never opened.
- [ ] Test policy-file and exception-target replacement links before policy
  parsing begins.
- [ ] Document the repository-wide tracked-symlink and unsupported-mode policy
  in `SECURITY.md` and contributor/release guidance.
- [ ] Record the correction under `CHANGELOG.md` → `[Unreleased]`.

Acceptance:

- The scanner never follows a rejected link.
- Ordinary staged content and unstaged worktree edits are both covered.
- Current `make scrub`, `make check`, and Quality Gate integration remain the
  single enforcement path; no duplicate workflow is added.

## Phase 2: UTC Public-Fact Precision

### 2.1 Official documentation corrections

- [ ] Preserve the selected-subset framing in `docs/sites/utc-mocshpc.md`.
- [ ] Add the official per-node CPU cap and five-day maximum runtime to the
  selected CPU-only EPYC row.
- [ ] Add the official one-GPU minimum and no-GPU-request scheduling behavior
  to the selected full-node EPYC row.
- [ ] Add a transparent July 2026 status line saying public documentation was
  rechecked and live cluster revalidation remains pending.

### 2.2 Field-note boundaries

- [ ] Keep the March 2026 observations explicitly historical until the live
  gate is completed.
- [ ] Distinguish the public Open OnDemand hostname from the exact dashboard
  route that still needs browser verification.
- [ ] Do not add QOS values, account names, allowlists, raw command output, or
  internal configuration.
- [ ] Keep the guide's independent, non-official disclaimer.

Acceptance:

- Every new public fact is supported by the official UTC partition page.
- No text implies that VPN/live validation has passed.

## Phase 3: Tagged-PDF Toolchain Proof

### 3.1 Immutable toolchain selection

- [ ] Add one small machine-readable PDF toolchain lock containing source URL,
  exact version, checksum or image digest, and expected executable version.
- [ ] Pin Pandoc `3.10.1` from its immutable upstream release.
- [ ] Select and pin a TeX Live 2025-or-newer environment with a supported
  LaTeX kernel and LuaLaTeX.
- [ ] Pin veraPDF `1.30.2`, verify its official signature, and record its
  installer checksum and `ua2` profile.
- [ ] Pin or inherit from an immutable image the Java runtime, fonts, qpdf,
  Poppler, Tesseract, and other downloaded build/QA tools.
- [ ] Add a checksum-verifying bootstrap path usable locally and in Actions;
  never execute an unverified download.

### 3.2 Minimal semantic proof

- [ ] Build a temporary fixture containing a title, headings, nested lists,
  a two-column table with header cells, a link, an image with alternative
  text, a page break, and a multiline code block.
- [ ] Invoke Pandoc's supported `pdfstandard=ua-2` mechanism with LuaLaTeX;
  do not inject `DocumentMetadata` after the document class.
- [ ] Compare code-block strategies without `listings` and select the smallest
  upstream-supported option that is tagged, readable, line-wrapped, and
  validator-clean.
- [ ] Inspect every package loaded by the generated Pandoc template and custom
  header, including the partially or currently incompatible verbatim,
  framing, caption, and table-footnote paths; add only narrowly scoped
  overrides proven necessary by the fixture.
- [ ] Confirm the fixture has `Tagged: yes`, `StructTreeRoot`, marked content,
  `Lang`, semantic tags, image alternative text, and a passing veraPDF `ua2`
  result.
- [ ] Stop and report an RC blocker if no approach preserves both semantic
  structure and readable wrapped code.

### 3.3 Reproducibility proof

- [ ] Remove the XeLaTeX/xdvipdfmx trailer special.
- [ ] Use Pandoc's documented `pdf-trailer-id` variable or its deterministic
  generated identifier instead of an engine-specific custom special.
- [ ] Preserve `SOURCE_DATE_EPOCH`, UTC build time, fixed source ordering, and
  the byte-identical two-build requirement.
- [ ] Demonstrate byte identity with the minimal fixture before migrating the
  full guide.

Acceptance:

- A pinned minimal build passes PDF/UA-2 and reproducibility checks before
  broad pipeline edits begin.

## Phase 4: Full Source and Build Migration

### 4.1 Semantic source preparation

- [ ] Replace the current three screenshot labels with context-meaningful
  alternative descriptions while preserving sanitization.
- [ ] Ensure the UTC table's first row is exposed as column headers.
- [ ] Verify headings, lists, and links remain native semantic source elements.
- [ ] Keep link text meaningful in context and avoid adding raw presentation
  markup unless the supported Pandoc path requires it.
- [ ] Mark repeated running headers, page numbers, rules, and purely decorative
  elements as artifacts.

### 4.2 LuaLaTeX build migration

- [ ] Switch `scripts/build_pdf.py` from XeLaTeX to the pinned LuaLaTeX path.
- [ ] Pass the supported PDF/UA-2 variable through Pandoc.
- [ ] Remove `--listings`, `\usepackage{listings}`, and `\lstset` unless the
  proof phase established a validator-clean supported replacement.
- [ ] Retain title, author, subject, `en-US`, US Letter, margins, fonts,
  Unicode-selectable text, table of contents, and source ordering.
- [ ] Preserve readable line wrapping for all narrative and Appendix B code.
- [ ] Keep the PDF free of forms, JavaScript, attachments, and encryption.

### 4.3 Release-state model

- [ ] Add a manifest-controlled candidate/final status so the same builder can
  render candidate or final labeling without another structural redesign.
- [ ] Set `release_target` to `1.2.1`, `document_version` to `1.2.1-rc.2`,
  and the candidate filename to `UTC_HPC_Guide_v1.2.1-rc.2.pdf`.
- [ ] Retain the required text `Release candidate for v1.2.1`.
- [ ] Generate any new deterministic identifier required by the new engine.
- [ ] Derive or validate Make and workflow output paths from the manifest so
  the build, hash, and uploaded filename cannot diverge.

Acceptance:

- The full guide builds as a visibly labeled review candidate with semantic
  structure and no unintended `rc.1` build-path references.

## Phase 5: Accessibility Gate and Tests

### 5.1 Structural checker

- [ ] Add `scripts/check_pdf_accessibility.py`.
- [ ] Require `Tagged: yes`, `StructTreeRoot`, `MarkInfo` with marked content,
  PDF 2.0, `Lang: en-US`, title, author, and the expected PDF/UA identifier.
- [ ] Traverse structure data and require representative heading, list, table,
  table-header, table-cell, link, figure, and code-reading-order structure.
- [ ] Require meaningful `Alt` entries for exactly the three OOD screenshots.
- [ ] Reject encryption, forms, JavaScript, embedded files, and attachments.
- [ ] Check for artifact-marked repeated header/footer content where it can be
  verified reliably; leave semantic quality to the manual checklist.

### 5.2 veraPDF integration

- [ ] Run the pinned veraPDF CLI explicitly with the `ua2` profile.
- [ ] Fail on every parser, validator, or conformance failure with no
  allowlist.
- [ ] Preserve the machine-readable report as
  `dist/verapdf-report.xml`.
- [ ] Parse the report to require exactly one compliant job and zero failed or
  exceptional jobs.

### 5.3 Unit and Make integration

- [ ] Add `tests/test_check_pdf_accessibility.py` with passing and failing
  structural/report fixtures or mocked tool boundaries.
- [ ] Cover missing tags, wrong language, missing alternative text, absent
  table headers, active content, malformed reports, and noncompliant veraPDF
  results.
- [ ] Add `test-pdf-accessibility` and `check-pdf-accessibility` Make targets.
- [ ] Add the new gate to `check-pdf` and therefore `release-check`.
- [ ] Keep qpdf, metadata, fonts/Unicode, extracted text, every-page render,
  every-page OCR, and two-build byte identity checks unchanged in strength.

Acceptance:

- Automated checks enforce machine-verifiable accessibility invariants without
  describing the result as WCAG or human certification.

## Phase 6: CI, Artifact, and Public Documentation Alignment

### 6.1 PDF workflow

- [ ] Replace apt-provided Pandoc/XeLaTeX with the checksum- or digest-pinned
  tagged-PDF toolchain.
- [ ] Verify every external artifact before use.
- [ ] Record Pandoc, LuaLaTeX, TeX Live, LaTeX kernel, Java, veraPDF, profile,
  fonts, QA tools, commit/ref, runner/image, and PDF SHA-256.
- [ ] Record `Tagged`, `StructTreeRoot`, `MarkInfo`, `Lang`, veraPDF result,
  reproducibility, structural QA, rendering, and OCR outcomes.
- [ ] Upload the `rc.2` PDF, `build-toolchain.txt`, and machine-readable
  veraPDF report together.

### 6.2 Contributor and release documentation

- [ ] Update `docs/pdf-guide.md`, `CONTRIBUTING.md`, `RELEASE_CHECKLIST.md`,
  `README.md`, `AGENTS.md`, the PR template, and Make help for the pinned
  LuaLaTeX/PDF/UA release path.
- [ ] Add a manual accessibility checklist covering heading/list navigation,
  reading order, table associations, link purpose, screenshot alternatives,
  artifacts, code blocks, contrast, 200% zoom/reflow, and screen-reader order.
- [ ] State that automated PDF/UA validation is necessary but not a WCAG 2.1
  AA certification.
- [ ] Keep the README stable link on `v1.2.0` and label `rc.2` artifacts as
  review-only.
- [ ] Keep all implementation notes under `CHANGELOG.md` → `[Unreleased]`.

Acceptance:

- Local instructions and Actions use the same locked toolchain and gates.
- The repository does not present `rc.2` as the stable or official guide.

## Phase 7: Candidate Validation, Review, and Public-Root Polish

### 7.1 Complete automated validation

- [ ] Run `npm ci`.
- [ ] Run `make check`.
- [ ] Run the separate live external-link monitor.
- [ ] Run shell syntax and ShellCheck targets.
- [ ] Run `make check-pdf` and the explicit veraPDF `ua2` command.
- [ ] Run `make release-check`.
- [ ] Run the complete Python unit-test discovery.
- [ ] Run `git diff --check`.
- [ ] Confirm two full builds are byte-identical.
- [ ] Confirm `pdfinfo` reports `Tagged: yes` and inspect the catalog for
  structure, marked content, and language.

### 7.2 Human PDF review

- [ ] Render every `rc.2` page at 200 DPI and inspect every page.
- [ ] Compare `rc.1` and `rc.2` renders and explain every material visual
  difference.
- [ ] Check clipping, margins, glyphs, blank pages, code wrapping, table
  continuation, screenshots, and Appendix B.
- [ ] Complete the manual accessibility checklist with reviewer, tool, date,
  and any limitations.
- [ ] Record page count and SHA-256.
- [ ] Stop with an RC report rather than weakening a gate if visual,
  reproducibility, OCR, or accessibility requirements conflict.

### 7.3 Public-root cleanup and review PR

- [ ] Transfer lasting outcomes to the changelog, release checklist, PDF guide,
  and focused PR body.
- [ ] Delete this temporary `TODO.md` before final candidate review unless a
  genuinely useful sanitized audit note is justified.
- [ ] Open one focused draft PR for `v1.2.1-rc.2`.
- [ ] Report baseline/head hashes, files and rationale, scrub regressions,
  UTC facts, full gates, page count/hash, reproducibility, tagging/catalog
  results, veraPDF profile/report, and manual review.
- [ ] State clearly that live UTC validation remains pending and the candidate
  is not for redistribution.
- [ ] Stop for user review without merging, tagging, publishing, or replacing
  the stable asset.

## Phase 8: VPN and Live UTC Gate — Explicit User Confirmation Required

### 8.1 Read-only validation

- [ ] Wait until the user explicitly confirms UTC VPN and Duo access is ready.
- [ ] Run only the audit-approved read-only scheduler summary, selected
  partition, memory-default, module, Jobstats, and filesystem-type commands.
- [ ] Test the public Open OnDemand root and dashboard routes in a browser.
- [ ] Do not run `srun`, `sbatch`, a workload, or a GPU allocation.

### 8.2 Sanitized decision record

- [ ] Record only the date and public-safe conclusions, never raw output,
  usernames, mount sources, account allowlists, or internal configuration.
- [ ] Retain, correct, or mark historical the memory and storage field notes
  according to the audit's decision rules.
- [ ] Stop final promotion if live values conflict with public UTC
  documentation until UTC HPC administration identifies the governing source.
- [ ] Obtain human UTC technical and accessibility review.

## Phase 9: Final v1.2.1 Promotion — Separate Tiny PR

Prerequisites: the `rc.2` review is accepted, the live gate has passed,
discrepancies are resolved, and human technical/accessibility review is
recorded.

### 9.1 Final metadata-only changes

- [ ] Update the sanitized live-verification statement.
- [ ] Resolve only factual discrepancies found at the live gate.
- [ ] Set the document version to `1.2.1`.
- [ ] Set the output filename to `UTC_HPC_Guide.pdf`.
- [ ] Replace candidate wording with `Version 1.2.1`.
- [ ] Add the dated `[1.2.1]` changelog section.
- [ ] Re-run every structural, visual, OCR, reproducibility, accessibility,
  PDF/UA, unit, shell, scrub, link, and whitespace gate.

### 9.2 Publication after explicit approval

- [ ] Merge only after user approval and passing required checks.
- [ ] Rebuild and review the successful artifact from the exact final `main`
  commit.
- [ ] Verify its SHA-256 against the reviewed local candidate.
- [ ] Tag the exact commit as `v1.2.1`.
- [ ] Publish the reviewed stable asset as the latest non-prerelease.
- [ ] Verify the stable latest-release URL serves byte-identical content.
- [ ] Present the result as an independently maintained practical onboarding
  guide unless UTC Research Technology formally adopts it.
