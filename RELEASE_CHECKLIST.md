# Public Release Checklist

Use this checklist before tagging a release or major public update.

Install the locked Node dependencies and required local ShellCheck/PDF tools,
then run the unified release gate from the repository root:

```bash
npm ci
make setup-pdf-tools
make release-check
```

Keep network-dependent dependency audits separate from this local gate.

## 1. Content and Scope

- Confirm generic docs remain cluster-agnostic and placeholder-based.
- Confirm examples avoid site-specific partition/account/QOS values.
- Confirm `docs/sites/` contains only public site-specific notes.
- Confirm site-specific notes are checked against official public docs or clearly labeled as field notes.
- For a UTC-targeted release, record the public-document recheck and sanitized
  live-validation date. Do not promote while required VPN/live checks are
  pending or a public/live conflict leaves supported user guidance ambiguous.
  A disclosed layered mismatch may be nonblocking only when current
  user-facing sources agree on a conservative supported value and the guide
  neither claims nor encourages the higher backend value.
- Confirm README "Last updated" month/year is current.
- Confirm the manifest status, document version, output filename, workflow
  artifact label, and distribution-status record all describe the same
  candidate or final build.

## 2. Sensitive Data Scrub

Run:

```bash
make scrub
```

Fail release if the all-tracked-text scan reports forbidden matches. Review
the contextual-hit total when content changes. Public site facts must have an
exact, reasoned exception bound to a Markdown page under `docs/sites/`;
generalize anything institution-specific that should not be public.

The scrub preflight must accept only stage-zero regular or executable index
entries. Fail on tracked symbolic links, gitlinks, unmerged entries,
unsupported modes, a symbolic link in any worktree path component, or a
non-directory parent. Regular worktree reads, the policy, and site-exception
targets must be opened one component at a time from the repository root
through the no-follow boundary. A scrub pass is still one defense in depth,
not proof that the repository is free of private data.

## 3. Screenshots and Assets

- Verify each image in `assets/` has no usernames, hostnames, account IDs, job IDs, node-specific real allocation names, GPU UUIDs, direct email addresses, or private paths.
- Run `make check-assets` and confirm all PNGs pass CRC, chunk-order, decode,
  scanline, filter, terminal-IEND, and ancillary-chunk checks.
- Run `make test-assets` and confirm the PNG failure-path suite passes.
- Remove or re-export any image with residual metadata or identifying UI elements.

## 4. Documentation Integrity

- Check that README links to all docs and examples; `make check-links` must
  resolve inline Markdown, reference-style, raw HTML, and heading-anchor links.
- Confirm commands render correctly in Markdown and copy/paste cleanly.
- Confirm placeholders are consistent across docs.
- Run `make check-placeholders` and confirm shell snippets and sbatch templates
  contain no angle-bracket placeholders that a shell could parse as redirects.
- Confirm any downloadable installer uses an exact filename and a source-verified
  SHA-256 digest rather than a moving `latest` URL.
- Confirm the `make check` portion of `make release-check` passes with the
  locked local Markdown tooling.

## 5. Git Hygiene

- `git status` is clean before publishing.
- Commit message clearly states scope.
- Push only intended files.
- For substantial changes, prefer branch + PR for reviewable history.

## 6. Printable PDF

- Confirm `pdf/guide_manifest.json` lists the complete ordered guide source.
- Run `make setup-pdf-tools` and confirm every source checksum, signature, key
  fingerprint, version, and host QA-tool version required by
  `pdf/toolchain.lock.json` passes before building.
- Confirm the `make check-pdf` portion of `make release-check` requires
  byte-identical rebuilds plus passing structure, metadata, font,
  text-extraction, rendering, every-page OCR, and
  `make check-pdf-accessibility` checks.
- Confirm `pdfinfo` reports `Tagged: yes` and PDF 2.0.
- Confirm the catalog has a structure tree, marked-content metadata, `en-US`,
  and the expected PDF/UA-2 identification.
- Confirm representative headings, lists, table headers/cells, links, figures,
  and code are present in the logical structure.
- Confirm all three Open OnDemand figures carry the expected meaningful
  alternative descriptions.
- Confirm the PDF has no encryption, forms, JavaScript, attachments, embedded
  files, or other active content rejected by the accessibility checker.
- Run the locked veraPDF `ua2` profile with no allowlist and confirm
  `dist/verapdf-report.xml` contains exactly one compliant job and no failed or
  exceptional jobs.
- Confirm the shell syntax, ShellCheck, and `git diff --check` portions of the
  unified gate pass.
- Review the generated PDF visually before publishing.
- Treat OCR as a legibility regression check, not proof that screenshots or
  pages are safely redacted.
- Complete the [manual accessibility review](docs/pdf-guide.md#manual-accessibility-review)
  on the exact PDF hash. Verify reading order with a screen reader or
  read-aloud tool, or through an accessibility API; verify focus order with
  keyboard traversal or a tool that exposes the PDF tab-order setting. Record
  the reviewer profile, exact tools and versions, settings, date, tasks,
  itemized results, remediations, retest results, and untested limitations.
  Desktop Acrobat Reader plus NVDA on Windows is a recommended reference
  environment, not an exclusive requirement. Acrobat Read Out Loud may
  supplement a reading-order check, but Adobe states that it is not a screen
  reader and it must not be reported as screen-reader evidence.
- Do not describe automated tagging or veraPDF success as WCAG 2.1 AA
  certification, assistive-technology usability, or UTC accessibility
  approval.
- For an independent GitHub release, state the exact evidence and untested
  limitations without implying official endorsement. Institution-hosted or
  officially endorsed publication remains subject to the institution's
  documented accessibility review and publishing process.
- For a GitHub Actions build, download the PDF, `build-toolchain.txt`, and
  `verapdf-report.xml` from the same workflow artifact and confirm the recorded
  PDF SHA-256 matches. `pdf/toolchain.lock.json` is the declared toolchain lock;
  the artifact record is run traceability, not signed provenance, and the
  artifact is transient.
- For final promotion, review the successful artifact built from the exact
  final `main` commit and confirm its SHA-256 before tagging. Bind every manual
  result to that same hash.
- Attach the reviewed PDF to the matching GitHub release under the stable
  asset name `UTC_HPC_Guide.pdf`.
- After publication, confirm the stable latest-release asset URL resolves:
  `https://github.com/M-Gage-Plott42/utc-hpc-guide/releases/latest/download/UTC_HPC_Guide.pdf`.

## 7. Publication Note

For external materials (e.g., LANL package), include:

- Repo URL: `https://github.com/M-Gage-Plott42/utc-hpc-guide`
- One-line proof statement in your external materials package
