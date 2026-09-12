# Troubleshooting

## Notebook cannot import `enderscope`

If a notebook reports `ModuleNotFoundError: No module named 'enderscope'` after installation, it may be using a different Python environment. This can happen when Jupyter comes from an existing Miniforge or Conda installation, even after activating the `enderscope` environment in a terminal.

Check the notebook's Python by running this in a cell:

```python
import sys
print(sys.executable)
```

For the installation described in the [README](README.md#installation), the path should be `/home/YOUR_USERNAME/enderscope/bin/python`. If it points elsewhere, register the environment as a Jupyter kernel by running this in a terminal:

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

## Matplotlib does not recognize the `widget` backend

The virtual-stage notebooks use `%matplotlib widget` for interactive plots. If this reports `'widget' is not a recognised GUI loop or backend name`, install the missing `ipympl` backend in the Enderscope environment:

```bash
~/enderscope/bin/python -m pip install ipympl
```

Save your notebooks and restart Jupyter using `~/enderscope/bin/python -m jupyterlab`, then select **Python (enderscope)** and rerun the notebook. Launching Jupyter from this environment also makes the installed plot widget's frontend available. New installations include `ipympl` automatically. See the [ipympl installation documentation](https://matplotlib.org/ipympl/installing.html).

## Browser cannot load `MPLCanvasModel` from `jupyter-matplotlib`

This error means the browser cannot load the Matplotlib widget frontend. It can happen when `ipympl` is installed in the notebook kernel's environment but is missing from the environment running the Jupyter server, or when the frontend and backend versions do not match.

Save your notebooks, stop the Jupyter server in its terminal with Ctrl+C and confirm shutdown if prompted, then launch it from the Enderscope environment:

```bash
~/enderscope/bin/python -m jupyterlab
```

Open the address printed by this command, select **Python (enderscope)**, and refresh the browser with Ctrl+Shift+R. Restart the notebook kernel and rerun the plotting cells to create new widgets.

If you want to keep running the Jupyter server from another environment, install a matching version of `ipympl` there too. Check the kernel environment's version:

```bash
~/enderscope/bin/python -c 'import ipympl; print(ipympl.__version__)'
```

For example, if this prints `0.10.0` and Jupyter runs from `~/miniforge3`, run:

```bash
~/miniforge3/bin/python -m pip install ipympl==0.10.0
```

Use the version reported by your kernel environment and the Python path of your Jupyter server. Restart the server, refresh the browser, and restart the notebook kernel after installation. See the [ipympl frontend/backend compatibility guidance](https://matplotlib.org/ipympl/installing.html#mixing-frontend-and-backend-versions).
