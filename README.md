# UTC HPC Guide

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Quality Gate](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/quality.yml/badge.svg)](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/quality.yml)
[![Markdown Lint](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/markdown-lint.yml/badge.svg)](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/markdown-lint.yml)
[![Shell Lint](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/shell-lint.yml/badge.svg)](https://github.com/M-Gage-Plott42/utc-hpc-guide/actions/workflows/shell-lint.yml)

Practical HPC onboarding and workflows guide (SLURM + Open OnDemand + SSH + Python-first tooling).  
Originally developed for a university research environment and sanitized for public release.

Last updated: February 2026

## How to Use This Repo in 15 Minutes

1. Read [Overview](docs/00-overview.md), [Access and SSH](docs/01-access-ssh.md), and [SLURM Basics](docs/03-slurm-basics.md).
2. Review runnable templates in `examples/` and adapt placeholders (`<username>`, `<cpu-partition>`, `<gpu-partition>`, `<account>`).
3. Run quality checks from repo root:

```bash
make check
```

This runs markdown linting, strict-fail scrub checks, asset hygiene checks, and local Markdown link validation.

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

## Runnable Examples

- [CPU batch script](examples/slurm_cpu_example.sbatch)
- [GPU batch script](examples/slurm_gpu_example.sbatch)
- [Job array script](examples/job_array_example.sbatch)

## No Assumptions

This guide is intentionally general and works as a baseline SLURM/OOD/SSH guide. Replace placeholders such as
`<username>`, `<login-host>`, `<cpu-partition>`, `<gpu-partition>`, and `<account>` with your institution values.

## Security

See [SECURITY.md](SECURITY.md).  
Do not commit credentials, usernames, internal hostnames, or allocation IDs.

## Release Workflow

- [Changelog](CHANGELOG.md)
- [Public release checklist](RELEASE_CHECKLIST.md)
- [Agent guidance](AGENTS.md)
- [Contributing guide](CONTRIBUTING.md)

## Disclaimer

This is not official HPC administrator documentation.  
Always verify limits, partitions, software, and policies using your institution's official docs and live cluster commands.
