# UTC HPC Guide Repo Implementation Plan

## 1) Directory and Repository Name
- Working directory in this machine: `<your-git-root>/utc-hpc-guide`
- Proposed GitHub repo name: `utc-hpc-guide`
- Rationale: direct, discoverable, and consistent with your source context while still easy to sanitize for public use.

## 2) Phase 1: Scaffold and Hygiene
- Initialize git repo in `utc-hpc-guide`.
- Add baseline files:
  - `README.md`
  - `LICENSE` (MIT recommended; Apache-2.0 optional)
  - `.gitignore` (Python + docs/editor hygiene)
  - `SECURITY.md` with scrub guidance
- Create structure:
  - `docs/`
  - `examples/`
  - `assets/` (optional)

## 3) Phase 2: Documentation Conversion
- Split your guide into:
  - `docs/00-overview.md`
  - `docs/01-access-ssh.md`
  - `docs/02-open-ondemand.md`
  - `docs/03-slurm-basics.md`
  - `docs/04-gpu-jobs.md`
  - `docs/05-python-envs.md`
  - `docs/06-data-transfer.md`
  - `docs/07-troubleshooting.md`
  - `docs/08-best-practices.md`
- Rewrite any institution-specific text into generic placeholders.
- Keep sections short, practical, and command-oriented.

## 4) Phase 3: Runnable Example Jobs
- Add:
  - `examples/slurm_cpu_example.sbatch`
  - `examples/slurm_gpu_example.sbatch`
  - `examples/job_array_example.sbatch`
- Include inline comments explaining each SLURM directive.
- Use placeholders for partition/account/QOS; avoid site-specific names.

## 5) Phase 4: Reviewer-Friendly README
- README sections:
  - Purpose
  - Intended audience
  - What the repo demonstrates
  - Quickstart navigation to `docs/*`
  - "No assumptions" note (general SLURM/OOD/SSH)
  - Disclaimer: not official HPC admin documentation
  - `Last updated: February 2026`

## 6) Phase 5: Scrub and Release Checks
- Search for sensitive/internal info before first public push:
  - Emails, usernames, phone numbers
  - Hostnames/login node names
  - Allocation/account/project IDs
  - Paths with personal identifiers
- Suggested checks:
  - `rg -n "@|/home/|utc|login|partition|account|project|allocation" .`
  - Manual screenshot review under `assets/`

## 7) Phase 6: GitHub Publish Flow
- Create public GitHub repo `utc-hpc-guide` with:
  - Public visibility
  - README enabled (or push local README)
  - Python `.gitignore`
  - MIT license
- Push via SSH remote (token/auth already available in this WSL environment).

## 8) Phase 7: LANL Materials Update
- Current statement: "public GitHub release in progress" (v14).
- After publish, update to actual URL in next revision (v15) plus one-line proof statement.

## Strictly Needed Inputs for First Pass
- Required from you:
  - The current HPC guide source content (raw text/notes/doc) to convert into `docs/*`.
- Not strictly required right now:
  - Screenshots (`assets/`) - optional
  - Final repo description wording - can be refined later
  - Final license choice between MIT/Apache-2.0 (default MIT unless you prefer Apache-2.0)
