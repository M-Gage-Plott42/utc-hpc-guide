# 06 Data Transfer and Storage

Use storage tiers intentionally to avoid quota and performance issues.

## 1. Typical Storage Roles

- Home: small code repositories, configs, environment manifests, and shell/SSH setup
- Scratch: large active datasets, temporary outputs, and logs
- Group/project space: shared data and, when policy allows, persistent software/environments
- Public/shared space: data intended for broad access

Default placement policy:

- Keep Home as a control plane (code, configs, lightweight metadata).
- Put environments that must survive in site-approved persistent
  project/software storage designed for compute access and package-file I/O.
- Use Scratch for environments only when site retention, quota, metadata, and
  performance policies support that choice; assume a scratch environment may
  need to be rebuilt.
- Keep reconstruction manifests and lock files in version control or another
  durable location.
- Keep large active datasets and job outputs in Scratch or project/group
  storage as site policy directs.

Use your institution's exact paths, backup behavior, and retention policies.
Persistent does not necessarily mean backed up.

## 2. Check Capacity and Quota

```bash
HOME_PATH="REPLACE_WITH_HOME_PATH"
SCRATCH_PATH="REPLACE_WITH_SCRATCH_PATH"
PROJECT_PATH="REPLACE_WITH_PROJECT_PATH"
df -h "$HOME_PATH"
df -h "$SCRATCH_PATH" 2>/dev/null || true
df -h "$PROJECT_PATH" 2>/dev/null || true
quota -s 2>/dev/null || true
```

If quota commands fail, use your support channel for authoritative limits.

## 3. Transfer Methods

- `rsync` for large or incremental transfers
- `scp` for quick one-off copies
- `git` for code and lightweight text artifacts
- OOD upload/download for small files

## 4. rsync Example

```bash
HPC_USER="REPLACE_WITH_USERNAME"
LOGIN_HOST="REPLACE_WITH_LOGIN_HOST"
SCRATCH_PATH="REPLACE_WITH_SCRATCH_PATH"

# local -> cluster
rsync -avhP ./data/ \
  "${HPC_USER}@${LOGIN_HOST}:${SCRATCH_PATH}/project/data/"

# cluster -> local
rsync -avhP \
  "${HPC_USER}@${LOGIN_HOST}:${SCRATCH_PATH}/project/results/" ./results/
```

## 5. Data Hygiene Checklist

- Keep raw, intermediate, and final artifacts separated
- Compress/archive old runs
- Avoid writing large outputs to Home by default
- Stage active working sets to Scratch/project storage before large runs
- Document where canonical outputs live
- Size transfer and compute workflows from a short benchmark run, then scale deliberately
