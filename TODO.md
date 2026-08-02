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

## v1.2.2-rc.1 Polished PDF Redesign

Status: candidate ready for user inspection — local and hosted automation plus
visual review complete; real assistive-technology and final promotion remain
pending

Audit date: July 31, 2026

Reviewed prototype PDF SHA-256:
`29ca3b095aade4bb267a781348154265b3b5c377f77aacd8b7a7e910ce5d3d2e`

The audited 27-page prototype established the visual direction but remains an
untagged PDF 1.7 reference outside the locked pipeline. The redesign therefore
uses a new review-only `v1.2.2-rc.1` identity and does not alter the published
`v1.2.1` release.

### Phase 0: Guard and Candidate Boundary

- [x] Create the focused `agent/polished-pdf-redesign` topic branch at the
  audited `v1.2.1` post-publication baseline.
- [x] Move the manifest to review-only `v1.2.2-rc.1` metadata, output naming,
  deterministic epoch, and trailer identifier before changing PDF bytes.
- [x] Retain the numbered chapters, `docs/sites/` page, examples, manifest,
  header, template, and Lua filter as the canonical editable sources.
- [x] Keep the aggregate prototype Markdown, TeX, and PDF out of the commit.
- [x] Confirm no VPN or new live-cluster validation is required for this
  presentation-only migration.

### Phase 1: Tagging-Safe Visual Port

- [x] Lock the exact TeX Live Noto archive and require Noto Sans plus DejaVu
  Sans Mono to resolve from the pinned toolchain trees.
- [x] Port the navy, ink, link, code-rail, and restrained gold palette
  while keeping gold decorative rather than using it as low-contrast text.
- [x] Add the polished cover, two-column contents, running navigation,
  heading hierarchy, semantic code rails, and reviewed whitespace without
  replacing the standard tagging-aware document commands.
- [x] Avoid the prototype's tagging-incompatible or only partially compatible
  `titlesec`, `tocloft`, `needspace`, `listings`, `multirow`, and `tcolorbox`
  path.
- [x] Derive chapter, subsection, and appendix-template numbering during PDF
  assembly and apply reviewed screenshot widths through the PDF Lua filter.
- [x] Preserve the normal Markdown image alternatives through the three
  source-position `Figure` structures.

### Phase 2: Page, Semantic, and OCR Contracts

- [x] Give the physical cover the unique label `Cover`, use lowercase Roman
  contents labels, and restart Arabic numbering at body page `1`.
- [x] Require structure tab order on every page, unique contiguous structure
  parents, document-title display, and the exact manifest-owned logical role
  counts.
- [x] Keep cover, header, footer, rule, page-number, and code-rail decoration
  out of logical reading order as marked-content layout artifacts.
- [x] Require physical page 1 OCR to find the guide title and release-candidate
  label, in addition to complete-document and per-page-density OCR checks.
- [x] Add regression tests for candidate/final metadata, locked fonts,
  numbering, image sizing, page labels, structure contracts, and cover OCR.

### Phase 3: Completed Focused Validation

- [x] Run the focused build, manifest, toolchain-bootstrap, OCR,
  accessibility, and build-record unit suites.
- [x] Build the candidate twice with the locked toolchain and complete the
  reproducibility, structural, font, text, render, OCR, and PDF/UA-2 machine
  checks completed to date.

### Phase 4: Release and Human Review

- [x] Run the complete `npm ci` and `make release-check` gate on the final
  candidate worktree.
- [x] Render every page at high resolution and complete contact-sheet plus
  representative original-resolution visual inspection for reflow, clipping,
  overlap, malformed code, tables, figures, links, page labels, and contrast.
- [x] Copy the exact candidate PDF, and any deliberately generated inspection
  TeX, to the Windows Desktop for user review.
- [x] Record the exact reviewed PDF and local veraPDF report hashes, completed
  machine and visual evidence, and untested manual accessibility limitations.
- [x] Bind the commit-specific hosted toolchain record and veraPDF report
  hashes to the focused draft pull-request evidence after the first push.
- [x] Commit and push the complete candidate, then open a focused draft pull
  request and require every hosted check to pass.
- [x] Stop for user inspection and approval before merge or final promotion.

Local candidate evidence recorded August 1, 2026:

- `UTC_HPC_Guide_v1.2.2-rc.1.pdf` is 27-page US Letter PDF 2.0 with SHA-256
  `209193e9b0cadd583fa0c809d44c945fbb1ec49bd239578419636cbe38cd8964`.
  It is tagged, unencrypted, contains XMP metadata, has no forms or JavaScript,
  and embeds exactly four Unicode-mapped Noto Sans and DejaVu Sans Mono fonts.
- The complete release gate passed byte-identical repeated builds, qpdf,
  required-text extraction, all-page rendering, OCR at 150 DPI, exact cover
  OCR, exact logical-role counts, page contracts, and veraPDF 1.30.2 `ua2`.
  The local veraPDF report has SHA-256
  `aec1e8589025703050532f7121ca5be92f9616962775fd8b6304b26ef7a8aee5`
  and records one compliant job, 1,727 passed rules, 181,527 passed checks,
  and no failed rules, checks, or exceptions.
- Page labels progress from `Cover` to lowercase Roman `i` and Arabic `1`.
  Named destination `page.i` resolves once to physical page 2, `page.1`
  resolves once to physical page 3, all 27 pages use `/Tabs /S`, and structure
  parents are contiguous from 0 through 26.
- Every page was rerendered at 200 DPI. Contact-sheet and representative
  original-resolution review found no blank pages, reflow, clipping, overlap,
  malformed code, table or screenshot displacement, broken glyphs, or
  unintended low-contrast text. Gold remains decorative.
- The exact PDF was copied to the Windows Desktop as
  `UTC_HPC_Guide_v1.2.2-rc.1.pdf`; the Windows copy matches the reviewed
  SHA-256. No standalone inspection TeX was generated.
- The local traceability-record generator completed with both font packages,
  the explicit unversioned Noto state, and hashes for all eight configured font
  source files. Its commit-bound hosted artifact hash remains pull-request
  evidence rather than pre-commit evidence.
- No screen-reader/viewer pairing, keyboard traversal, reflow-mode review, or
  other real assistive-technology interoperability test was performed. The
  candidate makes no WCAG, universal assistive-technology, or UTC approval
  claim; that manual review remains a final-publication limitation.
