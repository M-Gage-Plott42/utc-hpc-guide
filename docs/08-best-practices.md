# 08 Best Practices

Operational habits that make HPC workflows reproducible and reviewer-friendly.

## 1. Reproducibility Baseline

- Keep sbatch scripts under version control
- Pin Python/package versions
- Record commit SHA and runtime arguments for each run
- Save environment metadata (`python --version`, `pip freeze`, or conda export)
- Keep deterministic seeds where applicable

## 2. Scheduler Etiquette

- Request only needed cores, memory, wall time, and GPUs from measured baseline jobs
- Start with small test jobs before scaling
- Poll `squeue`/`sacct` at low frequency (for example every 30-60 seconds), not tight loops
- Cancel stale or failed jobs quickly
- Prefer batch execution for heavy workloads over login nodes

## 3. Storage and Placement Hygiene

- Keep Home focused on source code, configs, and lightweight metadata
- Keep large datasets, environments, checkpoints, and logs in Scratch/project space
- Stage data where jobs run to reduce unnecessary filesystem traffic
- Archive or prune stale outputs to stay within quota and retention policies

## 4. Security and Privacy Hygiene

- Never commit credentials or tokens
- Replace personal or internal identifiers with placeholders
- Sanitize screenshots before publishing
- Run a scrub pass before every public release

Suggested scrub command:

```bash
rg -n "@|/home/|login|partition|account|allocation|project|token|secret" .
```

## 5. Minimal End-to-End Workflow

1. Connect to cluster network (VPN if needed).
2. SSH to login host.
3. Create environment in scratch/project space.
4. Validate with a small interactive or short batch job.
5. Submit production job with sbatch.
6. Monitor with `squeue`/`sacct`, then archive outputs.

## 6. Public-Release Checklist

- Confirm no internal hostnames or usernames remain
- Confirm no allocation IDs or account strings remain
- Confirm examples use placeholders only
- Confirm README disclaimer and "Last updated" are current
- Confirm `make check` passes in clean working tree state
