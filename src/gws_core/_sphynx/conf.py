# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import sphinx_rtd_theme

# -- Initialize GWS -----------------------------------------------------

__cdir__ = os.path.dirname(os.path.abspath(__file__))
wd = os.path.join(__cdir__,'../../')
sys.path.insert(0, os.path.join(wd,'../gws'))
from gws import runner
from gws.manage import load_settings
load_settings(wd)
ctx = None
runner._run(ctx)

#
extensions = [
    'sphinx_rtd_theme',
    'rinoh.frontend.sphinx'
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    'settings.py',
    'manage.py',
    '**/gws/runner.py',
    '**/gws/_sphynx/conf.py'
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = 'sphinx_rtd_theme'