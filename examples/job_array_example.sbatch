#!/bin/bash -l
# Minimal SLURM job array template.
# Replace placeholders before use.

#SBATCH --job-name=array_example
#SBATCH --partition=<cpu-partition>
#SBATCH --account=<account>
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=0-00:20:00
#SBATCH --array=0-9
#SBATCH --output=slurm-%x-%A_%a.out
#SBATCH --error=slurm-%x-%A_%a.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"

# Use the array index to shard work.
TASK_ID="${SLURM_ARRAY_TASK_ID}"
echo "Running array task ${TASK_ID}"

# Replace with task-specific command.
python - <<'PY'
import os
task = os.environ.get("SLURM_ARRAY_TASK_ID", "unknown")
print(f"Hello from array task {task}")
PY
