# Security Policy

Do not commit credentials, usernames, internal hostnames, or allocation IDs.

## Public Content Policy

- Keep secrets in environment variables or a secrets manager, never in git.
- Sanitize screenshots before adding them to `assets/`.
- Replace institution-specific identifiers with placeholders in public docs.
- Review changes with a scrub pass before each public push.

`make scrub` is a repository-policy scanner. It checks Git-tracked UTF-8 text
for this project's known internal markers, selected credential formats, email
addresses, private home paths, and unapproved UTC site facts. Its finite rules
cannot prove that a repository contains no secrets or private information.
Treat it as one defense in depth alongside review and provider-backed secret
scanning.

### Tracked Entry Boundary

This public documentation repository allows only stage-zero regular
(`100644`) and executable (`100755`) Git index entries. `make scrub` rejects
tracked symbolic links, gitlinks, unmerged entries, and any unsupported index
mode before it loads the policy or reads content.

The scanner evaluates the indexed blob for every accepted entry and also scans
a differing worktree version. A genuinely deleted worktree file therefore does
not remove its indexed content from scrutiny. Existing worktree entries,
including the policy file and site-exception targets, are inspected with
`lstat`, opened with a no-follow flag, and verified as the same regular file
after opening. A symbolic link that replaces an indexed regular file is a
policy failure; the scanner does not resolve, read, or print the link target.

GitHub documents automatic secret scanning for public repositories and
user-level push protection for supported secret patterns. That standard
service is the preferred complement to the local policy scanner because it
covers provider patterns and repository history. Maintainers should review the
repository's Security alerts and verify repository-level push-protection
settings before release; neither feature is confirmed by `make scrub`.

- [GitHub secret-scanning scope](https://docs.github.com/en/code-security/reference/secret-security/secret-scanning-scope)
- [GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection)

## Automated Check Boundaries

- `make check-assets` enforces the asset-tree allowlist plus PNG framing,
  decoding, chunk ordering, and metadata policy. These structural checks do
  not inspect visible pixels and cannot prove that a screenshot was redacted.
  A person must visually inspect every image before publication.
- `make check-placeholders` scans every line of tracked `examples/*.sbatch`
  files. In tracked Markdown it scans fenced blocks labeled `bash`, `sh`,
  `shell`, `zsh`, `console`, `shell-session`, or `sshconfig`, including
  Pandoc-style classes such as `{.bash}` and `{.shell}`. It deliberately does
  not scan indented Markdown code blocks; those remain manual-review scope to
  avoid treating ambiguous indentation as executable shell.
- Local link validation checks repository paths and anchors. A separate
  scheduled/manual workflow monitors external HTTP(S) destinations because
  network availability is unsuitable for the pull-request gate.
