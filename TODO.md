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

Status: planned — Fira Code selected; implementation has not started

Plan date: August 1, 2026

This is the complete resumption plan following the final independent audit and
the user's selection of the Fira Code proof. It supersedes the audit's
subjective Cascadia Mono preference but accepts the audit's actionable layout,
content, pipeline, and release-boundary findings as reconciled below.

### Guarded Inputs and Fixed Decisions

- `origin/main` must be
  `d5815af6c6574f4ddf2d0020422b91d82bd7ec95` before the focused work starts.
- The typeface-evidence branch and draft pull request #28 must remain at
  `e1c6f68822522dbf8e3d4c31e02dc4bde47bcf00` until the replacement pull
  request is ready.
- The focused RC.2 branch must start from the clean polished-candidate commit
  `aefc676200acc09df044be9a5f7039b9e093d878`, not from the proof-matrix tip.
- The new branch name is `agent/v1.2.2-rc.2-fira`.
- Before any implementation edit on that branch, cherry-pick the plan-only
  commit `PLAN_COMMIT_TO_BIND`. Verify that this transfer changes only
  `TODO.md`; stop if it carries proof implementation files.
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

- [ ] Confirm the worktree and index are clean before fetching or branching.
- [ ] Fetch `origin` with pruning and verify the three guarded commits above.
  Stop rather than rebasing, merging, or guessing if any ref differs.
- [ ] Create `agent/v1.2.2-rc.2-fira` directly from
  `aefc676200acc09df044be9a5f7039b9e093d878`.
- [ ] Cherry-pick the bound plan-only commit named above and verify that it
  changes only `TODO.md`; this keeps the complete plan on the clean-base branch.
- [ ] Keep PR #28 open, draft, unmerged, and unchanged while RC.2 is built so
  its proof artifacts and comments remain reachable as comparison evidence.
- [ ] Before any other PDF-changing edit, promote the manifest boundary to:
  - `release_status`: `candidate`
  - `release_target`: `1.2.2`
  - `document_version`: `1.2.2-rc.2`
  - `output_filename`: `UTC_HPC_Guide_v1.2.2-rc.2.pdf`
- [ ] Select a new deterministic source epoch and engine-compatible trailer
  identifier, and update candidate-owned required PDF and OCR text from RC.1
  to RC.2.
- [ ] Keep the current `1.2.2` changelog material under `[Unreleased]`; do not
  assign a stable release date during candidate work.

### Phase 1: Promote Only the Selected Fira Profile

- [ ] Bring over only `FiraCode-Regular.ttf`, `FiraCode-Bold.ttf`, the OFL
  license, and the Fira 6.2 source entry from the proof lock.
- [ ] Preserve the exact upstream release tag and commit, archive URL, archive
  byte size and SHA-256, archive members, local file sizes and SHA-256 values,
  PostScript names, license URL, license size, and license SHA-256.
- [ ] Fold the selected-font provenance and permanent MuPDF/fontTools host
  requirements into the canonical toolchain contract and build record; do not
  retain a multi-profile proof lock.
- [ ] Replace proof-parameterized font selection with one focused canonical
  Fira code-font configuration at `9.1/11.5 pt`.
- [ ] Apply the complete named and raw ligature denylist above to the canonical
  Fira family and reject an unresolved or missing option.
- [ ] Keep DejaVu Sans Mono as the inline-code family and Noto Sans as the
  prose/heading family; document this as an intentional semantic distinction.
- [ ] Add a small test-only semantic font fixture that exercises Regular and
  Bold Fira, the ambiguous-glyph string, indentation, and interior spaces.
  Never append that fixture to the canonical guide or upload it as a release
  artifact.
- [ ] Require the release PDF to embed exactly the Unicode-mapped faces its
  canonical content actually uses. Validate unused Fira Bold in the fixture
  rather than forcing it into the release artifact.

### Phase 2: Correct Appendix Assembly and Code Rails

- [ ] Assemble each generated Appendix B fenced block without a blank line
  between the opening fence and the tracked script's first source line.
- [ ] Add an assembly regression requiring every Appendix B block to begin
  immediately with its tracked `#!/bin/bash -l` line.
