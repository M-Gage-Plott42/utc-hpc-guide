# OOD Screenshot Assets

This folder contains sanitized screenshots derived from the local source guide PDF.

## Files

- `ood_desktop_request_form_sanitized.png`
  - Source: OOD Desktop request form screenshot.
  - Sanitization: partition value replaced with `<partition>`.
- `ood_session_card_sanitized.png`
  - Source: OOD session card screenshot.
  - Sanitization: compute host and created-at timestamp redacted.
- `ood_storage_shortcuts_sanitized.png`
  - Source: OOD storage shortcuts screenshot.
  - Sanitization: source already used placeholder-style username text.

## Usage Notes

- Screenshots are illustrative only; UI details vary by institution.
- Do not add unsanitized images containing usernames, hostnames, account strings, job IDs, or private paths.
- The asset-tree allowlist permits this README and lowercase
  `*_sanitized.png` files directly in `assets/ood/`; other files are rejected.
- `make check-assets` verifies that allowlist plus PNG signatures, chunk CRCs,
  required chunk ordering, decoded scanlines, filter bytes, end-of-file
  integrity, and the ancillary-chunk allowlist.
- Text, EXIF, and timestamp metadata chunks are forbidden. Re-export an asset
  rather than bypassing the privacy policy.
- These automated checks cover structure and metadata only. They do not inspect
  visible pixels or prove that sensitive content was redacted. Visually inspect
  every screenshot at readable scale before publication.
