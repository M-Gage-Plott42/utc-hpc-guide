# UTC HPC Guide

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Quality Gate](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/quality.yml/badge.svg)](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/quality.yml)
[![Shell Lint](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/shell-lint.yml/badge.svg)](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/shell-lint.yml)
[![PDF Guide](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/pdf.yml/badge.svg)](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/pdf.yml)
[![Dependency Review](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/dependency-review.yml)

Practical HPC onboarding and workflows guide (SLURM + Open OnDemand + SSH + Python-first tooling).  
Originally developed for a university research environment and sanitized for public release.

Last updated: July 2026

[Download the latest printable PDF](https://github.com/M-Gage-Plott42/utc-hpc-guide/releases/latest/download/UTC_HPC_Guide.pdf)
or review the [PDF build and validation instructions](docs/pdf-guide.md).
The stable download remains `v1.2.0`; `v1.2.1-rc.2` workflow artifacts are
review candidates and are not for redistribution.

## How to Use This Repo in 15 Minutes

1. Read [Overview](docs/00-overview.md), [Access and SSH](docs/01-access-ssh.md), and [SLURM Basics](docs/03-slurm-basics.md).
2. Review runnable templates in `examples/` and adapt the documented placeholders.
3. Install the locked local quality toolchain and run checks from repo root:

```bash
npm ci
make check
```

`npm ci` installs the exact versions in `package-lock.json`. `make check` uses
only the repository-local Markdown linter, then runs all-tracked-text scrub
checks, scrub failure-path tests, asset hygiene checks, parser-based local
link, reference-link, and heading-anchor validation, and link-parser
failure-path tests. It also rejects angle-bracket placeholders in shell
snippets and runnable templates.

For a release-affecting change, install ShellCheck, use the documented Ubuntu
24.04 x86_64 host, bootstrap the locked PDF toolchain, and run the complete
local gate:

```bash
npm ci
make setup-pdf-tools
make release-check
```

`make release-check` adds per-file Bash syntax checks, ShellCheck, a
byte-identical tagged-PDF build, structural and PDF/UA-2 machine validation,
rendering and every-page OCR QA, and staged/unstaged whitespace checks to the
routine gate. Automated PDF/UA validation is not a WCAG 2.1 AA certification;
manual accessibility review remains required. Dependency audits and other
network-dependent checks remain separate.

## Purpose

This repository is a documentation-first guide for new and intermediate HPC users who need a reliable baseline for:

- Accessing a cluster with SSH (and optional IDE remote workflows)
- Launching interactive sessions with Open OnDemand (OOD)
- Running reproducible CPU/GPU jobs with SLURM
- Building stable Python environments on shared systems

## Who This Is For

- Students and researchers starting on a SLURM-managed cluster
- Engineers who want simple, reusable sbatch templates
- Reviewers who need clear, reproducible onboarding documentation

## What This Demonstrates

- End-to-end workflow from access setup to production-style job submission
- Cluster-agnostic patterns with placeholders (no site-specific accounts, hosts, or partitions)
- Security-minded documentation practices for public release

## Quickstart Navigation

- [Overview](docs/00-overview.md)
- [Access and SSH](docs/01-access-ssh.md)
- [Open OnDemand](docs/02-open-ondemand.md)
- [SLURM Basics](docs/03-slurm-basics.md)
- [GPU Jobs](docs/04-gpu-jobs.md)
- [Python Environments](docs/05-python-envs.md)
- [Data Transfer and Storage](docs/06-data-transfer.md)
- [Troubleshooting](docs/07-troubleshooting.md)
- [Best Practices](docs/08-best-practices.md)
- [Printable PDF Guide](docs/pdf-guide.md)

Site-specific notes:

- [UTC MocsHPC](docs/sites/utc-mocshpc.md)

## Runnable Examples

- [CPU batch script](examples/slurm_cpu_example.sbatch)
- [GPU batch script](examples/slurm_gpu_example.sbatch)
- [Job array script](examples/job_array_example.sbatch)
- [TensorFlow GPU probe](examples/slurm_tensorflow_gpu_probe.sbatch)

## No Assumptions

This guide is intentionally general and works as a baseline SLURM/OOD/SSH guide. Replace placeholders such as
`<username>`, `<login-host>`, `<cpu-partition>`, `<gpu-partition>`, `<account>`, `<home-path>`,
`<scratch-path>`, and `<project-path>` with your institution values.
Site-specific notes, when present, are isolated under `docs/sites/` and should be verified against official institutional documentation.

## Security

See [SECURITY.md](SECURITY.md).  
Do not commit credentials, usernames, internal hostnames, or allocation IDs.

## Release Workflow

- [Changelog](CHANGELOG.md)
- [Public release checklist](RELEASE_CHECKLIST.md)
- [Agent guidance](AGENTS.md)
- [Contributing guide](CONTRIBUTING.md)

## GitHub automation

- Required workflows now use workflow-level concurrency and `merge_group`
  triggers so checks stay stable on pull requests and merge queues.
- The Quality Gate is the single Markdown-lint authority and uses the locked
  repository-local toolchain.
- PDF workflow runs upload the validated review candidate,
  `build-toolchain.txt`, and `verapdf-report.xml` together for short-lived
  review traceability. `pdf/toolchain.lock.json` pins the declared PDF
  toolchain inputs; the run record describes the observed build and is not
  signed provenance or a permanent archive.
- External HTTP(S) links are monitored only on a schedule or manual dispatch,
  with retries, timeouts, and an exact reasoned allowlist; network availability
  does not gate ordinary pull requests.
- Dependency review runs by default on public repos and can be enabled for
  private copies later with `ENABLE_DEPENDENCY_REVIEW=true` once GitHub Code
  Security or GHAS is available.

## Disclaimer

This is not official HPC administrator documentation.  
Always verify limits, partitions, software, and policies using your institution's official docs and live cluster commands.
