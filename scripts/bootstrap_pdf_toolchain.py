#!/usr/bin/env python3
"""Install and verify the locked native PDF build and QA toolchain."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


USER_AGENT = "utc-hpc-guide-pdf-toolchain-bootstrap/1"
LOCK_STAMP_NAME = "lock-attestation.txt"
SHA512_CHECKSUM = re.compile(
    r"^([0-9A-Fa-f]{128})[ \t]+\*?([^ \t].*)$"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha512(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_exact_output_line(
    output: str,
    expected_line: str,
    *,
    label: str,
) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if expected_line not in lines:
        observed = lines[0] if lines else "no output"
        raise RuntimeError(
            f"{label} version mismatch; expected exact line "
            f"{expected_line!r}, observed {observed!r}"
        )
    return expected_line


def validate_signed_sha512(
    text: str,
    *,
    expected_filename: str,
    expected_digest: str,
) -> None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) != 1:
        raise RuntimeError(
            "signed TeX Live checksum must contain exactly one nonempty line"
        )
    match = SHA512_CHECKSUM.fullmatch(lines[0])
    if match is None:
        raise RuntimeError("signed TeX Live checksum has an invalid format")
    digest, filename = match.groups()
    if filename != expected_filename:
        raise RuntimeError(
            "signed TeX Live checksum names an unexpected installer: "
            f"{filename}"
        )
    if digest.casefold() != expected_digest.casefold():
        raise RuntimeError(
            "signed TeX Live checksum digest does not match the lock"
        )


def validate_texlive_installer_output(
    output: str,
    *,
    release: str,
    repository_url: str,
    scheme: str,
) -> None:
    if "(not verified)" in output:
        raise RuntimeError("TeX Live installer reported an unverified repository")
    expected = (
        f"Installing TeX Live {release} from: "
        f"{repository_url} (verified)"
    )
    lines = [line.strip() for line in output.splitlines()]
    if lines.count(expected) != 1:
        raise RuntimeError(
            "TeX Live installer did not report the exact verified repository"
        )
    fallback = re.compile(r"^No \S+, switching to scheme-\S+\.$")
    if any(fallback.fullmatch(line) for line in lines):
        raise RuntimeError(
            "TeX Live installer substituted a different scheme instead of "
            f"{scheme}"
        )


def run(
    command: list[str | Path],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(item) for item in command],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def download(url: str, destination: Path, expected_sha256: str) -> Path:
    if destination.is_file() and sha256(destination) == expected_sha256:
        print(f"download_verified cached={destination.name}")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    temporary.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    print(f"downloading url={url}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with temporary.open("wb") as handle:
                shutil.copyfileobj(response, handle)
        actual = sha256(temporary)
        if actual != expected_sha256:
            raise RuntimeError(
                f"checksum mismatch for {url}: {actual} != {expected_sha256}"
            )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"download_verified sha256={expected_sha256} file={destination.name}")
    return destination


def download_sha512(
    url: str,
    destination: Path,
    expected_sha512: str,
) -> Path:
    if destination.is_file() and sha512(destination) == expected_sha512:
        print(f"download_verified cached={destination.name}")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    temporary.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    print(f"downloading url={url}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with temporary.open("wb") as handle:
                shutil.copyfileobj(response, handle)
        actual = sha512(temporary)
        if actual != expected_sha512:
            raise RuntimeError(
                f"SHA-512 mismatch for {url}: "
                f"{actual} != {expected_sha512}"
            )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    print(
        "download_verified "
        f"sha512={expected_sha512} file={destination.name}"
    )
    return destination


def safe_extract_tar(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, "r:*") as bundle:
        bundle.extractall(destination, filter="data")


def safe_extract_zip(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as bundle:
        root = destination.resolve()
        for item in bundle.infolist():
            target = (destination / item.filename).resolve()
            if target != root and root not in target.parents:
                raise RuntimeError(
                    f"ZIP member escapes extraction directory: {item.filename}"
                )
        bundle.extractall(destination)


def fingerprints(gpg: str, keyring: Path) -> set[str]:
    result = run(
        [
            gpg,
            "--batch",
            "--homedir",
            keyring,
            "--with-colons",
            "--fingerprint",
            "--fingerprint",
        ]
    )
    return {
        line.split(":")[9]
        for line in result.stdout.splitlines()
        if line.startswith("fpr:") and len(line.split(":")) > 9
    }


def verify_signature(
    *,
    gpg: str,
    keyring: Path,
    key: Path,
    signature: Path,
    signed_file: Path,
    primary_fingerprint: str,
    signing_fingerprint: str,
) -> None:
    keyring.mkdir(parents=True, exist_ok=True)
    keyring.chmod(0o700)
    run([gpg, "--batch", "--homedir", keyring, "--import", key])
    available = fingerprints(gpg, keyring)
    if primary_fingerprint not in available:
        raise RuntimeError(
            f"required signing-key fingerprint is absent: {primary_fingerprint}"
        )
    result = run(
        [
            gpg,
            "--batch",
            "--homedir",
            keyring,
            "--status-fd=1",
            "--verify",
            signature,
            signed_file,
        ]
    )
    valid_signatures = []
    for line in result.stdout.splitlines():
        if line.startswith("[GNUPG:] VALIDSIG "):
            valid_signatures.append(line.split())
    if not any(
        len(fields) >= 12
        and fields[2] == signing_fingerprint
        and fields[-1] == primary_fingerprint
        for fields in valid_signatures
    ):
        raise RuntimeError(
            f"signature was not made by the locked key: {signed_file.name}"
        )
    print(
        "signature_verified "
        f"file={signed_file.name} signer={signing_fingerprint}"
    )


def version_output(command: list[str | Path]) -> str:
    result = run(command)
    return (result.stdout + result.stderr).strip()


def require_version(
    command: list[str | Path],
    expected_line: str,
    *,
    label: str,
) -> str:
    output = version_output(command)
    require_exact_output_line(output, expected_line, label=label)
    print(f"tool_version_verified tool={label} expected={expected_line}")
    return output


def install_single_root_tar(
    archive: Path,
    destination: Path,
) -> None:
    if destination.exists():
        raise RuntimeError(
            f"existing incomplete tool directory requires review: {destination}"
        )
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}-",
        dir=destination.parent,
    ) as temporary:
        staging = Path(temporary) / "extract"
        safe_extract_tar(archive, staging)
        children = [path for path in staging.iterdir()]
        if len(children) != 1 or not children[0].is_dir():
            raise RuntimeError(f"archive does not contain one root directory: {archive}")
        shutil.move(str(children[0]), destination)


def install_pandoc(
    lock: dict[str, Any],
    tool_root: Path,
    downloads: Path,
) -> Path:
    destination = tool_root / f"pandoc-{lock['version']}"
    executable = destination / "bin" / "pandoc"
    if executable.is_file():
        require_version(
            [executable, "--version"],
            lock["version_line"],
            label="pandoc",
        )
        return executable
    archive = download(
        lock["url"],
        downloads / Path(lock["url"]).name,
        lock["sha256"],
    )
    install_single_root_tar(archive, destination)
    require_version(
        [executable, "--version"],
        lock["version_line"],
        label="pandoc",
    )
    return executable


def install_java(
    lock: dict[str, Any],
    tool_root: Path,
    downloads: Path,
) -> tuple[Path, Path]:
    destination = tool_root / "temurin-21.0.11"
    executable = destination / "bin" / "java"
    if executable.is_file():
        output = require_version(
            [executable, "-version"],
            lock["version_line"],
            label="java",
        )
        require_exact_output_line(
            output,
            lock["runtime_line"],
            label="java runtime",
        )
        return destination, executable
    archive = download(
        lock["url"],
        downloads / Path(lock["url"]).name,
        lock["sha256"],
    )
    install_single_root_tar(archive, destination)
    output = require_version(
        [executable, "-version"],
        lock["version_line"],
        label="java",
    )
    require_exact_output_line(
        output,
        lock["runtime_line"],
        label="java runtime",
    )
    return destination, executable


def texlive_package_details(tlmgr: Path, package: str) -> dict[str, str]:
    output = version_output([tlmgr, "info", "--only-installed", package])
    details: dict[str, str] = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            details[key.strip()] = value.strip()
    return details


def validate_texlive_package_details(
    package: str,
    details: dict[str, str],
    expected: dict[str, Any],
) -> None:
    if details.get("installed") != "Yes":
        raise RuntimeError(f"required TeX Live package is absent: {package}")
    if details.get("revision") != expected["revision"]:
        raise RuntimeError(
            f"TeX Live package revision mismatch for {package}: "
            f"{details.get('revision')} != {expected['revision']}"
        )
    if "version" not in expected:
        raise ValueError(
            f"TeX Live package lock must declare version for {package}"
        )
    expected_version = expected["version"]
    if expected_version is None:
        if "cat-version" in details:
            raise RuntimeError(
                f"TeX Live package version mismatch for {package}: "
                f"unexpected catalogue version {details['cat-version']}"
            )
    elif isinstance(expected_version, str):
        if details.get("cat-version") != expected_version:
            raise RuntimeError(
                f"TeX Live package version mismatch for {package}: "
                f"{details.get('cat-version')} != {expected_version}"
            )
    else:
        raise ValueError(
            f"TeX Live package lock version must be a string or null: {package}"
        )


def verify_texlive(lock: dict[str, Any], destination: Path) -> tuple[Path, Path]:
    binary_dir = destination / "bin" / "x86_64-linux"
    lualatex = binary_dir / "lualatex"
    tlmgr = binary_dir / "tlmgr"
    output = version_output([lualatex, "--version"])
    require_exact_output_line(
        output,
        lock["lualatex_version_line"],
        label="LuaLaTeX",
    )
    with tempfile.TemporaryDirectory(prefix="utc-hpc-latex-version-") as temporary:
        probe = run(
            [
                lualatex,
                "--interaction=nonstopmode",
                "--halt-on-error",
                "--jobname=kernel-version",
                (
                    "\\documentclass{article}\\begin{document}\\makeatletter"
                    "\\typeout{LOCK-LATEX-KERNEL=\\fmtversion}\\end{document}"
                ),
            ],
            cwd=Path(temporary),
        )
    kernel_marker = f"LOCK-LATEX-KERNEL={lock['latex_kernel']}"
    require_exact_output_line(
        probe.stdout,
        kernel_marker,
        label="LaTeX kernel",
    )
    scheme_details = texlive_package_details(tlmgr, lock["scheme"])
    if scheme_details.get("installed") != "Yes":
        raise RuntimeError(
            f"locked TeX Live scheme is absent: {lock['scheme']}"
        )
    for package, expected in lock["packages"].items():
        details = texlive_package_details(tlmgr, package)
        validate_texlive_package_details(package, details, expected)
    print(
        "texlive_verified "
        f"release={lock['release']} kernel={lock['latex_kernel']} "
        f"packages={len(lock['packages'])}"
    )
    return lualatex, tlmgr


def install_texlive(
    lock: dict[str, Any],
    tool_root: Path,
    downloads: Path,
    gpg: str,
) -> tuple[Path, Path, Path]:
    destination = tool_root / "texlive2025"
    if (destination / "bin" / "x86_64-linux" / "lualatex").is_file():
        lualatex, tlmgr = verify_texlive(lock, destination)
        return destination, lualatex, tlmgr

    installer = lock["installer"]
    archive = download(
        installer["url"],
        downloads / "install-tl-unx.tar.gz",
        installer["sha256"],
    )
    checksum = download(
        installer["checksum_url"],
        downloads / "install-tl-unx.tar.gz.sha512",
        installer["checksum_sha256"],
    )
    signature = download(
        installer["signature_url"],
        downloads / "install-tl-unx.tar.gz.sha512.asc",
        installer["signature_sha256"],
    )
    key_lock = lock["signing_key"]
    key = download(
        key_lock["url"],
        downloads / "texlive.asc",
        key_lock["sha256"],
    )
    keyring = tool_root / "verification" / "texlive-gnupg"
    verify_signature(
        gpg=gpg,
        keyring=keyring,
        key=key,
        signature=signature,
        signed_file=checksum,
        primary_fingerprint=key_lock["primary_fingerprint"],
        signing_fingerprint=key_lock["signing_fingerprint"],
    )
    validate_signed_sha512(
        checksum.read_text(encoding="utf-8"),
        expected_filename=archive.name,
        expected_digest=installer["sha512"],
    )
    if sha512(archive) != installer["sha512"]:
        raise RuntimeError("TeX Live installer SHA-512 does not match the lock")
    download(
        lock["repository_database"]["url"],
        downloads / "texlive.tlpdb",
        lock["repository_database"]["sha256"],
    )

    if destination.exists():
        raise RuntimeError(
            f"existing incomplete TeX Live directory requires review: {destination}"
        )
    with tempfile.TemporaryDirectory(
        prefix=".texlive-installer-",
        dir=tool_root,
    ) as temporary:
        staging = Path(temporary) / "extract"
        safe_extract_tar(archive, staging)
        installers = list(staging.glob("*/install-tl"))
        if len(installers) != 1:
            raise RuntimeError("TeX Live archive contains an unexpected installer")
        install_env = os.environ.copy()
        install_env["TL_GNUPGHOME"] = str(keyring)
        install = run(
            [
                "perl",
                installers[0],
                "--no-interaction",
                f"--scheme={lock['scheme']}",
                "--no-doc-install",
                "--no-src-install",
                f"--texdir={destination}",
                f"--repository={lock['repository_url']}",
                "--verify-downloads",
            ],
            env=install_env,
        )
        validate_texlive_installer_output(
            install.stdout + install.stderr,
            release=lock["release"],
            repository_url=lock["repository_url"],
            scheme=lock["scheme"],
        )

    binary_dir = destination / "bin" / "x86_64-linux"
    tlmgr = binary_dir / "tlmgr"
    package_archives: list[Path] = []
    package_downloads = downloads / "texlive-packages"
    for package, specification in lock["packages"].items():
        container_sha512 = specification.get("container_sha512")
        if (
            not isinstance(container_sha512, str)
            or not re.fullmatch(r"[0-9a-f]{128}", container_sha512)
        ):
            raise RuntimeError(
                f"TeX Live package lacks a locked container SHA-512: {package}"
            )
        archive_url = (
            f"{lock['repository_url'].rstrip('/')}/archive/{package}.tar.xz"
        )
        package_archives.append(
            download_sha512(
                archive_url,
                package_downloads / f"{package}.tar.xz",
                container_sha512,
            )
        )
    package_env = os.environ.copy()
    package_env["TL_GNUPGHOME"] = str(keyring)
    run(
        [
            tlmgr,
            "install",
            "--file",
            "--force",
            "--no-depends",
            *package_archives,
        ],
        env=package_env,
    )
    lualatex, tlmgr = verify_texlive(lock, destination)
    return destination, lualatex, tlmgr


def install_verapdf(
    lock: dict[str, Any],
    tool_root: Path,
    downloads: Path,
    gpg: str,
    java_home: Path,
) -> Path:
    destination = tool_root / f"verapdf-{lock['version']}"
    executable = destination / "verapdf"
    java = java_home / "bin" / "java"
    vera_env = os.environ.copy()
    vera_env["JAVA_HOME"] = str(java_home)
    vera_env["PATH"] = f"{java.parent}{os.pathsep}{vera_env.get('PATH', '')}"
    if executable.is_file():
        output = run([executable, "--version"], env=vera_env)
        observed = output.stdout + output.stderr
        require_exact_output_line(
            observed,
            lock["version_line"],
            label="veraPDF",
        )
        print(
            "tool_version_verified tool=verapdf "
            f"expected={lock['version_line']}"
        )
        return executable

    archive = download(
        lock["url"],
        downloads / Path(lock["url"]).name,
        lock["sha256"],
    )
    signature = download(
        lock["signature_url"],
        downloads / (Path(lock["url"]).name + ".asc"),
        lock["signature_sha256"],
    )
    key_lock = lock["signing_key"]
    key = download(
        key_lock["url"],
        downloads / "verapdf-release.asc",
        key_lock["sha256"],
    )
    keyring = tool_root / "verification" / "verapdf-gnupg"
    verify_signature(
        gpg=gpg,
        keyring=keyring,
        key=key,
        signature=signature,
        signed_file=archive,
        primary_fingerprint=key_lock["primary_fingerprint"],
        signing_fingerprint=key_lock["signing_fingerprint"],
    )

    with tempfile.TemporaryDirectory(
        prefix=".verapdf-installer-",
        dir=tool_root,
    ) as temporary:
        staging = Path(temporary) / "extract"
        safe_extract_zip(archive, staging)
        installers = list(staging.glob("*/verapdf-install"))
        if len(installers) != 1:
            raise RuntimeError("veraPDF archive contains an unexpected installer")
        auto_install = Path(temporary) / "auto-install.xml"
        auto_install.write_text(
            (
                '<AutomatedInstallation langpack="eng">\n'
                '  <com.izforge.izpack.panels.htmlhello.HTMLHelloPanel '
                'id="welcome"/>\n'
                '  <com.izforge.izpack.panels.target.TargetPanel '
                'id="install_dir">\n'
                f"    <installpath>{destination}</installpath>\n"
                "  </com.izforge.izpack.panels.target.TargetPanel>\n"
                '  <com.izforge.izpack.panels.packs.PacksPanel '
                'id="sdk_pack_select">\n'
                '    <pack index="0" name="veraPDF GUI" selected="false"/>\n'
                '    <pack index="1" name="veraPDF CLI" selected="true"/>\n'
                '    <pack index="2" name="veraPDF Documentation" '
                'selected="false"/>\n'
                '    <pack index="3" name="veraPDF Sample Plugins" '
                'selected="false"/>\n'
                "  </com.izforge.izpack.panels.packs.PacksPanel>\n"
                '  <com.izforge.izpack.panels.install.InstallPanel id="install"/>\n'
                '  <com.izforge.izpack.panels.finish.FinishPanel id="finish"/>\n'
                "</AutomatedInstallation>\n"
            ),
            encoding="utf-8",
        )
        run(["sh", installers[0], auto_install], env=vera_env)
    output = run([executable, "--version"], env=vera_env)
    require_exact_output_line(
        output.stdout + output.stderr,
        lock["version_line"],
        label="veraPDF",
    )
    print(
        "tool_version_verified tool=verapdf "
        f"expected={lock['version_line']}"
    )
    return executable


def parse_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]
        values[key] = value
    return values


def verify_host_packages(
    host_lock: dict[str, str],
    package_lock: dict[str, str],
) -> None:
    observed_os = parse_os_release()
    if observed_os.get("ID") != host_lock["os_id"]:
        raise RuntimeError(
            "locked PDF host OS mismatch; expected "
            f"{host_lock['os_id']}, observed {observed_os.get('ID')}"
        )
    if observed_os.get("VERSION_ID") != host_lock["version_id"]:
        raise RuntimeError(
            "locked PDF host version mismatch; expected "
            f"{host_lock['version_id']}, "
            f"observed {observed_os.get('VERSION_ID')}"
        )
    dpkg_query = shutil.which("dpkg-query")
    if not dpkg_query:
        raise RuntimeError("dpkg-query is required to verify host QA packages")
    for package, expected in package_lock.items():
        observed = version_output(
            [dpkg_query, "-W", "-f=${Version}", package]
        )
        if observed != expected:
            raise RuntimeError(
                f"host QA package mismatch for {package}: "
                f"{observed!r} != {expected!r}"
            )
    print(
        "host_packages_verified "
        f"os={host_lock['os_id']} version={host_lock['version_id']} "
        f"packages={len(package_lock)}"
    )


def verify_qa_tools(lock: dict[str, Any]) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for name, specification in lock.items():
        executable = shutil.which(name)
        if not executable:
            raise RuntimeError(f"required locked host QA tool is unavailable: {name}")
        require_version(
            [executable, *specification["arguments"]],
            specification["version_line"],
            label=name,
        )
        resolved[name] = Path(executable)
    return resolved


def replace_link(link: Path, target: Path) -> None:
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(target)


def write_lualatex_wrapper(
    wrapper: Path,
    lualatex: Path,
    texlive_root: Path,
) -> None:
    font_directory = (
        texlive_root
        / "texmf-dist"
        / "fonts"
        / "truetype"
        / "public"
        / "dejavu"
    )
    if not font_directory.is_dir():
        raise RuntimeError(f"locked DejaVu font directory is absent: {font_directory}")
    wrapper.write_text(
        (
            "#!/bin/sh\n"
            f"export OSFONTDIR='{font_directory}'\n"
            f"exec '{lualatex}' \"$@\"\n"
        ),
        encoding="utf-8",
    )
    wrapper.chmod(0o755)


def validate_lock_stamp(tool_root: Path, lock_digest: str) -> None:
    if not tool_root.exists():
        return
    entries = list(tool_root.iterdir())
    if not entries:
        return
    stamp = tool_root / LOCK_STAMP_NAME
    try:
        mode = stamp.lstat().st_mode
    except FileNotFoundError as exc:
        raise RuntimeError(
            "existing PDF toolchain cache is not attested to this lock; "
            "move it aside and bootstrap again"
        ) from exc
    if not stat.S_ISREG(mode):
        raise RuntimeError("PDF toolchain lock attestation must be a regular file")
    expected = f"lock_sha256={lock_digest}\n"
    if stamp.read_text(encoding="utf-8") != expected:
        raise RuntimeError(
            "PDF toolchain cache was created from a different lock; "
            "move it aside and bootstrap again"
        )


def write_lock_stamp(tool_root: Path, lock_digest: str) -> None:
    stamp = tool_root / LOCK_STAMP_NAME
    temporary = tool_root / f".{LOCK_STAMP_NAME}.partial"
    temporary.unlink(missing_ok=True)
    temporary.write_text(
        f"lock_sha256={lock_digest}\n",
        encoding="utf-8",
    )
    os.replace(temporary, stamp)


def install_toolchain(
    lock: dict[str, Any],
    tool_root: Path,
    lock_path: Path,
) -> None:
    if lock.get("schema_version") != 1:
        raise ValueError("PDF toolchain lock schema_version must be 1")
    if lock.get("platform") != "linux-x86_64":
        raise ValueError("PDF toolchain lock platform must be linux-x86_64")
    host_lock = lock.get("host")
    if (
        not isinstance(host_lock, dict)
        or not isinstance(host_lock.get("os_id"), str)
        or not isinstance(host_lock.get("version_id"), str)
    ):
        raise ValueError("PDF toolchain lock must declare its host OS")
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("the locked PDF toolchain requires Linux x86_64")

    lock_digest = sha256(lock_path)
    validate_lock_stamp(tool_root, lock_digest)
    verify_host_packages(
        host_lock,
        lock["ubuntu_24_04_qa_packages"],
    )
    gpg = shutil.which("gpg")
    if not gpg:
        raise RuntimeError("GnuPG is required to verify signed PDF tools")
    tool_root.mkdir(parents=True, exist_ok=True)
    downloads = tool_root / "downloads"
    pandoc = install_pandoc(lock["pandoc"], tool_root, downloads)
    java_home, java = install_java(lock["java"], tool_root, downloads)
    texlive_root, lualatex, tlmgr = install_texlive(
        lock["texlive"],
        tool_root,
        downloads,
        gpg,
    )
    verapdf = install_verapdf(
        lock["verapdf"],
        tool_root,
        downloads,
        gpg,
        java_home,
    )
    qa_tools = verify_qa_tools(lock["qa_tools"])

    binary_dir = tool_root / "bin"
    binary_dir.mkdir(parents=True, exist_ok=True)
    replace_link(binary_dir / "pandoc", pandoc)
    replace_link(binary_dir / "java", java)
    replace_link(binary_dir / "verapdf", verapdf)
    replace_link(binary_dir / "tlmgr", tlmgr)
    replace_link(
        binary_dir / "kpsewhich",
        texlive_root / "bin" / "x86_64-linux" / "kpsewhich",
    )
    write_lualatex_wrapper(binary_dir / "lualatex", lualatex, texlive_root)
    for name, executable in qa_tools.items():
        replace_link(binary_dir / name, executable)
    write_lock_stamp(tool_root, lock_digest)
    print(
        "pdf_toolchain_ready "
        f"root={tool_root} bin={binary_dir} "
        f"lock_sha256={lock_digest}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("pdf/toolchain.lock.json"),
    )
    parser.add_argument("--root", type=Path, default=Path(".cache/pdf-toolchain"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        lock_data = json.loads(arguments.lock.read_text(encoding="utf-8"))
        install_toolchain(
            lock_data,
            arguments.root.resolve(),
            arguments.lock.resolve(),
        )
    except (
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
        tarfile.TarError,
        urllib.error.URLError,
        zipfile.BadZipFile,
    ) as exc:
        print(f"ERROR: PDF toolchain bootstrap failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
