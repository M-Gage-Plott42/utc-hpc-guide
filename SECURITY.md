# Security Policy

Do not commit credentials, usernames, internal hostnames, or allocation IDs.

Additional guidance:

- Keep secrets in environment variables or a secrets manager, never in git.
- Sanitize screenshots before adding them to `assets/`.
- Replace institution-specific identifiers with placeholders in public docs.
- Review changes with a scrub pass before each public push.
