## Enderscopy

Enderscopy is a **lightweight** Python library that turns a 3D-printer chassis and a Raspberry Pi into a simple and **cost-effective microscope for scanning well plates**. It targets both laboratory applications and **educational demonstrations**, such as science fairs. Its simplicity makes it **ideal for beginners** to understand and extend.

### Features

- **Cheap**, based on minimalist hardware requirements: a Raspberry Pi and a 3D printer chassis.
- **Easy-to-read Python code**, designed for simplicity and educational use.
- Controlled through **Jupyter notebooks**, with a minimal graphical interface using ipywidgets.
- Uses GCode to control 3D printer movement.
- Supports the Raspberry Pi camera, with plans to include support for additional cameras in the future.

### Installation on Rapsberry Pi

For a Raspberry Pi 4 with Debian Bookworm OS (Released 2024-07-04), or later:

Create an 'enderscope' virtual environment to work in:

```
cd ~
python3 -m venv --system-site-packages enderscope
source enderscope/bin/activate
pip install git+https://github.com/mutterer/enderscopy.git
jupyter lab
```

Clone this repo and open the 'demo' notebook in JupyterLab.

To upgrade the library later, run:

```
pip install --upgrade git+https://github.com/mutterer/enderscopy.git
```


### Installation on Windows / macOS / Ubuntu (no Raspberry Pi camera)

Use a dedicated Miniforge environment for stage control and the virtual-stage notebooks.

1. Download and install [Miniforge3 for your operating system and processor](https://github.com/conda-forge/miniforge#install). On macOS, choose the installer for Apple Silicon or Intel as appropriate.
2. On Windows, open **Miniforge Prompt** from the Start menu. On macOS or Ubuntu, enable shell initialization when the installer asks, then open a new terminal. If `conda` is unavailable after installing to the default location, run `~/miniforge3/bin/conda init` and reopen the terminal.
3. Create and activate an environment, then install Enderscope and its notebook tools:

```bash
conda create -n enderscope python=3.12 pip git -y
conda activate enderscope
python -m pip install git+https://github.com/mutterer/enderscopy.git
python -m ipykernel install --user --name enderscope --display-name "Python (enderscope)"
```

Git is included in the environment for installing the library and downloading the example notebooks. Run the following from the directory where you want to keep your copy of the repository:

```bash
git clone https://github.com/mutterer/enderscopy.git
cd enderscopy
python -m jupyterlab
```

If you already have a copy of the repository, change into that directory and run `python -m jupyterlab`.

In JupyterLab, open a notebook from `example_notebooks` and select **Kernel → Change Kernel → Python (enderscope)**. Start with `02a_demo_virtual_stage.ipynb` to try stage control without hardware. Raspberry Pi camera notebooks require the Raspberry Pi setup above.

For later sessions, open Miniforge Prompt (Windows) or a terminal (macOS/Ubuntu), activate the environment, change into your repository directory, and start JupyterLab:

```bash
conda activate enderscope
cd path/to/enderscopy
python -m jupyterlab
```

Replace `path/to/enderscopy` with your repository path; quote it if it contains spaces. To upgrade the library, run this with the environment active:

```bash
python -m pip install --upgrade git+https://github.com/mutterer/enderscopy.git
```

Launch JupyterLab from this environment so the server and notebook kernel share the installed widget support. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for import errors, missing kernels, or Matplotlib widget errors.

### Usage on Raspberry Pi

```
cd ~
source enderscope/bin/activate
python -m jupyterlab
```
