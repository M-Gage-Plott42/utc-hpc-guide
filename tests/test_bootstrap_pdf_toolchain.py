from __future__ import annotations

import io
import json
import re
import tempfile
import unittest
import urllib.error
from pathlib import Path

from scripts.bootstrap_pdf_toolchain import (
    LOCK_STAMP_NAME,
    download_to_temporary,
    require_exact_output_line,
    validate_lock_stamp,
    validate_signed_sha512,
    validate_texlive_package_details,
    validate_texlive_installer_output,
    write_lock_stamp,
)


SHA512 = "a" * 128
INSTALLER = "install-tl-unx.tar.gz"
REPOSITORY = (
    "https://ftp.tu-chemnitz.de/pub/tug/historic/"
    "systems/texlive/2025/tlnet-final"
)
ROOT = Path(__file__).resolve().parents[1]


class DownloadRetryTests(unittest.TestCase):
    def test_retries_timeout_then_replaces_partial_content(self) -> None:
        attempts = 0

        def opener(_request: object, *, timeout: int) -> io.BytesIO:
            nonlocal attempts
            attempts += 1
            self.assertEqual(timeout, 7)
            if attempts == 1:
                raise urllib.error.URLError(TimeoutError("timed out"))
            return io.BytesIO(b"complete")

        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "download.partial"
            destination.write_bytes(b"stale")
            delays: list[float] = []
            download_to_temporary(
                "https://example.test/artifact",
                destination,
                attempts=3,
                timeout=7,
                opener=opener,
                sleeper=delays.append,
            )
            self.assertEqual(destination.read_bytes(), b"complete")

        self.assertEqual(attempts, 2)
        self.assertEqual(delays, [1.0])

    def test_retries_retryable_http_status(self) -> None:
        responses: list[object] = [
            urllib.error.HTTPError(
                "https://example.test/artifact",
                503,
                "Service Unavailable",
                None,
                None,
            ),
            io.BytesIO(b"complete"),
        ]

        def opener(_request: object, *, timeout: int) -> io.BytesIO:
            self.assertEqual(timeout, 60)
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "download.partial"
            delays: list[float] = []
            download_to_temporary(
                "https://example.test/artifact",
                destination,
                opener=opener,
                sleeper=delays.append,
            )
            self.assertEqual(destination.read_bytes(), b"complete")

        self.assertEqual(delays, [1.0])

    def test_does_not_retry_nonretryable_http_status(self) -> None:
        attempts = 0

        def opener(_request: object, *, timeout: int) -> io.BytesIO:
            nonlocal attempts
            attempts += 1
            self.assertEqual(timeout, 60)
            raise urllib.error.HTTPError(
                "https://example.test/missing",
                404,
                "Not Found",
                None,
                None,
            )

        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "download.partial"
            with self.assertRaises(urllib.error.HTTPError):
                download_to_temporary(
                    "https://example.test/missing",
                    destination,
                    opener=opener,
                    sleeper=lambda _delay: self.fail("unexpected retry"),
                )
            self.assertFalse(destination.exists())

        self.assertEqual(attempts, 1)


class ExactVersionTests(unittest.TestCase):
    def test_accepts_exact_version_line(self) -> None:
        self.assertEqual(
            require_exact_output_line(
                "pandoc 3.10.1\nFeatures: +server +lua\n",
                "pandoc 3.10.1",
                label="Pandoc",
            ),
            "pandoc 3.10.1",
        )

    def test_rejects_longer_version_with_locked_prefix(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "expected exact line"):
            require_exact_output_line(
                "pandoc 3.10.10\n",
                "pandoc 3.10.1",
                label="Pandoc",
            )


