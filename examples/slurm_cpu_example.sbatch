#!/bin/bash -l
# Minimal CPU batch job template.
# Replace placeholders before use.

#SBATCH --job-name=cpu_example
#SBATCH --partition=<cpu-partition>
#SBATCH --account=<account>
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=0-01:00:00
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err

set -euo pipefail

# Run from the directory where sbatch was called.
cd "$SLURM_SUBMIT_DIR"

# Activate your Python environment.
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate /scratch/$USER/envs/py312

# Replace with your workload.
python - <<'PY'
import platform
print("CPU example running")
print(platform.platform())
PY
