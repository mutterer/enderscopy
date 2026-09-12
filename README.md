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
pip install git+https://github.com/mutterer/enderscopy.git
jupyter notebook
```

Clone this repo and open a notebook from the `example_notebooks` folder in JupyterLab.

To upgrade the library later, run:

```
pip install --upgrade git+https://github.com/mutterer/enderscopy.git
```


### Usage

```
cd ~
source enderscope/bin/activate
jupyter notebook
```

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

