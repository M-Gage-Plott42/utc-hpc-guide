# AGENTS.md

## Repository Purpose

This repository is a public, documentation-first HPC onboarding guide focused on generic SLURM, Open OnDemand, SSH, and Python workflows.

## Mandatory Content Rules

- Keep generic docs and examples cluster-agnostic and reusable across institutions.
- Do not commit credentials, usernames, internal hostnames, account strings, allocation IDs, or private paths.
- Use placeholders for site-specific values:
  - `<username>`
  - `<login-host>`
  - `<cpu-partition>`
  - `<gpu-partition>`
  - `<account>`
  - `<home-path>`
  - `<scratch-path>`
  - `<project-path>`
- Treat official institutional HPC docs and live SLURM commands as source of truth for site-specific policy.

## Site-Specific Notes

- Public, official site-specific information is allowed only under `docs/sites/`.
- Site notes must cite or link to official public docs where possible.
- Label operational observations that are not in public docs as field notes.
- Use placeholders for user-specific values even in site pages, for example `<your_utc_id>`.
- Do not include personal usernames, job IDs, node-specific allocation hostnames from real jobs, GPU UUIDs, private paths, screenshots with identifiers, allocation/account strings, or private support emails.

## Repository Structure Expectations

- `docs/`: narrative onboarding guide pages
- `docs/sites/`: isolated public site-specific notes
- `examples/`: runnable minimal sbatch templates
- `assets/`: optional sanitized screenshots only
- `README.md`: reviewer-friendly entry point and navigation
- `SECURITY.md`: public hygiene baseline

## Editing Guidelines

- Preserve numbered docs (`docs/00` through `docs/08`) unless a structural change is intentional.
- Keep sections short and practical; prefer command snippets over long prose.
- Keep examples minimal and explicitly commented.
- If adding screenshots, ensure no identifiable user, hostname, job ID, or account metadata is visible.

## Pre-Publish Scrub Checklist

For routine documentation work, install the locked Node toolchain and run:

```bash
npm ci
make check
```

For release-affecting work, install ShellCheck and the documented host
prerequisites, bootstrap the locked PDF toolchain, then run:

```bash
npm ci
make setup-pdf-tools
make release-check
```

The release gate adds Bash syntax, ShellCheck, a byte-identical tagged-PDF
build, structural and PDF/UA-2 machine validation, every-page rendering and OCR
QA, and whitespace validation. Follow
[`docs/pdf-guide.md`](docs/pdf-guide.md) for the locked toolchain and manual
accessibility review. Automated tagging and veraPDF success do not establish
WCAG 2.1 AA, assistive-technology usability, or UTC accessibility approval.
Keep network-dependent dependency audits separate.

The repository scrub accepts only ordinary stage-zero regular or executable
Git index entries. Tracked symbolic links, gitlinks, unmerged entries,
unsupported modes, a symbolic link in any worktree path component, and a
worktree symbolic link replacing a regular file are policy failures. Worktree
content, including the policy and exception targets, must be opened one
component at a time from the repository root through the no-follow
regular-file boundary.

Manual-review scrub hits such as `login`, `partition`, `account`, or `allocation` are expected in generic placeholders and may be expected in `docs/sites/`, but each hit must be reviewed before release. Then manually review `assets/` for redaction quality.

## Commit Convention

- Use concise, descriptive commit messages.
- Group related documentation and template changes into a single logical commit.
- For routine single-maintainer updates, direct pushes to `main` are acceptable.
- Use topic branches and PRs when changes are larger or benefit from review context.
