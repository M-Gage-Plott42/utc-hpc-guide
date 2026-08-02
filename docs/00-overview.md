# 00 Overview

This guide provides a Python-first path for onboarding to an HPC environment using:

- SSH for terminal access
- Open OnDemand (OOD) for interactive sessions
- Slurm for CPU/GPU scheduling
- Reproducible Python environments for batch workflows

Slurm is the cluster workload manager and job scheduler that allocates compute
resources and queues jobs. Here, HPC means high-performance computing, SSH is
the Secure Shell protocol, OOD is Open OnDemand, and CPU and GPU mean central
processing unit and graphics processing unit, respectively.

## Audience

- New HPC users who need a concrete first workflow
- Returning users who want clean templates and checklists
- Reviewers evaluating reproducibility and operational hygiene

## What This Guide Assumes

- You have an HPC account and cluster access permission
- You can access the cluster network directly or through VPN
- You can run basic shell commands

## Workflow Map

1. Confirm account and network access.
2. Test SSH login to the cluster login host.
3. Launch an interactive session (SSH `srun --pty` or OOD).
4. Build a Python environment in site-approved project/software storage, or
   use scratch only when its retention policy supports a rebuildable
   environment.
5. Submit CPU/GPU jobs with `sbatch`.
6. Monitor jobs, inspect logs, iterate.

## Source of Truth Rule

Cluster policies and capacity change over time. Treat this repository as a practical baseline, then confirm details using:

- Your institution's official HPC documentation
- Live cluster commands such as `sinfo`, `scontrol`, and `squeue`

## Placeholder Convention

Replace these with site-specific values:

- `<username>`
- `<login-host>`
- `<cpu-partition>`
- `<gpu-partition>`
- `<account>`
- `<home-path>`
- `<scratch-path>`
- `<project-path>`

Angle-bracket placeholders are prose and path notation, not literal shell
input. Runnable shell examples use `REPLACE_WITH_*` markers because unquoted
angle brackets are shell redirection operators.
