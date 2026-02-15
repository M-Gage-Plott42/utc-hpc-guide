# 06 Data Transfer and Storage

Use storage tiers intentionally to avoid quota and performance issues.

## 1. Typical Storage Roles

- Home: small code repositories, configs, and shell/SSH setup
- Scratch: large datasets, temporary outputs, environments, and logs
- Group/project space: shared collaboration data
- Public/shared space: data intended for broad access

Use your institution's exact paths and retention policies.

## 2. Check Capacity and Quota

```bash
df -h "$HOME"
df -h /scratch/$USER 2>/dev/null || true
df -h /groups 2>/dev/null || true
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
# local -> cluster
rsync -avhP ./data/ <username>@<login-host>:/scratch/<username>/project/data/

# cluster -> local
rsync -avhP <username>@<login-host>:/scratch/<username>/project/results/ ./results/
```

## 5. Data Hygiene Checklist

- Keep raw, intermediate, and final artifacts separated
- Compress/archive old runs
- Avoid writing large outputs to Home by default
- Document where canonical outputs live