- [ ] Remove `\everypar{\GuideCodeRail}` from the `GuideCode` environment.
- [ ] Have the Lua code-line transformation attach `\GuideCodeRail` directly
  to each actual generated source-line paragraph.
- [ ] Preserve a rail for a deliberate blank line that exists in tracked
  source, but reject invented leading or trailing blank lines.
- [ ] Keep every rail inside a layout-artifact marked-content boundary and
  outside logical reading order while retaining the encompassing semantic
  `Code` structure.
- [ ] Add regressions proving one rail per real source line, no synthetic
  leading rail, unchanged first-line alignment, and exact extraction of
  indentation and meaningful interior spaces.
- [ ] Rebuild RC.2 after this root fix before adding pagination controls; record
  whether the B.4 orphan resolves naturally.

### Phase 3: Heading Pagination and PDF-Only Heading Typography

- [ ] Implement a tagging-safe chapter-opener keep rule with core LaTeX
  penalties/no-break controls, not a new package or a boxed long code block.
- [ ] Require each top-level chapter heading, its short introductory paragraph,
  and its first subsection heading to share a physical page. If a source shape
  cannot satisfy that bounded opener, fail the contract and resolve that case
  explicitly rather than silently weakening the rule.
- [ ] Require each B.1 through B.4 script heading to share a physical page with
  its first nonblank source line.
- [ ] Require that no heading end a page followed only by a code rail or other
  decoration.
- [ ] Add deterministic text-to-page mapping tests for every chapter opener,
  every Appendix B heading/shebang pair, and specifically `2. Access and SSH`
  with `2.1 Account and Network Prerequisites`.
- [ ] For PDF output only, convert inline `Code` nodes contained in `Header`
  nodes to ordinary literal heading text without interpreting punctuation or
  changing spaces.
- [ ] Assert unchanged heading text, identifiers, destinations, outline text,
  hierarchy, and structure roles while requiring the normal Noto heading face.
- [ ] Render the complete two-column contents page after the transformation.
  Shorten only entries that still wrap excessively; do not shrink the whole
  contents page to accommodate isolated long entries.
- [ ] Reject heading-only bottoms, excessive new whitespace, three-line TOC
  entries, terminal-style heading text, or new clipping and overlap.

### Phase 4: Canonical Source Wrapping and Focused Usability Edits

- [ ] Replace the long `sacct --format` argument in canonical Markdown with the
  reviewed readable `SACCT_FIELDS` composition and quoted use.
- [ ] Replace the long `pip download` line in canonical Markdown with the
  reviewed shell continuation, ending every nonfinal command line with `\`.
- [ ] Keep the 83-character immutable Miniconda SHA-256 assignment on one line.
  Record it as the sole exact code-width exception because splitting an opaque
  digest is less understandable and more error-prone for beginners.
- [ ] Apply the approximately 80-character width audit to the formal candidate,
  not through hidden proof-time replacements. Reject any new or unexplained
  exception.
- [ ] Add near first use: `Slurm is the cluster workload manager and job
  scheduler that allocates compute resources and queues jobs.`
- [ ] Use `Slurm` in current ordinary prose and headings. Preserve exact
  `SLURM_*` environment variables, code, source output, historical quotations,
  URLs, and immutable prior-release evidence.
- [ ] Add one compact terms sentence defining HPC, SSH, OOD, CPU, and GPU; do
  not add a long glossary.
- [ ] Explain that angle-bracket placeholders are prose/path notation, while
  runnable shell uses `REPLACE_WITH_*` because unquoted angle brackets are
  shell redirection operators.
- [ ] Remove `<group>` because it has no use in the current guide.
- [ ] Under Transfer Methods, add one-file `scp` upload and download examples
  using the existing placeholder variables, then place the incremental
  `rsync` examples underneath and remove the thin standalone `rsync` section.
- [ ] Keep every edit cluster-agnostic. Do not change the UTC table, field-note
  boundaries, screenshots, site facts, or live-validation evidence.

### Phase 5: Permanent QA, Pipeline, and Documentation Cleanup

- [ ] Do not bring over Cascadia files, the larger DejaVu proof profile,
  `font-proof-specimen.md`, the three-profile matrix/configuration, proof
  source transforms, proof orchestrator, proof-only checksum bundle, proof
  Make targets, or proof artifact upload.
- [ ] Retain only focused reusable selected-font logic for exact source files
  and license, provenance, PostScript names, embedded fonts, Unicode maps,
  default-cmap glyphs, extraction, and width checks.
- [ ] Require the fixture's Regular and Bold rows to map every literal character
  in `0 O o 1 l I | < > <= >= == != -> -- _ ~ \ / ' " ( ) [ ] { }` to one
  visible default glyph, with no multi-character ligature or contextual
  alternate.
