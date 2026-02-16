# Contributing

Thanks for improving the UTC HPC Guide.

## Contribution Scope

This repository is public and cluster-agnostic. Keep examples and docs reusable across institutions.

Use placeholders for site-specific values:

- `<username>`
- `<login-host>`
- `<cpu-partition>`
- `<gpu-partition>`
- `<account>`

## Local Validation Before PR

Run these commands from repo root:

```bash
make check
```

Expected scrub output: for normal clean-state runs, `make scrub` should produce no match lines from the two scan commands (only the scan labels).

If you change image assets, manually confirm screenshots do not expose usernames, hostnames, account/allocation IDs, or private paths.

## Pull Request Process

1. Keep changes focused and easy to review.
2. Update docs/examples together when behavior changes.
3. Include validation output in the PR body.
4. Use the repository PR template and check all hygiene boxes.

## Commit Guidance

- Prefer concise, descriptive commit messages.
- Group related docs/process updates into one logical commit.

## Style

- Keep sections short and command-oriented.
- Treat institutional docs and live SLURM commands as source of truth.
- Avoid institution-specific values unless clearly marked as placeholders.
