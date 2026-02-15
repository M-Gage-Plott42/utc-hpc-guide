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