- [ ] Require exact four-space indentation and meaningful two-space separators
  in locked Poppler extraction, while documenting that this does not prove
  clipboard behavior in every PDF viewer.
- [ ] Retain PDF 2.0, PDF/UA-2, page-label, destination, `/Tabs /S`, contiguous
  structure-parent, exact structure-role, alt-text, link, table, figure,
  metadata, font, active-content, render, OCR, and reproducibility contracts.
- [ ] Add the rail, chapter-opener, Appendix-heading, heading-font, canonical
  width, and selected-Fira contracts to routine/unit and release gates.
- [ ] Make `release-check` validate only the canonical RC.2 and the small
  test-only selected-font fixture; it must not build three full guide proofs.
- [ ] Make CI upload only the manifest-derived canonical candidate, canonical
  build record, and canonical veraPDF report.
- [ ] Update README, CONTRIBUTING, `docs/pdf-guide.md`, CHANGELOG,
  RELEASE_CHECKLIST, Make help, workflow comments, toolchain records, and this
  TODO so no active instruction treats the bake-off matrix as permanent.
- [ ] Retain the historical proof hashes and PR #28 link as evidence, clearly
  labelled as completed review-only inputs rather than release artifacts.

### Phase 6: Complete RC.2 Validation and Windows Handoff

- [ ] Run `npm ci`.
- [ ] Run `make setup-pdf-tools` and verify all locked inputs before building.
- [ ] Run `make check`.
- [ ] Run the separate network-dependent `make check-external-links` monitor
  and distinguish transient/restricted results from repository correctness.
- [ ] Run `make check-shell-syntax` and `make check-shell-lint`.
- [ ] Run `make release-check`.
- [ ] Run `python3 -m unittest discover -s tests` and record the exact count.
- [ ] Run `git diff --check` and the repository public scrub across index and
  worktree boundaries.
- [ ] Require two byte-identical canonical builds and record the RC.2 SHA-256,
  page count, PDF properties, exact embedded-font set, toolchain-record hash,
  and veraPDF-report hash.
- [ ] Require qpdf success, exact metadata and required text, no prohibited
  active content, exact extraction, default-glyph checks, every-page rendering,
  complete 150-DPI OCR, cover OCR, and one compliant veraPDF 1.30.2 `ua2` job
  with no failures or exceptions.
- [ ] Render every RC.2 page at 200 DPI and inspect the cover, complete contents,
  chapter 1-to-2 transition, every code-block opening and page transition,
  B.1 through B.4, UTC table, all three screenshots, ambiguous glyphs, long
  commands, wrapped continuations, links, figures, tables, labels, and contrast.
- [ ] Compare RC.2 with the immutable formal RC.1 and selected Fira proof.
  Explain every pagination difference and reject missing content, empty rails,
  heading or decoration orphans, clipping, overlap, malformed commands, broken
  glyphs, displaced figures/tables, or unintended low-contrast text.
- [ ] Preserve the exact manual-accessibility evidence actually performed and
  disclose every untested screen-reader/viewer, keyboard, reflow, or other
  assistive-technology pairing without making WCAG or UTC-approval claims.
- [ ] Copy only the passing canonical RC.2 PDF, plus any deliberately retained
  inspection TeX, to the Windows Desktop with an unambiguous RC.2 filename.
  Verify the copied bytes against the reviewed local SHA-256.

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
