#!/bin/bash -l
# Minimal CPU batch job template.
# Replace every REPLACE_WITH_* value before use.

#SBATCH --job-name=cpu_example
#SBATCH --partition=REPLACE_WITH_CPU_PARTITION
#SBATCH --account=REPLACE_WITH_ACCOUNT
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
ENV_PATH="REPLACE_WITH_CONDA_ENV_PATH"
if [[ "$ENV_PATH" == REPLACE_WITH_* ]]; then
    echo "Set ENV_PATH to a real Conda environment path before submitting." >&2
    exit 2
fi
# shellcheck source=/dev/null
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_PATH"

# Replace with your workload.
python - <<'PY'
import platform
print("CPU example running")
print(platform.platform())
PY
