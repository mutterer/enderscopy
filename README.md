## Enderscopy

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
### Next version
Check the refactored next version in the dev branch.
