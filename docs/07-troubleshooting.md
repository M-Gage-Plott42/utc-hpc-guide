# 07 Troubleshooting

Common HPC onboarding issues and quick fixes.

## 1. `execve(): bash: No such file or directory` in `srun`

Use an explicit shell path:

```bash
srun ... --pty /bin/bash -l
```

## 2. `Invalid generic resource (gres) specification`

Likely cause: requesting GPUs in a non-GPU allocation or unsupported GPU request shape.

Fixes:

- Submit from a GPU partition
- Verify partition policy with `scontrol show partition <gpu-partition>`
- Reduce requested GPU count

## 3. pip Build Failures for Scientific Packages

Likely cause: no compatible wheel for your platform; pip attempts source build.

Fixes:

- Prefer conda for compiled packages
- Pin to wheel-available versions
- Load a newer compiler module only if you must build from source

## 4. `module spider` Not Available

Some module setups only support:

```bash
module avail
module show <module-name>
```

## 5. `nproc` Shows Fewer CPUs Than Expected

Inside SLURM job steps, `nproc` reflects CPUs assigned to your job step, not total node CPUs.

## 6. SSH Connection Problems

Check in this order:

1. VPN/network path to cluster
2. Username and login host
3. Account permissions/activation
4. SSH key permissions and known_hosts entries

## 7. Escalation Checklist for Support Tickets

Include:

- Exact command used
- Full error text
- Job ID (if scheduler-related)
- Timestamp and timezone
- Partition and resource request summary
