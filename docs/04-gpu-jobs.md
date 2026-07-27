# 04 GPU Jobs

GPU jobs require both a GPU-capable partition and explicit GPU requests.

## 1. Interactive GPU Probe

```bash
GPU_PARTITION="REPLACE_WITH_GPU_PARTITION"
ACCOUNT="REPLACE_WITH_ACCOUNT"
srun \
  --partition="$GPU_PARTITION" \
  --account="$ACCOUNT" \
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
echo "$SLURM_JOB_ID"
echo "$SLURM_JOB_PARTITION"
echo "$CUDA_VISIBLE_DEVICES"
nvidia-smi -L
```

`--mem=16G` is a smoke-test value. Deep-learning training may need `32G`, `64G`, or more host RAM depending on the data pipeline, model, and preprocessing workload.

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
- Use `--ntasks=1` with `--cpus-per-task=N` for a normal single-process Python script.
- Use multiple tasks only for MPI, distributed launchers, or explicitly multi-process training.
- Match `--cpus-per-task` to your data pipeline requirements; it is the normal way to give one Python process more CPU.
- Confirm partition policies with `scontrol show partition "$GPU_PARTITION"`.
- Validate placement with `nvidia-smi` at job start.
- Request host memory explicitly with `--mem=<size>` and review measured usage after the job completes.

## 5. Allocation, Framework Visibility, and Memory

Debug GPU jobs in layers:

1. Confirm Slurm allocated a GPU.
2. Confirm the driver can see it.
3. Confirm the framework can see it.
4. Confirm host RAM was requested explicitly and was not exhausted.

Print allocation metadata at job start:

```bash
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unset}"
echo "SLURM_JOB_PARTITION=${SLURM_JOB_PARTITION:-unset}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L
nvidia-smi
```

`nvidia-smi` proves driver-level GPU visibility inside the allocation. TensorFlow or PyTorch can still fail to see a GPU if the environment, CUDA runtime libraries, or framework build are mismatched.

TensorFlow GPU probe:

```bash
python - <<'PY'
import tensorflow as tf
print(tf.__version__)
print(tf.config.list_physical_devices("GPU"))
PY
```

TensorFlow's install docs use `tf.config.list_physical_devices("GPU")` as the GPU verification check.

For a generic current Linux environment, TensorFlow documents
`python -m pip install 'tensorflow[and-cuda]'`. On a managed cluster, do not
assume that packaged CUDA libraries and a site-provided CUDA module should be
combined. First confirm the NVIDIA driver, the cluster's module policy, and the
framework version; then use one compatible environment strategy and verify it
inside an allocated GPU job.

TensorRT warnings during TensorFlow import are often not fatal unless the workload uses TensorRT acceleration. TensorFlow documents TensorRT as optional software for improving inference latency and throughput, so check framework GPU visibility and job memory before chasing TensorRT warnings.

`nvidia-smi` may report a newer CUDA driver capability than the toolkit module loaded for the job. NVIDIA documents backward compatibility where a newer NVIDIA driver can run applications built with an older CUDA Toolkit.

References: TensorFlow [pip install](https://www.tensorflow.org/install/pip) and NVIDIA [CUDA compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/why-cuda-compatibility.html) documentation.

## 6. Reproducibility Notes

- Pin framework versions (PyTorch/CUDA or TensorFlow stack).
- Save the exact sbatch script used for each training run.
- Persist key metadata: commit SHA, seed, CLI args, and environment export.
