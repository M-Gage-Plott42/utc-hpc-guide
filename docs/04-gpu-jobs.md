# 04 GPU Jobs

GPU jobs require both a GPU-capable partition and explicit GPU requests.

## 1. Interactive GPU Probe

```bash
srun \
  --partition=<gpu-partition> \
  --account=<account> \
  --nodes=1 \
  --ntasks=1 \
  --cpus-per-task=4 \
  --gpus-per-node=1 \
  --mem=16G \
  --time=0-00:20:00 \
  --pty /bin/bash -l
```

Inside the allocation:

```bash
hostname
nvidia-smi -L
```

## 2. GPU Batch Submission

Use `examples/slurm_gpu_example.sbatch` as a baseline:

```bash
sbatch examples/slurm_gpu_example.sbatch
```

## 3. Common Failure Mode: Invalid GRES

Error patterns like `Invalid generic resource (gres) specification` usually mean:

- You requested GPUs in a non-GPU allocation
- Partition/account policy does not permit the requested GPU type/count
- Requested resources exceed per-job limits

## 4. GPU Request Hygiene

- Start with one GPU and scale only when needed.
- Match `--cpus-per-task` to your data pipeline requirements.
- Confirm partition policies with `scontrol show partition <gpu-partition>`.
- Validate placement with `nvidia-smi` at job start.

## 5. Reproducibility Notes

- Pin framework versions (PyTorch/CUDA or TensorFlow stack).
- Save the exact sbatch script used for each training run.
- Persist key metadata: commit SHA, seed, CLI args, and environment export.
