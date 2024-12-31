import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Enderscope'
author = 'J\u00e9r\u00f4me Mutterer and Contributors'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon'
]
autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []

html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']