class SignedChecksumTests(unittest.TestCase):
    def test_accepts_one_exact_signed_checksum(self) -> None:
        validate_signed_sha512(
            f"{SHA512}  {INSTALLER}\n",
            expected_filename=INSTALLER,
            expected_digest=SHA512,
        )

    def test_rejects_digest_not_bound_to_lock(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "digest does not match"):
            validate_signed_sha512(
                f"{'b' * 128}  {INSTALLER}\n",
                expected_filename=INSTALLER,
                expected_digest=SHA512,
            )

    def test_every_direct_tex_package_has_a_locked_container_digest(self) -> None:
        lock = json.loads(
            (ROOT / "pdf/toolchain.lock.json").read_text(encoding="utf-8")
        )
        for package, specification in lock["texlive"]["packages"].items():
            with self.subTest(package=package):
                self.assertRegex(
                    specification["container_sha512"],
                    re.compile(r"^[0-9a-f]{128}$"),
                )

    def test_every_texlive_download_uses_one_https_repository(self) -> None:
        lock = json.loads(
            (ROOT / "pdf/toolchain.lock.json").read_text(encoding="utf-8")
        )
        texlive = lock["texlive"]
        urls = [
            texlive["repository_url"],
            texlive["repository_database"]["url"],
            texlive["installer"]["url"],
            texlive["installer"]["checksum_url"],
            texlive["installer"]["signature_url"],
        ]
        self.assertEqual(texlive["repository_url"], REPOSITORY)
        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(
                    url.startswith(REPOSITORY + "/") or url == REPOSITORY
                )
                self.assertTrue(url.startswith("https://"))

    def test_rejects_unexpected_installer_name(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unexpected installer"):
            validate_signed_sha512(
                f"{SHA512}  other.tar.gz\n",
                expected_filename=INSTALLER,
                expected_digest=SHA512,
            )

    def test_rejects_extra_checksum_lines(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            validate_signed_sha512(
                f"{SHA512}  {INSTALLER}\n{SHA512}  other.tar.gz\n",
                expected_filename=INSTALLER,
                expected_digest=SHA512,
            )


class InstallerVerificationTests(unittest.TestCase):
    def verified_output(self) -> str:
        return (
            "Trying to verify cryptographic signatures!\n"
            f"Installing TeX Live 2025 from: {REPOSITORY} (verified)\n"
            "Platform: x86_64-linux\n"
        )

    def test_accepts_exact_verified_repository_marker(self) -> None:
        validate_texlive_installer_output(
            self.verified_output(),
            release="2025",
            repository_url=REPOSITORY,
            scheme="scheme-small",
        )

    def test_rejects_not_verified_marker(self) -> None:
        output = self.verified_output().replace(
            "(verified)",
            "(not verified)",
        )
        with self.assertRaisesRegex(RuntimeError, "unverified"):
            validate_texlive_installer_output(
                output,
                release="2025",
                repository_url=REPOSITORY,
                scheme="scheme-small",
            )

    def test_rejects_missing_exact_verified_marker(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "exact verified"):
            validate_texlive_installer_output(
                "repository verified\n",
                release="2025",
                repository_url=REPOSITORY,
                scheme="scheme-small",
            )

    def test_rejects_scheme_substitution(self) -> None:
        output = (
            self.verified_output()
            + "No scheme-small, switching to scheme-minimal.\n"
        )
        with self.assertRaisesRegex(RuntimeError, "different scheme"):
            validate_texlive_installer_output(
                output,
                release="2025",
                repository_url=REPOSITORY,
                scheme="scheme-small",
            )


class TexLivePackageVerificationTests(unittest.TestCase):
    def test_accepts_exact_string_catalogue_version(self) -> None:
        validate_texlive_package_details(
            "dejavu",
            {
                "installed": "Yes",
                "revision": "77677",
                "cat-version": "2.34",
            },
            {"revision": "77677", "version": "2.34"},
        )

    def test_accepts_absent_catalogue_version_when_lock_is_null(self) -> None:
        validate_texlive_package_details(
            "noto",
            {"installed": "Yes", "revision": "77677"},
            {"revision": "77677", "version": None},
        )

    def test_rejects_catalogue_version_when_lock_is_null(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unexpected catalogue version"):
            validate_texlive_package_details(
                "noto",
                {
                    "installed": "Yes",
                    "revision": "77677",
                    "cat-version": "2025.01.01",
                },
                {"revision": "77677", "version": None},
            )

    def test_rejects_missing_catalogue_version_for_string_lock(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "version mismatch"):
            validate_texlive_package_details(
                "dejavu",
                {"installed": "Yes", "revision": "77677"},
                {"revision": "77677", "version": "2.34"},
            )

    def test_rejects_missing_explicit_version_lock(self) -> None:
        with self.assertRaisesRegex(ValueError, "must declare version"):
            validate_texlive_package_details(
                "noto",
                {"installed": "Yes", "revision": "77677"},
                {"revision": "77677"},
            )

    def test_lock_records_noto_without_catalogue_version(self) -> None:
        lock = json.loads(
            (ROOT / "pdf/toolchain.lock.json").read_text(encoding="utf-8")
        )
        noto = lock["texlive"]["packages"]["noto"]
        self.assertEqual(noto["revision"], "77677")
        self.assertIsNone(noto["version"])
        self.assertEqual(
            noto["container_sha512"],
            "2e94b1490e1682391f66fe03ca46a70d2fa697eb71ae02b6d675a7b71b42c94e"
            "449f846fe459f3fd873450b1de5fd022bde96d8a96bb82e14db545800ccee5a6",
        )


class LockStampTests(unittest.TestCase):
    def test_accepts_absent_or_matching_attested_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "toolchain"
            validate_lock_stamp(root, "1" * 64)
            root.mkdir()
            validate_lock_stamp(root, "1" * 64)
            write_lock_stamp(root, "1" * 64)
            validate_lock_stamp(root, "1" * 64)

    def test_rejects_unattested_existing_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "toolchain"
            root.mkdir()
            (root / "pandoc").mkdir()
            with self.assertRaisesRegex(RuntimeError, "not attested"):
                validate_lock_stamp(root, "1" * 64)

    def test_rejects_cache_from_different_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "toolchain"
            root.mkdir()
            write_lock_stamp(root, "1" * 64)
            with self.assertRaisesRegex(RuntimeError, "different lock"):
                validate_lock_stamp(root, "2" * 64)

    def test_rejects_symlink_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "toolchain"
            root.mkdir()
            target = Path(temporary) / "outside"
            target.write_text("lock_sha256=" + "1" * 64 + "\n", encoding="utf-8")
            (root / LOCK_STAMP_NAME).symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, "regular file"):
                validate_lock_stamp(root, "1" * 64)


if __name__ == "__main__":
    unittest.main()
