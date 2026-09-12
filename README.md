## Enderscopy

Enderscopy is a **lightweight** Python library that turns a 3D-printer chassis and a Raspberry Pi into a simple and **cost-effective microscope for scanning well plates**. It targets both laboratory applications and **educational demonstrations**, such as science fairs. Its simplicity makes it **ideal for beginners** to understand and extend.

### Features

- **Cheap**, based on minimalist hardware requirements: a Raspberry Pi and a 3D printer chassis.
- **Easy-to-read Python code**, designed for simplicity and educational use.
- Controlled through **Jupyter notebooks**, with a minimal graphical interface using ipywidgets.
- Uses GCode to control 3D printer movement.
- Supports the Raspberry Pi camera, with plans to include support for additional cameras in the future.

### Installation

For a Raspberry Pi 4 with Debian Bookworm OS (Released 2024-07-04):

Create an 'enderscope' virtual environment to work in:

```
cd ~
python3 -m venv --system-site-packages enderscope
source enderscope/bin/activate
python -m pip install git+https://github.com/mutterer/enderscopy.git ipykernel
python -m ipykernel install --user --name enderscope --display-name "Python (enderscope)"
jupyter notebook
```

Clone this repo and open a notebook from the `example_notebooks` folder in JupyterLab.
Select **Kernel → Change Kernel → Python (enderscope)** so the notebook uses the environment where the library is installed.

To upgrade the library later, run:

```
python -m pip install --upgrade git+https://github.com/mutterer/enderscopy.git
```


### Usage

```
cd ~
source enderscope/bin/activate
jupyter notebook
```

### Troubleshooting: notebook cannot import `enderscope`

If a notebook reports `ModuleNotFoundError: No module named 'enderscope'` after installation, it may be using a different Python environment. This can happen when Jupyter comes from an existing Miniforge or Conda installation, even after activating the `enderscope` environment in a terminal.

Check the notebook's Python by running this in a cell:

```python
import sys
print(sys.executable)
```

For the installation above, the path should be `/home/YOUR_USERNAME/enderscope/bin/python`. If it points elsewhere, register the environment as a Jupyter kernel by running this in a terminal:

```bash
~/enderscope/bin/python -m ipykernel install --user --name enderscope --display-name "Python (enderscope)"
```

If this command reports that `ipykernel` is missing, install it with `~/enderscope/bin/python -m pip install ipykernel`, then repeat the registration command. See the [IPython kernel installation documentation](https://ipython.readthedocs.io/en/stable/install/kernel_install.html) for details.

Save the notebook, refresh the browser page, and select **Kernel → Change Kernel → Python (enderscope)**. If the kernel is still missing from the menu, restart Jupyter and reopen the notebook. Run `jupyter kernelspec list` in the terminal used to launch Jupyter to check that `enderscope` is listed.

Verify the import in a notebook cell:

```python
import enderscope
print(enderscope.__file__)
```

The result should be a path ending in `enderscope/__init__.py`. A result of `None` can mean Python found a directory named `enderscope` rather than the installed library; check the selected kernel and `sys.executable` as above.

### Contributing

Enderscope is designed to be simple and modular, making it easy to add new features or improve existing ones.

1. Fork the repository and create a new branch for your feature or bugfix.
2. Write clean, readable code and include comments where necessary.
3. Submit a pull request with a clear description of your changes.

### Planned features

- Support for additional camera modules (USB webcam).
- Integration with more advanced image analysis tools.
- Improved documentation and tutorials for educational use.

### License

Enderscope is open-source software licensed under the [MIT License](LICENSE).

### Acknowledgments

Special thanks to the open-source community for tools and inspiration, and to educators and researchers for their feedback in shaping this project.
