# 05 Python Environments

Use isolated environments for reproducible jobs. Avoid installing into shared/base Python.

Choose an environment root from your site's storage and software policy. When
an environment must survive scratch purges, prefer persistent project/software
storage that is available on compute nodes and suitable for package-file I/O.
Use scratch only when the site permits environments there and its retention,
quota, metadata, and performance policies fit your workflow.

Scratch environments must be treated as rebuildable. Keep an
`environment.yml`, pinned requirements or lock file, and any installation
notes in version control or another genuinely durable location. Do not assume
that a persistent filesystem is backed up; verify the site's backup policy.

## 1. Inspect Current Python

```bash
which python
python --version
python -c "import sys; print(sys.executable)"
```

## 2. Option A (Recommended): Conda at a Site-Approved Environment Root

```bash
ENV_ROOT="REPLACE_WITH_SITE_APPROVED_ENV_ROOT"
ENV="${ENV_ROOT}/conda/py312"
conda create -p "$ENV" python=3.12 -y
conda activate "$ENV"
python -m pip install --upgrade pip
python -m pip install numpy pandas matplotlib
```

Batch script activation snippet:

```bash
ENV_ROOT="REPLACE_WITH_SITE_APPROVED_ENV_ROOT"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${ENV_ROOT}/conda/py312"
```

## 3. Option B: Install Miniconda/Miniforge in User Space

Use this when `conda` is not available on your cluster by default. Install it
under the same site-approved environment root; that root may be a persistent
project/software tier or policy-compatible scratch.

```bash
ENV_ROOT="REPLACE_WITH_SITE_APPROVED_ENV_ROOT"
INSTALLER_DIR="${ENV_ROOT}/installers"
INSTALL_ROOT="${ENV_ROOT}/miniconda3"
INSTALLER="Miniconda3-py312_26.5.3-1-Linux-x86_64.sh"
INSTALLER_URL="https://repo.anaconda.com/miniconda/${INSTALLER}"
INSTALLER_SHA256="ecb43ee4ae30a7a5af87737e9548ceb21f0a10ec55b8dc40d247aa925b80bfec"

mkdir -p "$INSTALLER_DIR"
cd "$INSTALLER_DIR"
curl --fail --location --output "$INSTALLER" "$INSTALLER_URL"
printf '%s  %s\n' "$INSTALLER_SHA256" "$INSTALLER" | sha256sum --check -
bash "$INSTALLER" -b -p "$INSTALL_ROOT"
"$INSTALL_ROOT/bin/conda" init bash
```

This example pins the official Linux x86-64 Python 3.12 installer rather than
using the moving `latest` alias. Confirm your node architecture first, obtain
the matching filename and SHA-256 from the official
[Miniconda installer index](https://repo.anaconda.com/miniconda/), and never
run an installer after a hash mismatch. Anaconda's installation guidance
recommends SHA-256 verification.

## 4. Option C: venv + pip

Good for lightweight pure-Python projects.

```bash
ENV_ROOT="REPLACE_WITH_SITE_APPROVED_ENV_ROOT"
module avail python
module load python/REPLACE_WITH_VERSION
python -m venv "${ENV_ROOT}/venvs/py310"
source "${ENV_ROOT}/venvs/py310/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 5. If pip Tries to Compile and Fails

On older system libraries, prefer conda for compiled packages.

```bash
python -m pip download --only-binary=:all: --no-deps "numpy==2.2.6" -d /tmp/wheels_test
python -m pip install --only-binary=:all: "numpy==2.2.6"
```

If the wheel is unavailable for your platform, either pin differently or switch to conda.

## 6. Useful Module Checks

```bash
module avail gcc
module avail cuda
module avail openmpi
```

## 7. After Cluster Maintenance or Software Refresh

Cluster rebuilds, OS updates, and module-stack changes can break binary packages that were compiled or installed against older libraries. Recreate an environment when imports fail, shared libraries are missing, or framework GPU probes fail after the refresh.

Do not make environment rebuilds the first response to a job that only prints plain `Killed`. Check Slurm memory, GPU allocation, and job accounting first:

```bash
JOB_ID="REPLACE_WITH_JOB_ID"
sacct -j "$JOB_ID" --format=JobID,ReqMem,AllocTRES,State,ExitCode,MaxRSS
```

Snapshot before rebuilding. Review the output, then save the appropriate
manifest or lock file with the project in version-controlled or otherwise
durable storage:

```bash
python --version
python -m pip freeze
conda env export --no-builds 2>/dev/null || true
python - <<'PY'
try:
    import tensorflow as tf
    print("tensorflow", tf.__version__)
    print(tf.config.list_physical_devices("GPU"))
except Exception as exc:
    print(type(exc).__name__, exc)
PY
```

For a generic current Linux environment, TensorFlow's official install docs
recommend `pip`, install GPU support with
`python -m pip install 'tensorflow[and-cuda]'`, and verify GPU visibility with
`tf.config.list_physical_devices("GPU")`.

Avoid blindly installing or upgrading TensorFlow inside an old managed-HPC
environment. Check the site CUDA-module policy, NVIDIA driver, Python version,
and TensorFlow compatibility first. A site module can be appropriate for an
existing environment built against that module, while the current generic pip
extra supplies its own supported CUDA user-space dependencies. Do not combine
the two approaches without verifying compatibility.

Reference: TensorFlow [pip install](https://www.tensorflow.org/install/pip) documentation.
