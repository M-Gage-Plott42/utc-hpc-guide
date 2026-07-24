# Public Release Checklist

Use this checklist before tagging a release or major public update.

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
- Confirm any downloadable installer uses an exact filename and a source-verified
  SHA-256 digest rather than a moving `latest` URL.
- Run `npm ci` followed by `make check` from repo root and confirm all checks
  pass with the locked local tooling.

## 5. Git Hygiene

- `git status` is clean before publishing.
- Commit message clearly states scope.
- Push only intended files.
- For substantial changes, prefer branch + PR for reviewable history.

## 6. Publication Note

For external materials (e.g., LANL package), include:

- Repo URL: `https://github.com/M-Gage-Plott42/utc-hpc-guide`
- One-line proof statement in your external materials package
