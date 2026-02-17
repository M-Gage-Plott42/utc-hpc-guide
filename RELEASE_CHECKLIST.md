# Public Release Checklist

Use this checklist before tagging a release or major public update.

## 1. Content and Scope

- Confirm docs remain cluster-agnostic and placeholder-based.
- Confirm examples avoid site-specific partition/account/QOS values.
- Confirm README "Last updated" month/year is current.

## 2. Sensitive Data Scrub

Run:

```bash
make scrub
```

Fail release if the strict scan reports forbidden matches.
Review any manual-review matches and generalize anything institution-specific that should not be public.

## 3. Screenshots and Assets

- Verify each image in `assets/` has no usernames, hostnames, account IDs, job IDs, or private paths.
- Run `make check-assets` and confirm `asset_policy_clean`.
- Remove or re-export any image with residual metadata or identifying UI elements.

## 4. Documentation Integrity

- Check that README links to all docs and examples.
- Confirm commands render correctly in Markdown and copy/paste cleanly.
- Confirm placeholders are consistent across docs.
- Run `make check` from repo root and confirm all checks pass.

## 5. Git Hygiene

- `git status` is clean before publishing.
- Commit message clearly states scope.
- Push only intended files.
- Default to branch + PR merges into `main` (avoid direct pushes).

## 6. Publication Note

For external materials (e.g., LANL package), include:

- Repo URL: `https://github.com/M-Gage-Plott42/utc-hpc-guide`
- One-line proof statement in your external materials package
