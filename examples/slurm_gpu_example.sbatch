#!/bin/bash -l
# Minimal GPU batch job template.
# Replace placeholders before use.

#SBATCH --job-name=gpu_example
#SBATCH --partition=<gpu-partition>
#SBATCH --account=<account>
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=16G
#SBATCH --time=0-01:00:00
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate /scratch/$USER/envs/py312-gpu

# Confirm GPU visibility inside the allocation.
nvidia-smi -L

# Replace with your training/inference command.
python - <<'PY'
print("GPU example submitted")
PY
