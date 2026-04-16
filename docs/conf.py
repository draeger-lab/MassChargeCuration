# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "MassChargeCuration"
copyright = "2026, Finn Mier and Reihaneh Mostolizadeh"
author = "Finn Mier and Reihaneh Mostolizadeh"
release = "1.0.1"

# -- Path setup --------------------------------------------------------------

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(str(Path(".."))))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "nbsphinx",
    "myst_parser",
    "IPython.sphinxext.ipython_console_highlighting",
    "sphinxcontrib.bibtex",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

# For copy buttons in code blocks
copybutton_selector = "div.copyable pre"

# For citations
bibtex_bibfiles = ["library.bib"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Changes code highlighting
pygments_style = "blinds-light"

# Make figures numbered
numfig = True

# Explicitly assign the master document
master_doc = "index"

# Support both reStructuredText and Markdown sources.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}


# -- Autodoc -----------------------------------------------------------------

autodoc_preserve_defaults = True
autodoc_mock_imports = [
    "numpy",
    "libsbml",
    "matplotlib",
    "pandas",
    "requests",
    "tqdm",
    "z3",
    "z3-solver",
    "dill",
    "cobra",
]
