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

Run before commit/push:

```bash
make check
```

Manual-review scrub hits such as `login`, `partition`, `account`, or `allocation` are expected in generic placeholders and may be expected in `docs/sites/`, but each hit must be reviewed before release. Then manually review `assets/` for redaction quality.

## Commit Convention

- Use concise, descriptive commit messages.
- Group related documentation and template changes into a single logical commit.
- For routine single-maintainer updates, direct pushes to `main` are acceptable.
- Use topic branches and PRs when changes are larger or benefit from review context.