- Draft pull request
  [`#28`](https://github.com/M-Gage-Plott42/utc-hpc-guide/pull/28) carries the
  commit-bound hosted artifact hashes. PDF, quality, ShellCheck, dependency
  review, and CodeQL checks all passed before the user-inspection handoff.

### Phase 5: Code Typography Bake-Off

Status: proof bundle ready for user selection — local and hosted validation
complete

- [x] Preserve the hash-verified RC.1 PDF as the comparison baseline and keep
  all typography proofs explicitly review-only.
- [x] Pin official static Regular and Bold sources for upstream Cascadia Mono
  and Fira Code, including release, archive, file, and license provenance.
- [x] Define reproducible DejaVu Sans Mono, Cascadia Mono, and Fira Code proof
  profiles with matched perceived size rather than a blind nominal-size swap.
- [x] Keep one visible glyph per literal character; use Cascadia Mono's
  no-ligature face and explicitly disable Fira Code common, discretionary,
  contextual, and TeX ligature features.
- [x] Manually wrap the three current source lines longer than 80 characters
  at valid shell boundaries, with explicit continuation syntax where needed.
- [x] Add an ambiguous-glyph proof containing `0 O o 1 l I | < > <= >= == !=
  -> -- _ ~ \ / ' " ( ) [ ] { }`.
- [x] Add exact extraction regression coverage for indentation and meaningful
  interior spaces rather than treating page-density OCR as clipboard proof.
- [x] Build each complete proof twice and require byte identity, the expected
  embedded font family and Unicode maps, structural checks, every-page
  rendering and OCR, exact semantic contracts, and veraPDF PDF/UA-2 success.
- [x] Inspect matched representative pages and all-page contact sheets at high
  resolution for glyph distinction, code size and leading, wrapping,
  clipping, pagination, figure/table placement, and overall visual balance.
- [x] Copy all passing proof PDFs to the Windows Desktop with unambiguous
  filenames and verify their hashes after copying.
- [x] Record proof hashes, validation evidence, and limitations; commit and
  push the implementation to draft pull request #28 and require hosted checks
  to pass before the selection handoff.
- [x] Stop for user selection. Promote only the chosen profile in a later
  PDF-changing candidate with a new formal identifier and complete revalidation.

The bake-off follows Google's current code-sample and command-line guidance:
prefer actual semantic code text, keep printable lines near 80 characters,
use valid continuation characters, and distinguish commands from output. No
VPN or live-cluster activity is required.

Local evidence recorded August 1, 2026:

- The standalone proof guard rebuilt the current base sources twice and
  reproduced the immutable 27-page RC.1 SHA-256
  `209193e9b0cadd583fa0c809d44c945fbb1ec49bd239578419636cbe38cd8964`.
  All proof covers say `TYPEFACE PROOF — NOT A RELEASE CANDIDATE`; none changes
  the formal candidate manifest or stable-release artifact.
- The exact proof sizes and verified regular-face metrics are DejaVu Sans Mono
  `9.0/11.5 pt` at `4.9219 pt` effective x-height, Cascadia Mono
  `9.5/11.8 pt` at `4.9170 pt`, and Fira Code `9.1/11.5 pt` at `4.9140 pt`.
  The locked gate reads these metrics from each pinned TTF and limits their
  spread to `0.02 pt`.
- The complete `npm ci` and `make release-check` gate passed 203 routine/unit
  checks, Bash syntax, ShellCheck, whitespace, base-candidate validation, and
  every proof gate. The proof-specific Ubuntu pins are
  `mupdf-tools=1.23.10+ds1-1build3` and
  `python3-fonttools=4.46.0-1build2`.
- Each proof is a tagged 28-page PDF 2.0 with Unicode-mapped embedded fonts,
  exact structure counts, all-page 150-DPI OCR, fixed-pitch extraction for
  four-space indentation and two-space separators, and MuPDF traces matching
  one default cmap glyph per literal character in both regular and bold rows:
  - DejaVu Sans Mono:
    `fbb826b7514a09a816973220f7b87543088052cac601b09a382e67679590b719`
  - Cascadia Mono:
    `99297697eab91ce8ee5ac743fda21e35767628e9cd57ddf06a51e7bdf31f9371`
  - Fira Code:
    `263371523226872363b9f67c311e6eac6d6d187f0292f53d1761545cea440534`
- Each veraPDF 1.30.2 `ua2` report records one compliant job, 1,727 passed
  rules, no failed rules/checks or exceptions, and respectively 185,534,
  185,748, and 185,526 passed checks for DejaVu, Cascadia, and Fira.
- All 84 rendered pages were reviewed in contact sheets, with seven matched
  representative-page comparisons and a 600-DPI ambiguous-glyph specimen.
  No blank page, clipping, overlap, malformed wrap, displaced screenshot or
  table, broken glyph, or code crowding was found. All three distinguish
  `0/O/o` and `1/l/I/|`; Cascadia is darkest/widest, Fira is lightest/openest,
  and DejaVu leaves the most right-margin reserve.
- One selection-relevant pagination difference remains visible: DejaVu and
  Fira leave the `B.4 slurm_tensorflow_gpu_probe.sbatch` heading at the bottom
  of physical page 25 while its code starts on page 26; Cascadia keeps that
  heading with its code on page 26. Apply a keep-with-next correction with the
  selected font if the chosen profile otherwise retains the orphan.
- The exact three passing PDFs were copied to the Windows Desktop with their
  unambiguous proof filenames; the destination SHA-256 values match the three
  hashes above.
- The offline gate verifies the recorded vendored font and license bytes but
  does not redownload the official release archives. For Cascadia's license it
  also reconstructs the upstream CRLF form and its one stripped trailing space
  from the policy-clean copy, then verifies the upstream byte hash. The lock
  retains release/archive URLs,
  archive digests and members, release commits, local digests, PostScript
  names, and license provenance for review.
- Locked Poppler extraction does not establish clipboard fidelity in every
  viewer. No screen-reader/viewer pairing, keyboard traversal, reflow-mode
  review, or other real assistive-technology interoperability test was
  performed; the proofs make no WCAG or universal-accessibility claim.
- Draft pull request
  [`#28`](https://github.com/M-Gage-Plott42/utc-hpc-guide/pull/28) carries the
  commit-bound proof-bundle hashes. Its PDF, quality, ShellCheck, dependency
  review, and CodeQL checks passed before this user-selection handoff.

### Phase 6: Publication Boundary

- [ ] After candidate approval, prepare a separate final-promotion change for
  `v1.2.2` and re-run all PDF-changing validation on its exact hash.
- [ ] Merge, tag, and publish only the reviewed final artifact; do not attach
  the candidate to a stable release or overwrite the existing `v1.2.1` asset.

No VPN or new live-cluster validation is needed for this design migration.
Reopen live validation only under the existing live-site rule above.

## v1.2.2-rc.2 Fira Canonicalization and Publication Plan

Status: Phase 4 complete — canonical wrapping, terminology, placeholders, and
transfer guidance corrected; Phase 5 has not started

Plan date: August 1, 2026

This is the complete resumption plan following the final independent audit and
the user's selection of the Fira Code proof. It supersedes the audit's
subjective Cascadia Mono preference but accepts the audit's actionable layout,
content, pipeline, and release-boundary findings as reconciled below.

### Guarded Inputs and Fixed Decisions

- `origin/main` must be
  `d5815af6c6574f4ddf2d0020422b91d82bd7ec95` before the focused work starts.
- The immutable typeface-evidence implementation commit is
  `e1c6f68822522dbf8e3d4c31e02dc4bde47bcf00`. It must remain an ancestor of
  the draft PR #28 branch; commits after it and before focused RC.2 work may
  change only this durable plan in `TODO.md`.
- The focused RC.2 branch must start from the clean polished-candidate commit
  `aefc676200acc09df044be9a5f7039b9e093d878`, not from the proof-matrix tip.
- The new branch name is `agent/v1.2.2-rc.2-fira`.
- Before any implementation edit on that branch, restore `TODO.md` from
  `origin/agent/polished-pdf-redesign` and commit that documentation-only
  transfer. Verify that the source branch differs from the immutable evidence
  commit only in `TODO.md`; stop if it carries later implementation files.
- The selected proof is Fira Code with SHA-256
  `263371523226872363b9f67c311e6eac6d6d187f0292f53d1761545cea440534`.
- Canonical fenced code uses Fira Code 6.2 at `9.1/11.5 pt`. Compact inline
  code remains DejaVu Sans Mono, and prose plus headings remain Noto Sans.
- Retain both official static Fira Code Regular and Bold TTFs and their OFL
  license/provenance. Validate both faces in a test-only fixture, but do not
  force an otherwise unused Bold face into the release PDF.
- Disable all ligature and contextual-substitution paths with exactly
  `RequiredOff`, `CommonOff`, `ContextualOff`, `DiscretionaryOff`,
  `HistoricOff`, and `TeXOff`, plus raw features `-calt`, `-liga`, `-clig`,
  `-dlig`, `-hlig`, `-rlig`, and `-tlig`.
- Fira Code's `ContextualOff` and `-calt` controls are essential; common
  ligature controls alone are insufficient for its programming substitutions.
- Do not use `needspace`, `listings`, `minted`, `tcolorbox`, or another new
  code-layout package. Preserve the current tagging-aware Pandoc/LuaLaTeX
  design.
- Do not change UTC operational facts, access the UTC VPN or HPC, submit a
  Slurm job, merge PR #28, replace the stable `v1.2.1` asset, tag a release,
  or publish during RC.2 implementation.

### Reconciled Audit Record

- The empty Appendix B rail is real, but its direct root cause is synthetic
  source assembly: the opening fence and script are separate sequence entries
  joined with two newlines. The Lua filter then preserves that invented blank
  line and `\everypar` decorates it. Fix the assembly boundary first; merely
  moving the rail command does not remove the synthetic blank.
- The Access/SSH chapter opener is separated from its first subsection. The
  Fira proof also separates the B.4 heading from its shebang. Rebuild after the
  assembly fix because B.4 may resolve when the invented blank disappears,
  then enforce deterministic page contracts.
- Inline-code styling in Markdown headings produces terminal-looking,
  excessively wrapped contents entries. Change only the PDF heading rendering;
  preserve source Markdown, literal text, anchors, outlines, and semantics.
- The proof matrix is valid experiment evidence but is not an appropriate
  permanent release pipeline. The three-profile orchestration and unselected
  fonts must not enter the focused RC.2 branch.
- The PR #28 body is stale, but its latest evidence comment already records
  the current head, synthetic merge, 203 checks, artifact identifiers, proof
  hashes, and seven successful hosted checks. A final transition comment is
  needed only after the replacement PR exists.
- The core guide still needs a near-first-use Slurm definition, preferred
  `Slurm` capitalization in ordinary prose/headings, a prose-versus-shell
  placeholder explanation, removal of unused `<group>`, and compact `scp`
  examples.
- Automated PDF/UA-2 and veraPDF success covers machine-verifiable checks
  only. Preserve the existing disclosure of untested screen-reader/viewer,
  keyboard-traversal, reflow, WCAG, universal-assistive-technology, and UTC
  approval claims.

### Phase 0: Guard, Evidence, and RC.2 Boundary

- [x] Confirm the worktree and index are clean before fetching or branching.
- [x] Fetch `origin` with pruning and verify the guarded commits above. Require
  `e1c6f68822522dbf8e3d4c31e02dc4bde47bcf00` to be an ancestor of
  `origin/agent/polished-pdf-redesign`, and require
  `git diff --name-only e1c6f68822522dbf8e3d4c31e02dc4bde47bcf00..origin/agent/polished-pdf-redesign`
  to report only `TODO.md`. Stop rather than rebasing, merging, or guessing if
  either guard fails.
- [x] Create `agent/v1.2.2-rc.2-fira` directly from
  `aefc676200acc09df044be9a5f7039b9e093d878`.
- [x] Run
  `git restore --source origin/agent/polished-pdf-redesign -- TODO.md`, verify
  that the resulting worktree change is only `TODO.md`, and commit the durable
  plan transfer before implementation. This keeps the complete plan and proof
  evidence on the clean-base branch without importing proof implementation.
- [x] Keep PR #28 open, draft, unmerged, and unchanged while RC.2 is built so
  its proof artifacts and comments remain reachable as comparison evidence.
- [x] Before any other PDF-changing edit, promote the manifest boundary to:
  - `release_status`: `candidate`
  - `release_target`: `1.2.2`
  - `document_version`: `1.2.2-rc.2`
  - `output_filename`: `UTC_HPC_Guide_v1.2.2-rc.2.pdf`
- [x] Select a new deterministic source epoch and engine-compatible trailer
  identifier, and update candidate-owned required PDF and OCR text from RC.1
  to RC.2.
- [x] Keep the current `1.2.2` changelog material under `[Unreleased]`; do not
  assign a stable release date during candidate work.

Phase 0 evidence recorded August 1, 2026:

- The pre-branch worktree and index were clean. After a pruned fetch,
  `origin/main` was exactly
  `d5815af6c6574f4ddf2d0020422b91d82bd7ec95`, and
  `e1c6f68822522dbf8e3d4c31e02dc4bde47bcf00` remained an ancestor of
  `origin/agent/polished-pdf-redesign`. The guarded range changed only
  `TODO.md`.
- `agent/v1.2.2-rc.2-fira` was created directly from
  `aefc676200acc09df044be9a5f7039b9e093d878`. The exact source-branch
  `TODO.md` was transferred alone and committed before implementation as
  `acf61dc221d17d5f895a5f42da1e943026f71f9a`.
- PR #28 remained open, draft, unmerged, and unchanged at
  `77ebf10cd43fe9dfa3b88a4bb2ee31127be0e37c`.
- The manifest now identifies review-only `v1.2.2-rc.2`, writes
  `UTC_HPC_Guide_v1.2.2-rc.2.pdf`, and uses deterministic epoch
  `1785628800` (`2026-08-02 00:00:00 UTC`) with derived trailer identifier
  `f4ea8ec5e9282eabbe16cc4597130260`. Exact RC.2 text is required in PDF
  extraction and physical-cover OCR.
- The `1.2.2` changelog remains under `[Unreleased]`. No VPN/HPC activity,
  proof implementation, merge, tag, release, or stable-asset change occurred.
- `npm ci` completed with no reported vulnerabilities, the locked PDF
  toolchain verified, and `make release-check` passed 162 tests plus Bash,
  ShellCheck, reproducibility, qpdf, four-font, every-page 150-DPI OCR, and
  veraPDF 1.30.2 `ua2` gates. The 27-page boundary-validation build was
  byte-identical at SHA-256
  `c9cefd2cf74bfff086e60557794aa5ba03f873ac310b745f06fd78d5f9853072`;
  it is not the later selected-Fira inspection candidate.

### Phase 1: Promote Only the Selected Fira Profile

- [x] Bring over only `FiraCode-Regular.ttf`, `FiraCode-Bold.ttf`, the OFL
  license, and the Fira 6.2 source entry from the proof lock.
- [x] Preserve the exact upstream release tag and commit, archive URL, archive
  byte size and SHA-256, archive members, local file sizes and SHA-256 values,
  PostScript names, license URL, license size, and license SHA-256.
- [x] Fold the selected-font provenance and permanent MuPDF/fontTools host
  requirements into the canonical toolchain contract and build record; do not
  retain a multi-profile proof lock.
- [x] Replace proof-parameterized font selection with one focused canonical
  Fira code-font configuration at `9.1/11.5 pt`.
- [x] Apply the complete named and raw ligature denylist above to the canonical
  Fira family and reject an unresolved or missing option.
- [x] Keep DejaVu Sans Mono as the inline-code family and Noto Sans as the
  prose/heading family; document this as an intentional semantic distinction.
- [x] Add a small test-only semantic font fixture that exercises Regular and
  Bold Fira, the ambiguous-glyph string, indentation, and interior spaces.
  Never append that fixture to the canonical guide or upload it as a release
  artifact.
- [x] Require the release PDF to embed exactly the Unicode-mapped faces its
  canonical content actually uses. Validate unused Fira Bold in the fixture
  rather than forcing it into the release artifact.

Phase 1 evidence recorded August 1, 2026:

- The branch contains only the official Fira Code 6.2 static Regular and Bold
  TTFs and exact upstream OFL bytes. Their SHA-256 values are respectively
  `5992ab9640e2df491b2f609467b1de60e8bc39b2c28db184342a0592d98f6117`,
  `41f6554e845e2f5b70adad3950122334b866aac436793b7742ade600067701be`,
  and `1d41e10031ab125302780a05ec4c91d218e47db0c7e37cf315cce5e608cdc25c`.
  No Cascadia, enlarged-DejaVu, specimen, matrix, proof configuration, or
  proof orchestration file was transferred.
- The canonical lock records release tag `6.2`, upstream commit
  `eee6db993696aba61ff4eef03698e2987d79910c`, the 2,462,987-byte release
  archive and SHA-256
  `0949915ba8eb24d89fd93d10a7ff623f42830d7c5ffc3ecbf960e4ecad3e3e79`,
  exact archive members, local sizes and hashes, PostScript names, and license
  provenance. Its SHA-256 is
  `e6821c9177e7160333a273c8b466fbb87be4b35ef9a9dc9525dfab2412bfce31`.
- Fenced code now uses Fira Code at `9.1/11.5 pt`; compact inline code remains
  DejaVu Sans Mono and prose/headings remain Noto Sans. Every named and raw
  ligature-disable option is generated from the validated lock, and a missing
  `ContextualOff`, `-calt`, or other required control fails closed.
- The isolated one-page fixture was tagged PDF 2.0 and passed qpdf, exact
  Regular/Bold Unicode font checks, exact four-space indentation and two-space
  extraction, one default cmap glyph for each of the 59 literal characters in
  both faces, and one clean veraPDF 1.30.2 `ua2` job. It was generated only in
  a temporary directory and was not added to the guide or release artifacts.
- `npm ci` reported no vulnerabilities. The final lock-attested toolchain
  verified seven Ubuntu packages and all pinned tools. `make release-check`
  passed 164 routine/unit tests, Bash, ShellCheck, reproducibility, qpdf,
  every-page 150-DPI OCR, structural checks, and veraPDF PDF/UA-2. The
  separate complete discovery run passed all 171 tests, including the focused
  selected-font and fixture failure paths. The
  canonical 27-page PDF was byte-identical at SHA-256
  `1e1a9b02b0587eeb5db395c3c059d87cba15890c9ecbd1782348cb8e57a4cbd2`
  and embedded exactly Noto Sans Regular/Bold, DejaVu Sans Mono Regular/Bold,
  and Fira Code Regular. Fira Bold appeared only in the fixture.
- A real local build-record smoke run captured the complete selected-font
  provenance, configuration, host-package pins, tool versions, and both face
  hashes. No Phase 2 assembly or rail change, VPN/HPC activity, PR transition,
  merge, tag, release, Windows copy, or stable-asset change occurred.

### Phase 2: Correct Appendix Assembly and Code Rails

- [x] Assemble each generated Appendix B fenced block without a blank line
  between the opening fence and the tracked script's first source line.
- [x] Add an assembly regression requiring every Appendix B block to begin
  immediately with its tracked `#!/bin/bash -l` line.
- [x] Remove `\everypar{\GuideCodeRail}` from the `GuideCode` environment.
- [x] Have the Lua code-line transformation attach `\GuideCodeRail` directly
  to each actual generated source-line paragraph.
- [x] Preserve a rail for a deliberate blank line that exists in tracked
  source, but reject invented leading or trailing blank lines.
- [x] Keep every rail inside a layout-artifact marked-content boundary and
  outside logical reading order while retaining the encompassing semantic
  `Code` structure.
- [x] Add regressions proving one rail per real source line, no synthetic
  leading rail, unchanged first-line alignment, and exact extraction of
  indentation and meaningful interior spaces.
- [x] Rebuild RC.2 after this root fix before adding pagination controls; record
  whether the B.4 orphan resolves naturally.

Phase 2 evidence recorded August 1, 2026:

- Appendix B now assembles each heading, opening fence, tracked source, and
  closing fence as one source-exact block. All four blocks begin immediately
  with the tracked `#!/bin/bash -l`; empty sources, incorrect shebangs, and
  leading or trailing blank source lines fail closed.
- `GuideCode` no longer uses `\everypar`. The Lua filter enters horizontal
  mode and attaches exactly one `\GuideCodeRail` to each real source-line
  paragraph, including an explicit `\strut` for a deliberate interior blank
  line. The existing rail macro remains a zero-width `\llap` inside a layout
  artifact, while the enclosing code remains in the semantic `Code`
  structure.
- Dynamic Pandoc-filter tests require one direct rail for each of five fixture
  lines and reject invented edge blanks. Locked Poppler extraction preserves
  representative four- and eight-space indentation and meaningful two-space
  separators. MuPDF traces place all four Appendix shebangs at `59.438 pt` in
  both the Phase 1 reference and the corrected build, proving unchanged
  first-line alignment.
- `npm ci` reported no vulnerabilities, the locked PDF toolchain verified,
  the focused PDF assembly suite passed 28 tests, complete discovery passed
  all 176 tests, and `make release-check` passed 169 routine/unit tests plus
  scrub, asset, link, placeholder, Bash, ShellCheck, reproducibility, qpdf,
  exact extraction, every-page 150-DPI OCR, structural, and veraPDF 1.30.2
  `ua2` gates.
- The corrected canonical PDF remains 27 pages and is byte-identical across
  repeated builds at SHA-256
  `e90ea8587fe703a9ba9eef00e07fa112e7907f2828ec190448d736ecc4a1ea21`.
  It embeds the expected five Unicode-mapped font faces, passes OCR on every
  page, retains 2,577 validated structure roles, and produces one compliant
  veraPDF job.
- B.4 and its first `#!/bin/bash -l` now share physical page 25, so the
  selected-Fira orphan resolved naturally after the assembly correction. No
  Phase 3 pagination control was introduced. No VPN/HPC activity, PR change,
  merge, tag, release, Windows copy, or later-phase implementation occurred.

### Phase 3: Heading Pagination and PDF-Only Heading Typography

- [x] Implement a tagging-safe chapter-opener keep rule with core LaTeX
  penalties/no-break controls, not a new package or a boxed long code block.
- [x] Require each top-level chapter heading, its short introductory paragraph,
  and its first subsection heading to share a physical page. If a source shape
  cannot satisfy that bounded opener, fail the contract and resolve that case
  explicitly rather than silently weakening the rule.
- [x] Require each B.1 through B.4 script heading to share a physical page with
  its first nonblank source line.
- [x] Require that no heading end a page followed only by a code rail or other
  decoration.
- [x] Add deterministic text-to-page mapping tests for every chapter opener,
  every Appendix B heading/shebang pair, and specifically `2. Access and SSH`
  with `2.1 Account and Network Prerequisites`.
- [x] For PDF output only, convert inline `Code` nodes contained in `Header`
  nodes to ordinary literal heading text without interpreting punctuation or
  changing spaces.
- [x] Assert unchanged heading text, identifiers, destinations, outline text,
  hierarchy, and structure roles while requiring the normal Noto heading face.
- [x] Render the complete two-column contents page after the transformation.
  Shorten only entries that still wrap excessively; do not shrink the whole
  contents page to accommodate isolated long entries.
- [x] Reject heading-only bottoms, excessive new whitespace, three-line TOC
  entries, terminal-style heading text, or new clipping and overlap.

Phase 3 evidence recorded August 1, 2026:

- The PDF Lua filter now wraps each bounded H1-through-first-H2 opener in the
  core LaTeX `samepage` environment and emits `\nopagebreak[4]` after every
  H2. It preserves the standard tagging-aware section commands and adds no
  heading, code-box, or page-measurement package. A chapter whose first real
  body block is not a paragraph, or which lacks a first H2, fails closed.
- All 11 chapter openers satisfy the physical-page contract. Their H1/H2 page
  pairs are respectively `3/3`, `4/4`, `5/5`, `7/7`, `9/9`, `11/11`,
  `14/14`, `15/15`, `17/17`, `19/19`, and `23/23`. In particular,
  `2. Access and SSH`, its introduction, and
  `2.1 Account and Network Prerequisites` now share physical page 4 without
  leaving excessive whitespace on physical page 3.
- B.1, B.2, B.3, and B.4 share their first tracked `#!/bin/bash -l` lines on
  physical pages 23, 24, 25, and 25. MuPDF structured-text checks also require
  same-page semantic text below every one of the 82 source headings, excluding
  running headers, footers, and decorative rails.
- For LaTeX/PDF output only, all 11 inline `Code` nodes found in source
  headings become literal `Str` nodes. Source Markdown, literal text,
  punctuation, spacing, 82 unique identifiers, 11-H1/71-H2 hierarchy, and the
  exact 82-entry outline remain unchanged. Every body heading uses only Noto
  Sans Bold. The 2,577-role logical structure, including all 49 semantic
  `Code` roles, is unchanged.
- The complete contents remains one two-column physical page. It uses only
  Noto Sans Regular/Bold, retains every outline entry, and has no entry beyond
  two visual lines. The release PDF now embeds exactly its four used
  Unicode-mapped faces: Noto Sans Regular/Bold, DejaVu Sans Mono Regular, and
  Fira Code Regular; DejaVu Sans Mono Bold remains toolchain-provenanced but is
  no longer forced into the PDF solely by terminal-styled headings.
- `npm ci` reported no vulnerabilities. The focused build suite passed 31
  tests, complete discovery passed all 179 tests, and `make release-check`
  passed 172 routine/unit tests plus scrub, asset, link, placeholder, Bash,
  ShellCheck, reproducibility, qpdf, exact extraction, heading/outline/font,
  every-page 150-DPI OCR, structural, and veraPDF 1.30.2 `ua2` gates.
- The 27-page canonical PDF is byte-identical across repeated builds at
  SHA-256
  `49e19ef5a9548f10d2e6acd2a078236217df3890e90ff1230d718afe4e17d21e`.
  Focused 160-DPI review of the complete contents, the Overview-to-Access
  transition, and physical pages 23–25 found no clipping, overlap, malformed
  heading, excessive gap, empty rail, or decoration orphan. The all-page
  Phase 6 visual and manual-accessibility reviews remain pending.
- No canonical Markdown content, UTC fact, field-note boundary, screenshot,
  VPN/HPC state, PR, merge, tag, release, Windows copy, or later-phase
  implementation changed.

### Phase 4: Canonical Source Wrapping and Focused Usability Edits

- [x] Replace the long `sacct --format` argument in canonical Markdown with the
  reviewed readable `SACCT_FIELDS` composition and quoted use.
- [x] Replace the long `pip download` line in canonical Markdown with the
  reviewed shell continuation, ending every nonfinal command line with `\`.
- [x] Keep the 83-character immutable Miniconda SHA-256 assignment on one line.
  Record it as the sole exact code-width exception because splitting an opaque
  digest is less understandable and more error-prone for beginners.
- [x] Apply the approximately 80-character width audit to the formal candidate,
  not through hidden proof-time replacements. Reject any new or unexplained
  exception.
- [x] Add near first use: `Slurm is the cluster workload manager and job
  scheduler that allocates compute resources and queues jobs.`
- [x] Use `Slurm` in current ordinary prose and headings. Preserve exact
  `SLURM_*` environment variables, code, source output, historical quotations,
  URLs, and immutable prior-release evidence.
- [x] Add one compact terms sentence defining HPC, SSH, OOD, CPU, and GPU; do
  not add a long glossary.
- [x] Explain that angle-bracket placeholders are prose/path notation, while
  runnable shell uses `REPLACE_WITH_*` because unquoted angle brackets are
  shell redirection operators.
- [x] Remove `<group>` because it has no use in the current guide.
- [x] Under Transfer Methods, add one-file `scp` upload and download examples
  using the existing placeholder variables, then place the incremental
  `rsync` examples underneath and remove the thin standalone `rsync` section.
- [x] Keep every edit cluster-agnostic. Do not change the UTC table, field-note
  boundaries, screenshots, site facts, or live-validation evidence.

Phase 4 evidence recorded August 2, 2026:

- The two formal-candidate command edits are the exact token-preserving forms
  reviewed during the bake-off: `SACCT_FIELDS` is composed in two readable
  assignments and passed quoted to `sacct`, while `pip download` uses a valid
  shell continuation with its sole nonfinal line ending in `\`. The focused
  regression evaluates the composed accounting field list and compares the
  wrapped pip token stream with the original commands.
- The assembled canonical Markdown now has no fenced-code line above 80
  characters except the exact 83-character immutable
  `INSTALLER_SHA256=...` assignment. The focused regression allows that one
  full-digest line and rejects any new or changed exception; no hidden proof
  transform participates in the formal build.
- The overview now defines Slurm near first use and defines HPC, SSH, OOD, CPU,
  and GPU in one compact sentence. Current core prose and headings use the
  preferred `Slurm` spelling while exact `SLURM_*` code tokens remain intact.
  Placeholder guidance distinguishes prose/path angle brackets from runnable
  `REPLACE_WITH_*` shell markers and removes the unused `<group>` entry.
- Transfer Methods now gives explicit one-file `scp` upload and download
  examples in documented source-then-destination order, followed by the
  incremental `rsync` examples using the same `HPC_USER`, `LOGIN_HOST`, and
  `SCRATCH_PATH` variables. The standalone `rsync` subsection was removed and
  the manifest's exact TOC-derived heading, link, list-item, code, TOCI, and
  reference role counts were updated to the resulting structure.
- `npm ci` found no vulnerabilities. It emitted the known nonfatal engine
  warning because local Node `v24.14.0` precedes the transitive `ini@7.0.0`
  `^24.15.0` range; the locked install and all repository checks completed.
  The focused build/OCR suite passed 39 tests, complete discovery passed all
  180 tests, and the final `make release-check` passed 173 routine/unit tests,
  scrub, assets, local links, placeholders, Bash syntax, ShellCheck,
  whitespace, deterministic double build, qpdf, exact text/font/heading QA,
  all-page 150-DPI OCR, structural checks, and veraPDF 1.30.2 `ua2`.
- The canonical PDF remains a 27-page tagged, unencrypted US Letter PDF 2.0
  with exactly Noto Sans Regular/Bold, DejaVu Sans Mono Regular, and Fira Code
  Regular embedded with Unicode maps. Repeated builds are byte-identical at
  SHA-256
  `3aba1172a34e3ae28a2290143fc3e132c2e383e11b1276aa8643017eac58b4e3`.
  It has 81 validated headings and 2,596 validated structure roles. The
  veraPDF report SHA-256 is
  `38baa40ffa3b196660b0718e3bd568514d68bb8e1117cf69d0fb069a857f8a99`
  and records one compliant job, 1,727 passed rules, 182,043 passed checks,
  and no failed rules or checks.
- Focused 160-DPI review of physical pages 2, 3, 6, 8, and 13 through 15 found
  a complete one-page contents, legible new definitions, intact Slurm
  headings, valid accounting and pip continuations, safe transfer-block page
  flow, and no clipping, overlap, malformed rail, broken glyph, or heading
  orphan. No `docs/sites/` content, UTC table, field-note boundary,
  screenshot, live-validation evidence, VPN/HPC state, PR, merge, tag,
  release, Windows copy, or later-phase implementation changed.

### Phase 5: Permanent QA, Pipeline, and Documentation Cleanup

- [x] Do not bring over Cascadia files, the larger DejaVu proof profile,
  `font-proof-specimen.md`, the three-profile matrix/configuration, proof
  source transforms, proof orchestrator, proof-only checksum bundle, proof
  Make targets, or proof artifact upload.
- [x] Retain only focused reusable selected-font logic for exact source files
  and license, provenance, PostScript names, embedded fonts, Unicode maps,
  default-cmap glyphs, extraction, and width checks.
- [x] Require the fixture's Regular and Bold rows to map every literal character
  in `0 O o 1 l I | < > <= >= == != -> -- _ ~ \ / ' " ( ) [ ] { }` to one
  visible default glyph, with no multi-character ligature or contextual
  alternate.
- [x] Require exact four-space indentation and meaningful two-space separators
  in locked Poppler extraction, while documenting that this does not prove
  clipboard behavior in every PDF viewer.
- [x] Retain PDF 2.0, PDF/UA-2, page-label, destination, `/Tabs /S`, contiguous
  structure-parent, exact structure-role, alt-text, link, table, figure,
  metadata, font, active-content, render, OCR, and reproducibility contracts.
- [x] Add the rail, chapter-opener, Appendix-heading, heading-font, canonical
  width, and selected-Fira contracts to routine/unit and release gates.
- [x] Make `release-check` validate only the canonical RC.2 and the small
  test-only selected-font fixture; it must not build three full guide proofs.
- [x] Make CI upload only the manifest-derived canonical candidate, canonical
  build record, and canonical veraPDF report.
- [x] Update README, CONTRIBUTING, `docs/pdf-guide.md`, CHANGELOG,
  RELEASE_CHECKLIST, Make help, workflow comments, toolchain records, and this
  TODO so no active instruction treats the bake-off matrix as permanent.
- [x] Retain the historical proof hashes and PR #28 link as evidence, clearly
  labelled as completed review-only inputs rather than release artifacts.

Phase 5 evidence recorded August 2, 2026:

- The focused permanent implementation adds no Cascadia bytes, expanded
  DejaVu profile, proof specimen, comparison matrix, proof transform,
  orchestrator, proof checksum bundle, proof Make target, or proof upload.
  README and `docs/pdf-guide.md` preserve only the three historical proof
  hashes and PR #28 link, explicitly as completed review-only evidence.
- `scripts/check_code_width.py` enforces the 80-character canonical fenced-code
  contract and permits only the exact 83-character immutable Miniconda digest
  line. The canonical assembler applies the exception only when the relevant
  core source is present, while arbitrary fixtures receive no exception.
- The temporary semantic fixture checks the exact official Fira Code 6.2
  Regular/Bold files, license, provenance, PostScript names, embedded Unicode
  maps, disabled required/common/contextual/discretionary/historic/TeX
  ligatures, and raw OpenType feature denylist. Each face maps the complete
  59-character ambiguity row to one visible default-cmap glyph per source
  character; synthetic regressions reject contextual alternates and
  multi-character substitutions.
- Locked Poppler extraction must preserve the fixture's exact four-space
  indentation and meaningful two-space separator. Contributor and PDF-build
  documentation explicitly state that this does not prove clipboard behavior
  in every viewer.
- `make check` now includes focused code-width and selected-font suites.
  `make check-pdf` and therefore `make release-check` build only the canonical
  PDF plus the small fixture in temporary storage. The workflow uploads exactly
  the canonical PDF, `build-toolchain.txt`, and `verapdf-report.xml`.
- The toolchain-record parser now requires the expanded canonical heading,
  chapter-opener, heading-code-literal, and Fira-fixture success markers; this
  also repairs the stale parser contract exposed by the Phase 3 PDF-QA marker.
  Focused affected suites passed 62 tests, the fixture passed with 59 glyphs
  per Regular/Bold row and one clean veraPDF `ua2` job, and full discovery
  passed all 186 tests.
- README, CONTRIBUTING, `docs/pdf-guide.md`, CHANGELOG,
  RELEASE_CHECKLIST, Make help, workflow comments, and this TODO now describe
  the selected-Fira permanent pipeline and retain all earlier PDF 2.0,
  PDF/UA-2, extraction, font, rail, heading, structure, active-content,
  rendering, OCR, and reproducibility contracts.

### Phase 6: Complete RC.2 Validation and Windows Handoff

- [x] Run `npm ci`.
- [x] Run `make setup-pdf-tools` and verify all locked inputs before building.
- [x] Run `make check`.
- [x] Run the separate network-dependent `make check-external-links` monitor
  and distinguish transient/restricted results from repository correctness.
- [x] Run `make check-shell-syntax` and `make check-shell-lint`.
- [x] Run `make release-check`.
- [x] Run `python3 -m unittest discover -s tests` and record the exact count.
- [x] Run `git diff --check` and the repository public scrub across index and
  worktree boundaries.
- [x] Require two byte-identical canonical builds and record the RC.2 SHA-256,
  page count, PDF properties, exact embedded-font set, toolchain-record hash,
  and veraPDF-report hash.
- [x] Require qpdf success, exact metadata and required text, no prohibited
  active content, exact extraction, default-glyph checks, every-page rendering,
  complete 150-DPI OCR, cover OCR, and one compliant veraPDF 1.30.2 `ua2` job
  with no failures or exceptions.
- [x] Render every RC.2 page at 200 DPI and inspect the cover, complete contents,
  chapter 1-to-2 transition, every code-block opening and page transition,
  B.1 through B.4, UTC table, all three screenshots, ambiguous glyphs, long
  commands, wrapped continuations, links, figures, tables, labels, and contrast.
- [x] Compare RC.2 with the immutable formal RC.1 and selected Fira proof.
  Explain every pagination difference and reject missing content, empty rails,
  heading or decoration orphans, clipping, overlap, malformed commands, broken
  glyphs, displaced figures/tables, or unintended low-contrast text.
- [x] Preserve the exact manual-accessibility evidence actually performed and
  disclose every untested screen-reader/viewer, keyboard, reflow, or other
  assistive-technology pairing without making WCAG or UTC-approval claims.
- [x] Copy only the passing canonical RC.2 PDF, plus any deliberately retained
  inspection TeX, to the Windows Desktop with an unambiguous RC.2 filename.
  Verify the copied bytes against the reviewed local SHA-256.

Phase 6 evidence recorded August 2, 2026:

- `npm ci` completed with zero vulnerabilities. It emitted the known nonfatal
  engine warning because local Node `v24.14.0` precedes the transitive
  `ini@7.0.0` `^24.15.0` range; the locked install and all repository checks
  completed. `make setup-pdf-tools` verified all seven host prerequisites and
  every locked input at lock SHA-256
  `e6821c9177e7160333a273c8b466fbb87be4b35ef9a9dc9525dfab2412bfce31`.
- `make check`, four-file Bash syntax and ShellCheck, `make release-check`,
  `git diff --check`, and the index/worktree no-follow public scrub all passed.
  Complete unittest discovery passed exactly 186 tests. The scrub covered 76
  tracked files and reviewed the expected placeholder/site-note findings.
- The separate external-link monitor reached every ordinary public dependency.
  Its only failure was the authenticated UTC Open OnDemand host after three
  retries because this environment returned DNS `URLError [Errno -2]`. This is
  recorded as restricted/transient network monitoring, not a repository gate;
  no allowlist or correctness check was weakened.
- Repeated locked builds produced a byte-identical 27-page US Letter, tagged,
  unencrypted PDF 2.0 at SHA-256
  `3aba1172a34e3ae28a2290143fc3e132c2e383e11b1276aa8643017eac58b4e3`.
  It embeds exactly Unicode-mapped Noto Sans Regular/Bold, DejaVu Sans Mono
  Regular, and Fira Code Regular. The local worktree toolchain record SHA-256
  is `7ea2c71ef35998617e352e736f3a6627036dab0b34c99187c95dd00fd92d58f4`;
  its commit-bound hosted replacement is a Phase 7 artifact.
- qpdf, exact metadata/text/extraction/font/heading/page-label/destination,
  prohibited-active-content, structure, and default-glyph checks passed. OCR
  covered all 27 pages at 150 DPI with at least 200 alphanumeric characters
  per page and the separate cover requirements. The PDF has 81 headings, all
  11 chapter-opener contracts, all 11 heading-code literals, and 2,596 logical
  structure roles.
- veraPDF 1.30.2 reported one compliant `ua2` job, 1,727 passed rules,
  182,043 passed checks, no failed rules or checks, and no exceptions. The
  local report SHA-256 is
  `247d4ec0ae07d356fc0e21677c59c09829b47cfce2996a9d8eb4e8a496521041`.
- Every RC.2 page was rendered and reviewed at 200 DPI. The cover, complete
  contents, chapter transitions, three sanitized screenshots, UTC table, every
  code opening and continuation, ambiguous glyphs, wrapped commands, links,
  figures, labels, and B.1 through B.4 show no missing content, empty rail,
  orphan, clipping, overlap, malformed command, broken glyph, displaced
  figure/table, or unintended low-contrast text.
- RC.2 remains 27 pages like formal RC.1. The chapter-opener keep moved Access
  from physical page 3 to 4 and its local continuation content forward; the
  Fira metrics and added concise terminology moved selected Python, transfer,
  troubleshooting, and best-practice headings forward by one page. The new
  one-file `scp` material replaces the standalone `rsync` heading while
  retaining the commands. Appendix A and B still open on physical pages 19
  and 23. The selected Fira proof is otherwise the reviewed typography/layout
  input and has only its explicit, noncanonical proof specimen as page 28.
- Manual review here covered visual reading order, heading/content adjacency,
  legibility, contrast, link/table/figure placement, and code differentiation.
  No screen reader or PDF-viewer assistive-technology pairing, keyboard-only
  navigation, or reflow session was performed. The evidence therefore makes
  no WCAG 2.1 AA, universal clipboard/accessibility, or UTC-approval claim.
- The passing PDF alone was copied to
  `C:\\Users\\Gage\\Desktop\\UTC_HPC_Guide_v1.2.2-rc.2.pdf`; no inspection
  TeX was deliberately retained. Its Windows copy has the same reviewed
  SHA-256 `3aba1172a34e3ae28a2290143fc3e132c2e383e11b1276aa8643017eac58b4e3`.

### Phase 7: Focused Draft PR and Proof-Branch Transition

- [ ] Commit and push the complete focused RC.2 implementation only after the
  local gates and Windows-copy hash verification pass.
- [ ] Open a new draft pull request against `main`, titled approximately
  `Prepare v1.2.2-rc.2 with Fira code typography`.
- [ ] In the PR body record main, clean-base, and new-head commits; the selected
  proof and reason; retained/discarded bake-off files; exact commands and test
  count; RC.2 filename, page count, and SHA-256; reproducibility; embedded
  fonts; OCR; structural and page contracts; veraPDF counts; visual review;
  Windows-copy hash; accessibility evidence and limitations; and confirmation
  that no VPN/HPC action occurred.
- [ ] Require every hosted quality, ShellCheck, dependency-review, CodeQL, and
  PDF check to pass on the final PR head.
- [ ] Download the commit-bound hosted candidate artifact and verify its PDF,
  build record, and veraPDF report against the recorded local evidence.
- [ ] After the replacement PR URL exists, add one final comment to PR #28 with
  its head and synthetic merge, formal RC.1 hash, all three proof hashes, 203
  proof-era checks, the Fira selection, accepted layout findings, replacement
  PR link, and `experiment evidence — do not merge` disposition.
- [ ] Close PR #28 unmerged only after that cross-link exists. Retain its remote
  branch and comments through the `v1.2.2` release for auditability.
- [ ] Stop for user inspection and approval. Do not merge the focused RC.2 PR,
  tag, publish, or replace the stable `v1.2.1` release in this phase.

### Phase 8: Approved Final Promotion and Publication

- [ ] Resume only after the user approves the exact RC.2 Windows copy and
  explicitly authorizes the next merge/promotion action.
- [ ] Merge only the focused RC.2 pull request; never merge PR #28.
- [ ] Require all push-to-main checks to pass on the exact RC.2 merge commit and
  independently verify its hosted PDF, build record, and veraPDF report.
- [ ] Create a separate final-promotion branch from that exact approved commit.
- [ ] Promote the manifest to final `1.2.2`, output `UTC_HPC_Guide.pdf`, select
  the actual publication date and deterministic epoch, generate a new trailer
  identifier, move the completed changelog entry out of `[Unreleased]`, and
  remove candidate-only wording without changing approved guide content.
- [ ] Complete the full routine, release, reproducibility, extraction, glyph,
  OCR, structural, PDF/UA-2, all-page visual, and manual accessibility review
  on the exact final hash. Record performed tools, versions, reviewer profile,
  tasks, results, remediations, retests, and untested limitations.
- [ ] Copy the exact passing final PDF to the Windows Desktop and obtain final
  user approval before publication.
- [ ] Open and validate a focused final-promotion PR. Merge only with explicit
  user authorization after all hosted checks and downloaded hashes pass.
- [ ] Tag the exact reviewed main commit as `v1.2.2`, publish a non-prerelease
  GitHub release with the verified final PDF, build record, and veraPDF report,
  and confirm the stable latest-download URL serves the recorded PDF hash.
- [ ] Confirm the tag, release assets, `main`, local branch, remote tracking
  refs, index, and worktree are clean and synchronized.

### Research and Policy Basis

- Fira Code 6.2 documents that its design includes punctuation and frequent
  character-pair work beyond ligatures:
  <https://github.com/tonsky/FiraCode/blob/6.2/README.md#whats-in-the-box>.
- The official fontspec manual maps the retained named controls to required,
  common, contextual, discretionary, historic, and TeX ligature features:
  <https://latex3.github.io/fontspec/fontspec.pdf>.
- Current LaTeX tagging status supports avoiding the incompatible `needspace`,
  `listings`, and `minted` packages and the only partially compatible
  `tcolorbox` package:
  <https://latex3.github.io/tagging-project/tagging-status/>.
- Google's printable code and command guidance supports an approximately
  80-character threshold with valid continuation characters:
  <https://developers.google.com/style/code-samples> and
  <https://developers.google.com/style/code-syntax>.
- SchedMD records `Slurm` as the preferred spelling, OpenSSH documents modern
  `scp` syntax and SFTP transport, and veraPDF limits PDF/UA claims to
  machine-verifiable checks:
  <https://slurm.schedmd.com/faq.html>, <https://man.openbsd.org/scp.1>, and
  <https://docs.verapdf.org/validation/>.

No phase requires the UTC VPN or HPC. Reopen live-site validation only if a
new authoritative source changes an isolated UTC fact under the existing
live-site rule.
