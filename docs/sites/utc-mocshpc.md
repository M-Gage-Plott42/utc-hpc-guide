# UTC MocsHPC Site Notes

This page contains public, site-specific UTC MocsHPC notes. The generic guide remains cluster-agnostic. Verify current limits, partitions, modules, and policies using official UTC docs and live cluster commands.

Official public references:

- [First time login instructions](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/Article/163777/Research-Institute-First-Time-Login-Instructions)
- [Slurm partitions](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/Article/163830/HPC-Cluster-Slurm-Partitions)
- [Node types and stats](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/Article/163829/HPC-Cluster-Node-Types-and-Stats)
- [CUDA and NVIDIA](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/Article/163891/CUDA-and-NVIDIA)
- [Jobstats](https://utc.teamdynamix.com/TDClient/2717/Portal/KB/Article/171575/Job-resource-utilization-monitoring-Jobstats)

Validation status, July 30, 2026: the public UTC pages above were rechecked,
and a VPN-enabled, read-only session confirmed authenticated SSH, scheduler
visibility, and Open OnDemand routing. A private human browser check completed
authentication and confirmed the final dashboard origin and
`/pun/sys/dashboard` path; no session data was retained. No job, allocation,
workload, account, or user record was queried or created. One public/live
conflict remains unresolved: the public partition page says `epyc-cpu` has a
120-CPU-per-node maximum, while both live `scontrol` and `sinfo` reported 128.
Treat 120 as the current published value, not a live-confirmed limit, and
obtain UTC technical confirmation before release promotion.

## Access

SSH login:

```bash
UTC_USER="REPLACE_WITH_UTC_ID"
ssh "${UTC_USER}@login.mocshpc.utc.edu"
```

Open OnDemand:

- UTC's public login documentation lists the
  [Open OnDemand entry URL](https://ondemand.mocshpc.utc.edu/).
- A July 30, 2026 VPN-path check confirmed that the public root first redirects
  to `/pun/sys/dashboard` and then to the authentication endpoint with valid
  TLS. A private human browser check then completed authentication and
  confirmed the dashboard remained on the public host at
  `/pun/sys/dashboard`; no query, fragment, cookie, or session detail was
  recorded.
- UTC's public login documentation directs off-campus users to connect to the
  UTC VPN before using SSH or Open OnDemand.

## July 30, 2026 Read-only Live Field Notes

These are sanitized operational observations, not public UTC policy:

- The intended SSH alias authenticated successfully to a login host, and the
  scheduler reported Slurm 26.05.0.
- The global scheduler configuration reported `DefMemPerNode=4096` MiB and
  `MaxMemPerNode=UNLIMITED`. The selected partition records did not report a
  more specific finite default. Slurm documents that an unset partition
  default inherits the cluster-wide `DefMemPerNode`; this corroborates the
  4 GiB default while remaining a field note rather than a published UTC
  guarantee. Continue requesting memory explicitly.
- `epyc-gpu` was up with a five-day limit, an eight-CPU-per-node job cap, and
  two A100 80 GB GPUs represented in its live generic-resource record.
- `epyc-full` was up with a five-day limit, a 128-CPU-per-node job cap, and
  two A100 80 GB GPUs represented in its live generic-resource record.
  Its detailed `scontrol` record was not available to the validating identity,
  so access restrictions and minimum-GPU behavior were not live-tested.
- `epyc-cpu` was up with a five-day limit, but its live 128-CPU-per-node job
  cap conflicts with the public page's 120-CPU value.

See the upstream
[Slurm partition memory-default documentation](https://slurm.schedmd.com/slurm.conf.html#OPT_DefMemPerNode)
for the inheritance rule. Because this validation deliberately submitted no
job, it did not test GPU-request rejection, account-gated submission, actual
scheduling, memory enforcement, CUDA modules, or Jobstats. Those claims remain
public-document facts or explicitly historical field notes.

## Historical March 2026 Refresh Field Note

The following observations came from a March 2026 refresh and debugging
session. They remain historical field notes, not current public policy, except
where the July 30 read-only observations above independently corroborate them:

- The login address and Open OnDemand URL changed.
- Scheduler behavior changed.
- Memory is now tracked and should be explicitly requested.
- If memory is omitted, jobs may receive a low default, reported in the maintenance note as 4 GB per node.
- Jobs that exceed requested memory may be terminated.
- Conda, venv, and custom software stacks may need recreation after the rebuild, but allocation and resource issues should be ruled out first.
- Storage transitioned to GPFS, so old hardcoded paths may need review.
- Run small validation jobs before scaling up.

The 4 GB default is not published in the TeamDynamix pages above. The July 30
read-only check found the same 4096 MiB cluster-wide value, but UTC support
remains the authority for policy and enforcement. Inspect live Slurm
configuration when behavior matters:

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

The table reports the public UTC page. It does not resolve the current
`epyc-cpu` discrepancy: the July 30 live partition views both advertised 128
CPUs per node. Confirm the effective job cap with UTC before relying on either
number.

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
