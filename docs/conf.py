# Configuration file for Sphinx documentation builder.

# -- Setup function ----------------------------------------------------------

# Defines custom steps in the process.

def autodoc_skip_member(app, what, name, obj, skip, options):
    """Exclude all private attributes, methods, and dunder methods from Sphinx."""
    import re
    exclude = re.findall(r'\._.*', str(obj))
    return skip or exclude

def remove_module_docstring(app, what, name, obj, options, lines):
    """Remove everything after 'Author: '."""
    if what == "module":
        keep = [i for i, line in enumerate(lines) if line.startswith("Author: ")]
        if keep:
            del lines[keep[0]:]
    return

def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip_member)
    app.connect("autodoc-process-docstring", remove_module_docstring)
    return


# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------
project = 'gio'
copyright = '2022, Agile Scientific'
author = 'Agile Scientific'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.githubpages',
    'sphinxcontrib.apidoc',
    'sphinx.ext.napoleon',
    'myst_nb',
    'sphinx.ext.coverage', 
]
 
myst_enable_extensions = ["dollarmath", "amsmath"]

# Apidoc automation
# https://pypi.org/project/sphinxcontrib-apidoc/
# The apidoc extension and this code automatically update apidoc.
apidoc_module_dir = '../gio'
apidoc_output_dir = './'
apidoc_excluded_paths = []
apidoc_toc_file = False
apidoc_separate_modules = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'notebooks']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# https://sphinx-themes.org/sample-sites/furo/
html_theme = 'furo'

html_theme_options = {
    "sidebar_hide_name": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'custom.css',
]

# Branding.
html_favicon = '_static/favicon.ico'
html_logo = '_static/gio_logo.png'
