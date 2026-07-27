# 01 Access and SSH

This section covers account prerequisites, network access, and SSH setup.

## 1. Account and Network Prerequisites

- Active HPC account with scheduler permissions
- Correct username format for your site
- VPN access if required off-campus/off-network

If access fails, verify permissions first before debugging SSH syntax.

## 2. Basic SSH Login

```bash
HPC_USER="REPLACE_WITH_USERNAME"
LOGIN_HOST="REPLACE_WITH_LOGIN_HOST"
ssh "${HPC_USER}@${LOGIN_HOST}"
```

You should land on a login/head node. Avoid running heavy compute on login nodes.

## 3. SSH Keys (Recommended)

Generate a local key and install the public key on the cluster account.

```bash
# local machine
HPC_USER="REPLACE_WITH_USERNAME"
LOGIN_HOST="REPLACE_WITH_LOGIN_HOST"
ssh-keygen -t ed25519 -C "${HPC_USER}@hpc"

# if supported at your site
ssh-copy-id "${HPC_USER}@${LOGIN_HOST}"
```

## 4. Optional SSH Config Alias

Add a host alias to `~/.ssh/config` on your local machine:

```sshconfig
Host hpc
    HostName REPLACE_WITH_LOGIN_HOST
    User REPLACE_WITH_USERNAME
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 120
```

Then connect with:

```bash
ssh hpc
```

## 5. Optional IDE Remote Workflow

VS Code and Cursor-style workflows typically use SSH remote extensions:

1. Install the SSH remote extension in your editor.
2. Connect to `<username>@<login-host>`.
3. Open your project folder on cluster storage.
4. Use the integrated terminal for `srun`, `sbatch`, and debugging.

## 6. Connection Sanity Checks

```bash
whoami
hostname
pwd
```

If login fails, check:

- VPN connectivity
- Correct username/host values
- Account activation status
- SSH key permissions (`chmod 600 ~/.ssh/id_ed25519`)
