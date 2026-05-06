# UTC MocsHPC Site Notes

This page contains public, site-specific UTC MocsHPC notes. The generic guide remains cluster-agnostic. Verify current limits, partitions, modules, and policies using official UTC docs and live cluster commands.

Official public references:

- [First time login instructions](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=163777)
- [Slurm partitions](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=163830)
- [Node types and stats](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=163829)
- [CUDA and NVIDIA](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=163891)
- [Jobstats](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=171575)

## Access

SSH login:

```bash
ssh <your_utc_id>@login.mocshpc.utc.edu
```

Open OnDemand:

- Public docs list `ondemand.mocshpc.utc.edu`.
- The dashboard URL is `https://ondemand.mocshpc.utc.edu/pun/sys/dashboard/`.
- VPN may be required when connecting from off campus.

## March 2026 Refresh Field Note

Field note from the March 2026 refresh and debugging session:

- The login address and Open OnDemand URL changed.
- Scheduler behavior changed.
- Memory is now tracked and should be explicitly requested.
- If memory is omitted, jobs may receive a low default, reported in the maintenance note as 4 GB per node.
- Jobs that exceed requested memory may be terminated.
- Conda, venv, and custom software stacks may need recreation after the rebuild, but allocation and resource issues should be ruled out first.
- Storage transitioned to GPFS, so old hardcoded paths may need review.
- Run small validation jobs before scaling up.

The 4 GB default is a field note from the maintenance/debugging report, not a value found in the public TeamDynamix pages above. For an authoritative current default, check with UTC support or inspect live Slurm configuration:

```bash
scontrol show config | egrep -i "DefMem|MaxMem"
scontrol show partition epyc-gpu
```

## Important Partitions for TensorFlow GPU Jobs

| Partition | Public UTC notes |
| --- | --- |
| `epyc-gpu` | Nodes `epyc[00-15]`; max 5 days; max 8 CPUs per node; max 2 GPUs; min 1 GPU; a job without a GPU request will not start. |
| `epyc-cpu` | Nodes `epyc[00-28]`; CPU-only; max GPUs 0; a job requesting a GPU will not start. |
| `epyc-full` | Nodes `epyc[00-15]`; max 5 days; max 128 CPUs per node; max 2 GPUs; requires explicit account access. |

For ordinary single-process TensorFlow or PyTorch jobs, start with `epyc-gpu`, one GPU, one task, and enough explicit host memory for the workload.

## Hardware Notes

- `epyc[00-15]` nodes have 512 GB RAM and two NVIDIA A100 80 GB GPUs per node.
- `epyc[16-28]` are CPU-only EPYC nodes with 512 GB RAM.

## Recommended Interactive GPU Probe

```bash
srun \
  --partition=epyc-gpu \
  --nodes=1 \
  --ntasks=1 \
  --cpus-per-task=4 \
  --gpus-per-node=1 \
  --mem=64G \
  --time=0-01:00:00 \
  --pty /bin/bash -l
```

Inside the allocation:

```bash
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unset}"
echo "SLURM_JOB_PARTITION=${SLURM_JOB_PARTITION:-unset}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L
nvidia-smi
```

Do not use `--ntasks=4` for a single Python/TensorFlow script just to give it more CPU. Use `--ntasks=1 --cpus-per-task=4` unless you are using MPI or a true distributed launcher.

## TensorFlow Batch Pattern

Use the generic [TensorFlow GPU probe example](../../examples/slurm_tensorflow_gpu_probe.sbatch) after replacing placeholders. For the UTC TensorFlow debug pattern that succeeded, use this resource shape:

```bash
#SBATCH --partition=epyc-gpu
#SBATCH --account=<account>
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=64G
#SBATCH --time=0-01:00:00
```

Then make the job print allocation and framework diagnostics before running the workload:

```bash
module purge
module load cuda/11.8

# shellcheck source=/dev/null
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate <env-name-or-path>

nvidia-smi -L
nvidia-smi
python - <<'PY'
import tensorflow as tf
print("tensorflow", tf.__version__)
print("physical GPUs", tf.config.list_physical_devices("GPU"))
PY

/usr/bin/time -v python <your-script>.py
```

UTC's CUDA page currently lists CUDA 11.8 and 12.2 availability on `epyc`, and shows `module load cuda/12.2` for NVCC. For an older TensorFlow environment that logs a missing `libcudart.so.11.0`, trying `cuda/11.8` is reasonable before rebuilding. In the field result that motivated this note, the environment did not need to be rebuilt once the job requested `--mem=64G`.

## Jobstats

UTC documents `jobstats <jobid>` for command-line resource review and also exposes Jobstats through Open OnDemand. Use it to inspect CPU usage, memory usage, runtime, node information, GPU usage, and storage performance.

```bash
jobstats <jobid>
```

For plain `Killed` failures, compare requested memory against observed memory first, then check CUDA/TensorFlow environment details.
