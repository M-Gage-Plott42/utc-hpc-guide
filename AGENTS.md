# AGENTS.md

## Repository Purpose

This repository is a public, documentation-first HPC onboarding guide focused on generic SLURM, Open OnDemand, SSH, and Python workflows.

## Mandatory Content Rules

- Keep content cluster-agnostic and reusable across institutions.
- Do not commit credentials, usernames, internal hostnames, account strings, allocation IDs, or private paths.
- Use placeholders for site-specific values:
  - `<username>`
  - `<login-host>`
  - `<cpu-partition>`
  - `<gpu-partition>`
  - `<account>`
- Treat official institutional HPC docs and live SLURM commands as source of truth for site-specific policy.

## Repository Structure Expectations

- `docs/`: narrative onboarding guide pages
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

Then manually review `assets/` for redaction quality.

## Commit Convention

- Use concise, descriptive commit messages.
- Group related documentation and template changes into a single logical commit.
- For routine single-maintainer updates, direct pushes to `main` are acceptable.
- Use topic branches and PRs when changes are larger or benefit from review context.
