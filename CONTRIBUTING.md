# Contributing

Thanks for improving the UTC HPC Guide.

By participating, you agree to follow this repository's [Code of Conduct](CODE_OF_CONDUCT.md).

## Contribution Scope

This repository is public and cluster-agnostic by default. Keep generic docs and examples reusable across institutions.

Use placeholders for site-specific values:

- `<username>`
- `<login-host>`
- `<cpu-partition>`
- `<gpu-partition>`
- `<account>`
- `<home-path>`
- `<scratch-path>`
- `<project-path>`

Public site-specific notes are allowed only under `docs/sites/`. Site notes should link to official public documentation where possible, label non-public operational observations as field notes, and use placeholders for user-specific values.

## Routine Local Validation

Run these commands from repo root:

```bash
npm ci
make check
```

Expected behavior:

- `npm ci` installs the exact local tooling recorded in `package-lock.json`.
- `make lint` uses only `./node_modules/.bin/markdownlint`; a global
  `markdownlint` installation is neither required nor used.
- `make scrub` scans every Git-tracked text file and prints
  `public_scrub_policy_passed` or fails on repository-policy patterns.
- The scrub preflight reads NUL-safe index records and accepts only ordinary
  stage-zero regular or executable files. Tracked symbolic links, gitlinks,
  unmerged entries, and unsupported modes are repository-policy failures.
  Worktree entries are inspected separately from an open repository-root
  descriptor. Every component is opened without following symbolic links,
  every parent must be a directory, and the final component must be a regular
  file. The opened chain remains retained through the read and every component
  name is revalidated against its descriptor before the content is accepted.
- Public site facts require exact, reasoned exceptions under `docs/sites/` in
  `scripts/public_scrub_exceptions.json`.
- `make test-scrub` exercises scan coverage and exception failure paths.
- `make check-assets` prints `asset_policy_clean` only when the asset-tree
  allowlist, sanitized naming, PNG structure, CRCs, chunk ordering,
  decompression, filters, and ancillary-chunk metadata policy all pass.
- `make test-assets` exercises corrupt, malformed, metadata-bearing, and
  undecodable PNG failure paths.
- `make check-links` parses Markdown links, reference links, raw HTML link
  attributes, and heading anchors; it fails on missing local targets or anchors.
- `make test-links` exercises inline, reference, HTML, code-mask, duplicate
  heading, and failure-path behavior.

## Release Validation

For a release-affecting change, use the Ubuntu 24.04 x86_64 host, install
ShellCheck and the prerequisites listed in
[the PDF guide](docs/pdf-guide.md), then bootstrap the locked PDF toolchain and
run:

```bash
npm ci
make setup-pdf-tools
make release-check
```

The release gate runs the routine checks, applies `bash -n` and ShellCheck to
each tracked `examples/*.sbatch` file, requires a byte-identical PDF rebuild
that passes structural, PDF/UA-2 machine, rendering, text-extraction, and
every-page OCR QA, and checks staged and unstaged changes for whitespace
errors. The pinned veraPDF result covers machine-verifiable conformance only;
it does not certify WCAG 2.1 AA or replace the manual accessibility checklist.
Network-dependent dependency audits remain separate.

If you change image assets, manually confirm screenshots do not expose usernames, hostnames, account/allocation IDs, or private paths.
The automated asset gate checks paths, structure, decoding, and metadata; it
does not inspect pixels or prove that an image is safely redacted.

## Pull Request Process

1. Keep changes focused and easy to review.
2. Update docs/examples together when behavior changes.
3. Include routine or release validation output, as appropriate, in the PR
   body.
4. Use the repository PR template and check all hygiene boxes.

## Branch Policy

- For a single maintainer, direct pushes to `main` are acceptable.
- For larger or risky changes, prefer a topic branch and PR for reviewable history.
- Treat PDF toolchain, accessibility, and release-promotion changes as
  substantial work that requires a topic branch and pull request.

## Commit Guidance

- Prefer concise, descriptive commit messages.
- Group related docs/process updates into one logical commit.

## Style

- Keep sections short and command-oriented.
- Treat institutional docs and live SLURM commands as source of truth.
- Avoid institution-specific values in generic docs and examples unless clearly marked as placeholders.
