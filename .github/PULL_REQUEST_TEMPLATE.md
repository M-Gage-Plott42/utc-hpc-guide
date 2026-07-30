# Pull Request

## Summary

Describe what changed and why.

## Scope

- [ ] Docs content
- [ ] Site-specific public documentation (`docs/sites/`)
- [ ] Examples (`examples/*.sbatch`)
- [ ] Repo/process metadata (`README`, `SECURITY`, checklists)
- [ ] PDF/toolchain/accessibility

## Reviewer Checklist

- [ ] Content is cluster-agnostic and placeholder-based
- [ ] No credentials, usernames, internal hostnames, account strings, or allocation IDs
- [ ] Commands and examples are copy/paste friendly
- [ ] README/docs links are valid
- [ ] Screenshots (if any) are sanitized
- [ ] Site facts cite official public sources and field-note status is explicit
- [ ] Screenshot alternative text is meaningful
- [ ] Candidate/final labeling and output filename match the PDF manifest
- [ ] No WCAG, PDF/UA, or UTC approval claim relies only on automation

## Validation Performed

Paste the checks you ran. Use the routine gate for ordinary documentation
changes:

```bash
npm ci
make check
```

For release-affecting changes, use:

```bash
npm ci
make setup-pdf-tools
make release-check
```

For PDF or release changes, complete the
[public release checklist](../RELEASE_CHECKLIST.md) and report:

- Candidate version and filename:
- PDF page count and SHA-256:
- Two-build byte-identity result:
- `Tagged`, `StructTreeRoot`, `MarkInfo`, and `Lang` results:
- veraPDF profile, result, and report artifact:
- All-page visual-review result:
- Manual accessibility reviewer, tools, date, findings, and limitations:
- UTC live-validation status:
