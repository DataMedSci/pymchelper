"""
DEPRECATED: This setup.py is kept for backwards compatibility only.

The project has been migrated to pyproject.toml for modern Python packaging.
Please use:
    pip install .
    pip install -e .[full]  # for development with all extras

All configuration is now in pyproject.toml with setuptools-scm for dynamic versioning.

This file now only serves as a fallback and will be removed in a future version.
Use pyproject.toml for all configuration.
"""

# This minimal setup.py allows setuptools to use pyproject.toml
# The actual build is handled by setuptools.build_meta via pyproject.toml

from setuptools import setup

# All configuration is in pyproject.toml
# This setup() call with no arguments allows setuptools to read pyproject.toml
setup()
