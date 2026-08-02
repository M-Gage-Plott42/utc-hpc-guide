# 03 Slurm Basics

Slurm allocates compute resources for interactive and batch workloads.

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
printf 'SLURM_CPUS_PER_TASK=%s\n' "${SLURM_CPUS_PER_TASK:-unset}"
printf 'SLURM_CPUS_ON_NODE=%s\n' "${SLURM_CPUS_ON_NODE:-unset}"
scontrol show job "$SLURM_JOB_ID"
```

Treat these as complementary checks, not interchangeable proof. GNU `nproc`
reports processors available to the current process. Depending on the
installed Coreutils version and process environment, CPU affinity/cpusets,
cgroup v2 CPU quotas, `OMP_NUM_THREADS`, or `OMP_THREAD_LIMIT` can affect that
number. Slurm variables describe scheduler scopes:

- `SLURM_CPUS_PER_TASK` is set when CPUs per task were explicitly requested.
- `SLURM_CPUS_ON_NODE` describes CPUs available to the step on the current
  node, with details depending on the site's Slurm selection plugin.
- `scontrol show job "$SLURM_JOB_ID"` reports the job allocation, while a job
  step's binding can still constrain an individual process.

Compare the values with the request and site configuration; no single value is
a universal allocation test.

References: GNU Coreutils [`nproc`](https://www.gnu.org/software/coreutils/manual/html_node/nproc-invocation.html)
and Slurm [`srun`](https://slurm.schedmd.com/srun.html) and
[`sbatch`](https://slurm.schedmd.com/sbatch.html) documentation.

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
SACCT_FIELDS="JobID,JobName,Partition,ReqMem,AllocTRES,AllocCPUS"
SACCT_FIELDS="${SACCT_FIELDS},Elapsed,State,ExitCode,MaxRSS"
sacct -j "$JOB_ID" --format="$SACCT_FIELDS"
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
