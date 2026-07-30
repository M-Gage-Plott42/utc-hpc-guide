# Public Release Checklist

Use this checklist before tagging a release or major public update.

Install the locked Node dependencies and required local ShellCheck/PDF tools,
then run the unified release gate from the repository root:

```bash
npm ci
make release-check
```

Keep network-dependent dependency audits separate from this local gate.

## 1. Content and Scope

- Confirm generic docs remain cluster-agnostic and placeholder-based.
- Confirm examples avoid site-specific partition/account/QOS values.
- Confirm `docs/sites/` contains only public site-specific notes.
- Confirm site-specific notes are checked against official public docs or clearly labeled as field notes.
- Confirm README "Last updated" month/year is current.

## 2. Sensitive Data Scrub

Run:

```bash
make scrub
```

Fail release if the all-tracked-text scan reports forbidden matches. Review
the contextual-hit total when content changes. Public site facts must have an
exact, reasoned exception bound to a Markdown page under `docs/sites/`;
generalize anything institution-specific that should not be public.

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
- Confirm the `make check-pdf` portion of `make release-check` requires
  byte-identical rebuilds plus passing structure, metadata, font,
  text-extraction, rendering, and every-page OCR checks.
- Confirm the shell syntax, ShellCheck, and `git diff --check` portions of the
  unified gate pass.
- Review the generated PDF visually before publishing.
- Treat OCR as a legibility regression check, not proof that screenshots or
  pages are safely redacted.
- For a GitHub Actions build, download the PDF and `build-toolchain.txt` from
  the same workflow artifact and confirm the recorded PDF SHA-256 matches.
  The artifact is transient, and the record is neither a toolchain lock nor
  signed build provenance.
- Attach the reviewed PDF to the matching GitHub release under the stable
  asset name `UTC_HPC_Guide.pdf`.
- After publication, confirm the stable latest-release asset URL resolves:
  `https://github.com/M-Gage-Plott42/utc-hpc-guide/releases/latest/download/UTC_HPC_Guide.pdf`.

## 7. Publication Note

For external materials (e.g., LANL package), include:

- Repo URL: `https://github.com/M-Gage-Plott42/utc-hpc-guide`
- One-line proof statement in your external materials package
