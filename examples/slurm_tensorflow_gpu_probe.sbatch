#!/bin/bash -l
# TensorFlow GPU diagnostic job.
# Replace placeholders before use. This is not a production training script.

#SBATCH --job-name=tf_gpu_probe
#SBATCH --partition=<gpu-partition>
#SBATCH --account=<account>
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=32G
#SBATCH --time=0-00:20:00
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"

echo "hostname=$(hostname)"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unset}"
echo "SLURM_JOB_PARTITION=${SLURM_JOB_PARTITION:-unset}"
echo "SLURM_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK:-unset}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"

nvidia-smi -L
nvidia-smi

# Activate the environment that contains TensorFlow.
# shellcheck source=/dev/null
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "<env-name-or-path>"

export TF_FORCE_GPU_ALLOW_GROWTH=true

python - <<'PY'
import os
import tensorflow as tf

print("tensorflow", tf.__version__)
print("CUDA_VISIBLE_DEVICES", os.environ.get("CUDA_VISIBLE_DEVICES", "unset"))

try:
    print("build_info", tf.sysconfig.get_build_info())
except Exception as exc:
    print("build_info_unavailable", type(exc).__name__, exc)

physical_gpus = tf.config.list_physical_devices("GPU")
print("physical GPUs", physical_gpus)

for gpu in physical_gpus:
    try:
        tf.config.experimental.set_memory_growth(gpu, True)
    except Exception as exc:
        print("memory_growth_warning", gpu, type(exc).__name__, exc)

logical_gpus = tf.config.list_logical_devices("GPU")
print("logical GPUs", logical_gpus)

if not physical_gpus:
    raise SystemExit("No TensorFlow GPU devices detected")

with tf.device("/GPU:0"):
    a = tf.random.uniform((256, 256))
    b = tf.linalg.matmul(a, a)
    print("matmul_sum", float(tf.reduce_sum(b).numpy()))
PY
