# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))  # 指向源代码目录
project = 'myFund'
copyright = '2025, Hui Qiao'
author = 'Hui Qiao'
release = 'v0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',   # 自动生成 API 文档
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',  # 支持 Google 风格注释
    'myst_parser',          # 支持 Markdown
]
# 在文档中引用代码模块
autodoc_mock_imports = ["optional_dependencies"]
templates_path = ['_templates']
exclude_patterns = []

language = 'zh_CN'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
