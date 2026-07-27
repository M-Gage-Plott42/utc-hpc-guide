# 07 Troubleshooting

Common HPC onboarding issues and quick fixes.

## 1. `Killed` With No Python Traceback During ML Jobs

A plain `Killed` line, especially after nonfatal CUDA or TensorFlow warnings, often points to memory enforcement or allocation issues before it points to Python package corruption.

Check in this order:

- Step 1: confirm the job requested host RAM explicitly with `--mem`, `--mem-per-cpu`, or `--mem-per-gpu`.
- Step 2: confirm allocation metadata:

```bash
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unset}"
echo "SLURM_JOB_PARTITION=${SLURM_JOB_PARTITION:-unset}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L
```

- Step 3: confirm framework GPU visibility:

```bash
python - <<'PY'
import tensorflow as tf
print(tf.config.list_physical_devices("GPU"))
PY
```

- Step 4: check job accounting:

```bash
JOB_ID="REPLACE_WITH_JOB_ID"
sacct -j "$JOB_ID" --format=JobID,ReqMem,AllocTRES,State,ExitCode,MaxRSS
```

- Step 5: if your site provides `jobstats`, `seff`, or similar tools, use them to review memory and GPU usage.
- Step 6: only after allocation and memory checks, inspect CUDA/TensorFlow library mismatch.
- Step 7: recreate the Python environment only if GPU probes fail, imports fail, or packages are inconsistent.

## 2. TensorRT Warnings During TensorFlow Import

Warnings about missing TensorRT libraries are usually nonfatal unless the workload explicitly uses TF-TRT or TensorRT inference acceleration.

Prioritize:

- `nvidia-smi -L`
- TensorFlow `tf.config.list_physical_devices("GPU")`
- Slurm memory and accounting checks

## 3. `execve(): bash: No such file or directory` in `srun`

Use an explicit shell path:

```bash
srun ... --pty /bin/bash -l
```

## 4. `Invalid generic resource (gres) specification`

Likely cause: requesting GPUs in a non-GPU allocation or unsupported GPU request shape.

Fixes:

- Submit from a GPU partition
- Verify partition policy with `scontrol show partition "$GPU_PARTITION"`
- Reduce requested GPU count

## 5. pip Build Failures for Scientific Packages

Likely cause: no compatible wheel for your platform; pip attempts source build.

Fixes:

- Prefer conda for compiled packages
- Pin to wheel-available versions
- Load a newer compiler module only if you must build from source

## 6. `module spider` Not Available

Some module setups only support:

```bash
module avail
module show REPLACE_WITH_MODULE_NAME
```

## 7. `nproc` Shows Fewer CPUs Than Expected

Inside SLURM job steps, `nproc` reflects CPUs assigned to your job step, not total node CPUs.

## 8. SSH Connection Problems

Check in this order:

1. VPN/network path to cluster
2. Username and login host
3. Account permissions/activation
4. SSH key permissions and known_hosts entries

## 9. Escalation Checklist for Support Tickets

Include:

- Exact command used
- Full error text
- Job ID (if scheduler-related)
- Timestamp and timezone
- Partition and resource request summary
