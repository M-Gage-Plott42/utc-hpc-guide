# 03 SLURM Basics

SLURM allocates compute resources for interactive and batch workloads.

## 1. Two Primary Modes

- `sbatch`: submit a script for non-interactive execution
- `srun --pty`: start an interactive shell on allocated resources

## 2. Quick Interactive CPU Session

```bash
srun \
  --partition=<cpu-partition> \
  --account=<account> \
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
squeue -u "$USER"
sacct -j <jobid> --format=JobID,JobName,Partition,AllocCPUS,Elapsed,State,ExitCode,NodeList,MaxRSS
```

## 6. Cancel a Job

```bash
scancel <jobid>
```

## 7. Useful Cluster Inspection Commands

```bash
sinfo -s
scontrol show partition <partition-name>
sinfo -N -p <gpu-partition> -o "%N %c %m %G"
```

## 8. Log Files and Working Directory

In sbatch scripts, these are common patterns:

- `cd "$SLURM_SUBMIT_DIR"` to run from the submission folder
- `#SBATCH --output=slurm-%x-%j.out`
- `#SBATCH --error=slurm-%x-%j.err`
