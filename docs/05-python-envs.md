# 05 Python Environments

Use isolated environments for reproducible jobs. Avoid installing into shared/base Python.

## 1. Inspect Current Python

```bash
which python
python --version
python -c "import sys; print(sys.executable)"
```

## 2. Option A (Recommended): Conda Environment in Scratch

```bash
ENV=/scratch/$USER/envs/py312
conda create -p "$ENV" python=3.12 -y
conda activate "$ENV"
python -m pip install --upgrade pip
python -m pip install numpy pandas matplotlib
```

Batch script activation snippet:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate /scratch/$USER/envs/py312
```

## 3. Option B: Install Miniconda/Miniforge in User Space

Use this when `conda` is not available on your cluster by default.

```bash
cd /scratch/$USER
mkdir -p installers && cd installers
curl -L -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p /scratch/$USER/miniconda3
/scratch/$USER/miniconda3/bin/conda init bash
```

## 4. Option C: venv + pip

Good for lightweight pure-Python projects.

```bash
module avail python
module load python/<version>
python -m venv /scratch/$USER/venvs/py310
source /scratch/$USER/venvs/py310/bin/activate
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
sacct -j <jobid> --format=JobID,ReqMem,AllocTRES,State,ExitCode,MaxRSS
```

Snapshot before rebuilding:

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

For TensorFlow, the official install docs recommend `pip` because TensorFlow is officially released to PyPI, and they recommend verifying GPU visibility with `tf.config.list_physical_devices("GPU")`.

Avoid blindly running `pip install --upgrade tensorflow` inside an old managed-HPC environment. Check the site CUDA module, NVIDIA driver, Python version, and TensorFlow compatibility first.

Reference: TensorFlow [pip install](https://www.tensorflow.org/install/pip) documentation.
