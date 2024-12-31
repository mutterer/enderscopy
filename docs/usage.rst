Usage
=====

Enderscope provides a Python API and a GUI for controlling a 3D printer chassis-based microscope.

**Basic Usage:**

1. Import the package and create instances of the required classes:

   .. code-block:: python

      from enderscope import Stage, EnderLights

      stage = Stage(port='/dev/ttyUSB0', baud_rate=115200)
      stage.home()

2. Use the `gui` function to launch a control panel:

   .. code-block:: python

      from enderscope import gui
      stage, lights, panel = gui()

**Demo Notebooks:**

The package includes Jupyter notebooks for learning and demonstration purposes. See the `demos` folder for examples.
