# UTC MocsHPC Site Notes

This page contains public, site-specific UTC MocsHPC notes. The generic guide remains cluster-agnostic. Verify current limits, partitions, modules, and policies using official UTC docs and live cluster commands.

Official public references:

- [First time login instructions](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=163777)
- [Slurm partitions](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=163830)
- [Node types and stats](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=163829)
- [CUDA and NVIDIA](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=163891)
- [Jobstats](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/ArticleDet?ID=171575)

Validation status, July 2026: the public UTC pages above were rechecked for
this update. Live scheduler commands, authenticated login, and browser routing
have not yet been revalidated; those checks remain pending a VPN-enabled
session.

## Access

SSH login:

```bash
UTC_USER="REPLACE_WITH_UTC_ID"
ssh "${UTC_USER}@login.mocshpc.utc.edu"
```

Open OnDemand:

- UTC's public login documentation lists the
  [Open OnDemand entry URL](https://ondemand.mocshpc.utc.edu/).
- A March 2026 field note recorded `/pun/sys/dashboard/` as the authenticated
  dashboard path under that public host. Treat that path as historical until
  its current redirect behavior is confirmed in a VPN-enabled browser.
- UTC's public login documentation directs off-campus users to connect to the
  UTC VPN before using SSH or Open OnDemand.

## Historical March 2026 Refresh Field Note

The following observations came from a March 2026 refresh and debugging
session. They are historical field notes, not current public policy, and live
revalidation remains pending:

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

## Selected Partitions for TensorFlow GPU Onboarding

This table is a selected EPYC onboarding subset, not a complete partition
inventory. UTC's public partition page lists additional EPYC and non-EPYC
families. Recheck that page and live `sinfo` output before submitting work.

| Partition | Public UTC notes |
| --- | --- |
| `epyc-gpu` | Nodes `epyc[00-15]`; max 5 days; max 8 CPUs per node; max 2 GPUs; min 1 GPU; a job without a GPU request will not start. |
| `epyc-cpu` | Nodes `epyc[00-28]`; CPU-only; max 5 days; max 120 CPUs per node; max GPUs 0; a job requesting a GPU will not start. |
| `epyc-full` | Nodes `epyc[00-15]`; max 5 days; max 128 CPUs per node; max 2 GPUs; min 1 GPU; requires explicit account access; a job without a GPU request will not start. |

For an ordinary single-process TensorFlow or PyTorch probe, `epyc-gpu`, one
GPU, and one task are a useful starting shape. Request host memory explicitly,
then tune it from a representative run and Jobstats rather than treating the
example below as a minimum.

## Hardware Notes

- `epyc[00-15]` nodes have 512 GB RAM and two NVIDIA A100 80 GB GPUs per node.
- `epyc[16-28]` are CPU-only EPYC nodes with 512 GB RAM.

## Interactive GPU Probe

The following 64 GB request is a March 2026 field-note diagnostic starting
point, not a documented TensorFlow minimum or a recommendation for every
workload. Run a representative probe, review Jobstats, and adjust the next
request from measured usage.

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

Use the generic [TensorFlow GPU probe example](../../examples/slurm_tensorflow_gpu_probe.sbatch)
after replacing placeholders. The UTC debug pattern reported in the March
2026 field note used this resource shape:

```bash
#SBATCH --partition=epyc-gpu
#SBATCH --account=REPLACE_WITH_ACCOUNT
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=64G
#SBATCH --time=0-01:00:00
```

Treat 64 GB as a diagnostic starting point from that observation, not a
documented minimum. After a representative run, use Jobstats to tune memory
down or up.

Then make the job print allocation and framework diagnostics before running the workload:

```bash
module purge
module load cuda/11.8

ENV_PATH="REPLACE_WITH_CONDA_ENV_PATH"
SCRIPT_PATH="REPLACE_WITH_PYTHON_SCRIPT"

# shellcheck source=/dev/null
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_PATH"

nvidia-smi -L
nvidia-smi
python - <<'PY'
import tensorflow as tf
print("tensorflow", tf.__version__)
print("physical GPUs", tf.config.list_physical_devices("GPU"))
PY

/usr/bin/time -v python "$SCRIPT_PATH"
```

UTC's CUDA page currently lists CUDA 11.8 and 12.2 availability on `epyc`, and
shows `module load cuda/12.2` for NVCC. For an older TensorFlow environment
that logs a missing `libcudart.so.11.0`, trying `cuda/11.8` is reasonable
before rebuilding. In the single field result that motivated this note, the
environment did not need to be rebuilt once the job requested `--mem=64G`;
that observation does not establish a general memory minimum.

## Jobstats

UTC documents `jobstats <jobid>` for command-line resource review and also exposes Jobstats through Open OnDemand. Use it to inspect CPU usage, memory usage, runtime, node information, GPU usage, and storage performance.

```bash
JOB_ID="REPLACE_WITH_JOB_ID"
jobstats "$JOB_ID"
```

For plain `Killed` failures, compare requested memory against observed memory first, then check CUDA/TensorFlow environment details.
