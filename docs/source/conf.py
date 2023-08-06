# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../../src/'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = '4chan_scraper'
copyright = '2023, Jack H. Culbert, Po-Chun Chang'
author = 'Jack H. Culbert, Po-Chun Chang'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
# todo helps list todos, viewcode allows you to view code snippet, autodoc allows auto doc pulling from your modules (must)
extensions = ['sphinx.ext.todo', 'sphinx.ext.viewcode', 'sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# sphinx_rtd_theme is the most popular template

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
