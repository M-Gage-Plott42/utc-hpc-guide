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

Status: local proof bundle complete — hosted validation and user selection
remain pending

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
- [ ] Record proof hashes, validation evidence, and limitations; commit and
  push the implementation to draft pull request #28 and require hosted checks
  to pass before the selection handoff.
- [ ] Stop for user selection. Promote only the chosen profile in a later
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

### Phase 6: Publication Boundary

- [ ] After candidate approval, prepare a separate final-promotion change for
  `v1.2.2` and re-run all PDF-changing validation on its exact hash.
- [ ] Merge, tag, and publish only the reviewed final artifact; do not attach
  the candidate to a stable release or overwrite the existing `v1.2.1` asset.

No VPN or new live-cluster validation is needed for this design migration.
Reopen live validation only under the existing live-site rule above.
