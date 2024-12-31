Enderscope
==========

Enderscope is a **lightweight** Python software designed to transform a 3D printer chassis and a Raspberry Pi into a simple and **cost-effective microscope for scanning well plates**. The project is targeted at both laboratory applications and **educational demonstrations**, such as science fairs. Its simplicity makes it **ideal for beginners** to understand and extend.

Features
--------

- **Cheap** (based on minimalist hardware requirements such as a Raspberry Pi and a 3D printer chassis)
- **Easy-to-read Python code**, designed for simplicity and educational use.
- Controlled through **Jupyter notebooks**, with a minimal graphical interface using ipywidgets.
- Uses GCode to control 3D printer movement.
- Supports the Raspberry Pi camera, with plans to include support for additional cameras in the future.

Installation
------------

To install Enderscope on a Raspberry Pi 4 running Debian Bookworm OS (Released 2024-07-04):

1. Update your system and install required dependencies:

   .. code-block:: bash

      sudo apt update && sudo apt upgrade -y
      sudo apt install python3 python3-venv python3-pip git

2. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/mutterer/enderscopy.git
      cd enderscope

3. Create a virtual environment and activate it:

   .. code-block:: bash

      python3 -m venv enderscope_env
      source enderscope_env/bin/activate

4. Install the required Python packages:

   .. code-block:: bash

      pip install -r requirements.txt

.. note::

   Whenever possible, a pip version will be available, which will only require:

   .. code-block:: bash

      pip install enderscope

Usage
-----

To use Enderscope:

1. Activate the virtual environment:

   .. code-block:: bash

      source ~/enderscope/enderscope_env/bin/activate

2. Launch Jupyter Notebook:

   .. code-block:: bash

      jupyter notebook

3. Open the ``demo`` notebook in JupyterLab to get started.

Development
-----------

Enderscope is designed to be simple and modular, making it easy for contributors to add new features or improve existing ones. The project structure adheres to Python best practices, with the following key files:

- ``requirements.txt``: Lists the dependencies required for the project.
- ``pyproject.toml``: Contains project metadata and configuration for packaging.
- ``MANIFEST.in``: Specifies additional files to include in the package.

To contribute:

1. Fork the repository and create a new branch for your feature or bugfix.
2. Write clean, readable code and include comments where necessary.
3. Submit a pull request with a clear description of your changes.

Planned Features
----------------

- Support for additional camera modules (USB webcam, potentially Basler camera if compatible).
- Integration with more advanced image analysis tools.
- Improved documentation and tutorials for educational use.

License
-------

Enderscope is open-source software licensed under the MIT License. See the ``LICENSE`` file for more details.

Acknowledgments
---------------

Special thanks to the open-source community for tools and inspiration, and to educators and researchers for their feedback in shaping this project.

