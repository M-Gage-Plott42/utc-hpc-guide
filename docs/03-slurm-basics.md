# 03 SLURM Basics

SLURM allocates compute resources for interactive and batch workloads.

## 1. Two Primary Modes

- `sbatch`: submit a script for non-interactive execution
- `srun --pty`: start an interactive shell on allocated resources

## 2. Quick Interactive CPU Session

```bash
CPU_PARTITION="REPLACE_WITH_CPU_PARTITION"
ACCOUNT="REPLACE_WITH_ACCOUNT"
srun \
  --partition="$CPU_PARTITION" \
  --account="$ACCOUNT" \
  --nodes=1 \
  --ntasks=1 \
  --cpus-per-task=4 \
  --mem=8G \
  --time=0-01:00:00 \
  --pty /bin/bash -l
```

Then verify:

```bash
hostname
nproc
```

## 3. Important: `#SBATCH` Parsing Behavior

`#SBATCH` directives are parsed by `sbatch` before the shell executes your script body.
Do not rely on shell variable expansion inside `#SBATCH` lines.
Use explicit values/placeholders in directives, or pass dynamic values using `sbatch` CLI flags.

## 4. Submit a Batch Job

Use a script such as `examples/slurm_cpu_example.sbatch`:

```bash
sbatch examples/slurm_cpu_example.sbatch
```

## 5. Monitor and Inspect Jobs

```bash
JOB_ID="REPLACE_WITH_JOB_ID"
squeue -u "$USER"
sacct -j "$JOB_ID" \
  --format=JobID,JobName,Partition,ReqMem,AllocTRES,AllocCPUS,Elapsed,State,ExitCode,MaxRSS
```

`sacct` normally prints a primary row for the whole job and separate rows for
job steps such as `.batch` and `.extern`. Interpret the fields at the level
where Slurm records them:

- `ReqMem` comes from the job allocation, not an individual step.
- `MaxRSS` is the largest resident-memory high-water mark reported for one
  task in a job step. It may be blank on the whole-job row.
- Read `State`, `ExitCode`, `ReqMem`, and the populated step-level `MaxRSS`
  values together when debugging failures.

Site-local tools such as `jobstats`, `seff`, or reporting dashboards may
present the same resource data in a more readable form. Accounting fields also
depend on the site's configured job-accounting plugin.

## 6. Explicit Memory Requests

Request host RAM explicitly. Do not rely on site defaults, especially after scheduler changes, accounting changes, or cluster refreshes.

```bash
#SBATCH --mem=32G
```

Slurm defines `--mem=<size>` as real memory required per node. Suffixes such as `M`, `G`, and `T` are supported by Slurm, and `--mem`, `--mem-per-cpu`, and `--mem-per-gpu` are mutually exclusive request styles. Pick one style and keep it visible in every batch script.

For Python and ML jobs:

- Start with a conservative explicit memory request.
- Run a small validation job before scaling.
- Review `MaxRSS` or site job statistics after the job completes.
- Tune memory down or up from measured usage.

A job that ends with plain `Killed` and no Python traceback is often consistent with out-of-memory termination or memory enforcement. Check requested memory and job accounting before rebuilding Python environments or chasing nonfatal library warnings.

Reference: Slurm [`sbatch`](https://slurm.schedmd.com/sbatch.html) and [`sacct`](https://slurm.schedmd.com/sacct.html) documentation.

## 7. Cancel a Job

```bash
JOB_ID="REPLACE_WITH_JOB_ID"
scancel "$JOB_ID"
```

## 8. Useful Cluster Inspection Commands

```bash
PARTITION="REPLACE_WITH_PARTITION"
GPU_PARTITION="REPLACE_WITH_GPU_PARTITION"
sinfo -s
scontrol show config | egrep -i "DefMem|MaxMem"
scontrol show partition "$PARTITION"
sinfo -N -p "$GPU_PARTITION" -o "%N %c %m %G"
```

## 9. Log Files and Working Directory

In sbatch scripts, these are common patterns:

- `cd "$SLURM_SUBMIT_DIR"` to run from the submission folder
- `#SBATCH --output=slurm-%x-%j.out`
- `#SBATCH --error=slurm-%x-%j.err`
